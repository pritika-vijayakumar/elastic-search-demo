from types import SimpleNamespace

import pytest

from src.answer import Recommendation, ShoppingAnswer, generate_answer, validate_grounding
from src.config import Settings

CONTEXT = {
    "question": "Walking shoes?",
    "products": [
        {"product_id": "shoe-001", "passages": ["Lightweight sneakers with cushioned soles."]}
    ],
}


def answer(product_id="shoe-001", quote="cushioned soles"):
    return ShoppingAnswer(
        explanation="A listing describes cushioning.",
        recommendations=[
            Recommendation(product_id=product_id, reason="For walking", evidence_quote=quote)
        ],
        missing_information=[],
    )


@pytest.mark.parametrize(
    "product_id,quote",
    [("invented-id", "cushioned soles"), ("shoe-001", "certified waterproof"), ("shoe-001", "")],
)
def test_invalid_citations_and_quotes_fail(product_id, quote):
    with pytest.raises(ValueError):
        validate_grounding(answer(product_id, quote), CONTEXT)


def test_exact_quote_accepted():
    validate_grounding(answer(), CONTEXT)


def test_openai_call_uses_structured_response_and_nonstored_evidence():
    class Responses:
        def parse(self, **kwargs):
            assert kwargs["store"] is False
            assert kwargs["text_format"] is ShoppingAnswer
            assert "shoe-001" in kwargs["input"][0]["content"]
            return SimpleNamespace(
                output_parsed=answer(), status="completed", model="test", usage=None
            )

    settings = Settings("https://example.com", "fake", "demo", "jina", "fake", "test")
    result = generate_answer(settings, CONTEXT, SimpleNamespace(responses=Responses()))
    assert result["answer"]["recommendations"][0]["product_id"] == "shoe-001"


def test_refusal_or_incomplete_answer_not_displayed():
    class Responses:
        def parse(self, **kwargs):
            return SimpleNamespace(output_parsed=None, status="incomplete")

    settings = Settings("https://example.com", "fake", "demo", "jina", "fake", "test")
    with pytest.raises(RuntimeError, match="complete structured"):
        generate_answer(settings, CONTEXT, SimpleNamespace(responses=Responses()))
