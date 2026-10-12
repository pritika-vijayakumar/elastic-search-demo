"""
answer.py sends the selected evidence to OpenAI, receives a structured
answer, and checks its product citations before returning it to the UI.
"""

import json
from time import perf_counter

from openai import OpenAI
from pydantic import BaseModel, ConfigDict

from src.config import ROOT, Settings

#defines one recommendation
class Recommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: str
    reason: str
    evidence_quote: str

#defines the complete answer
class ShoppingAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    explanation: str
    recommendations: list[Recommendation]
    missing_information: list[str]

#checks the recommendations against the evidence
"""
Used inside generate answer()
Source is from context that was retrieved from Elastic Seach. 
This function rejects an answer if it:
- Contains more than three recommendations.
- Cites a product that was not retrieved.
- Recommends the same product twice.
- Provides an empty quote or a quote absent from that product’s supplied passages.
- Recommends products when no evidence was retrieved.
"""
def validate_grounding(answer: ShoppingAnswer, context: dict) -> None:
    if len(answer.recommendations) > 3:
        raise ValueError("Answer returned more than three recommendations.")
    sources = {p["product_id"]: p for p in context["products"]}
    seen = set()
    for rec in answer.recommendations:
        if rec.product_id not in sources or rec.product_id in seen:
            raise ValueError("Answer contains an unknown or duplicate product citation.")
        seen.add(rec.product_id)
        if not rec.evidence_quote.strip() or not any(
            rec.evidence_quote in passage for passage in sources[rec.product_id]["passages"]
        ):
            raise ValueError("Answer evidence quote does not match its cited retrieved product.")
    if not sources and answer.recommendations:
        raise ValueError("Cannot recommend products when retrieval returned no evidence.")

#calls OpenAI and returns the checked answers
def generate_answer(settings: Settings, context: dict, client=None) -> dict:
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required for answer generation.")
    api = client or OpenAI(api_key=settings.openai_api_key, timeout=settings.timeout, max_retries=2)
    started = perf_counter()
    response = api.responses.parse(
        model=settings.openai_model,
        instructions=(ROOT / "prompts" / "answer.txt").read_text(encoding="utf-8"),
        input=[{"role": "user", "content": json.dumps(context, ensure_ascii=False)}],
        text_format=ShoppingAnswer,
        max_output_tokens=1600,
        store=False,
    )
    answer = response.output_parsed#gets the parsed ShoppingAnswer object.
    if response.status != "completed" or answer is None:
        raise RuntimeError(
            "OpenAI did not return a complete structured answer (refusal or token limit)."
        )
    validate_grounding(answer, context)#then validates the answer
    usage = response.usage
    return {
        "answer": answer.model_dump(),
        "model": response.model,
        "elapsed_ms": round((perf_counter() - started) * 1000, 1),
        "usage": usage.model_dump() if usage else None,
    }
