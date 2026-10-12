import json

import httpx
from openai import OpenAI

from src.answer import generate_answer
from src.config import Settings


def test_real_sdk_serializes_and_parses_structured_response_offline():
    def respond(request):
        payload = json.loads(request.content)
        assert request.url.path == "/v1/responses"
        assert payload["store"] is False
        assert payload["text"]["format"]["type"] == "json_schema"
        assert payload["text"]["format"]["strict"] is True
        text = json.dumps(
            {
                "explanation": "No products were retrieved.",
                "recommendations": [],
                "missing_information": [],
            }
        )
        return httpx.Response(
            200,
            json={
                "id": "resp_test",
                "object": "response",
                "created_at": 0,
                "status": "completed",
                "model": "gpt-4o-mini",
                "error": None,
                "incomplete_details": None,
                "output": [
                    {
                        "id": "msg_test",
                        "type": "message",
                        "status": "completed",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": text, "annotations": []}],
                    }
                ],
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": 10,
                    "total_tokens": 20,
                    "input_tokens_details": {"cached_tokens": 0},
                    "output_tokens_details": {"reasoning_tokens": 0},
                },
            },
        )

    settings = Settings("https://example.com", "fake", "demo", "jina", "fake", "gpt-4o-mini")
    with OpenAI(
        api_key="fake", http_client=httpx.Client(transport=httpx.MockTransport(respond))
    ) as api:
        result = generate_answer(settings, {"question": "Shoes under $1?", "products": []}, api)
    assert result["answer"]["recommendations"] == []
    assert result["usage"]["total_tokens"] == 20
