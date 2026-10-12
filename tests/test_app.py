from dataclasses import asdict
from unittest.mock import MagicMock, patch

from streamlit.testing.v1 import AppTest

from src.catalog import load_catalog
from src.config import ROOT, Settings
from src.search import Constraints


def test_catalog_view_without_credentials():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=15).run()
    app.radio[0].set_value("Catalog").run()
    assert not app.exception
    assert "60 fictional" in app.subheader[0].value


def test_submission_generates_openai_answer_and_displays_evidence():
    product = load_catalog(ROOT / "data" / "products.jsonl")[0].model_dump()
    product.update(passages=[product["description"]], score=0.5)
    result = {
        "question": "Walking shoes",
        "mode": "semantic",
        "constraints": asdict(Constraints()),
        "products": [product],
        "request": {},
        "es_took_ms": 5,
        "elapsed_ms": 10,
    }
    generated = {
        "model": "test",
        "elapsed_ms": 20,
        "usage": {},
        "answer": {
            "explanation": "A retrieved listing describes cushioning.",
            "recommendations": [
                {
                    "product_id": "shoe-001",
                    "reason": "Cushioned soles.",
                    "evidence_quote": "cushioned soles",
                }
            ],
            "missing_information": [],
        },
    }
    settings = Settings("https://example.com", "fake", "demo", "jina", "fake", "test")
    with (
        patch("src.config.load_settings", return_value=settings),
        patch("src.elastic_client.create_client", return_value=MagicMock()),
        patch("src.search.run_search", return_value=result),
        patch("src.answer.generate_answer", return_value=generated) as generate,
    ):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=15).run()
        app.button(key="FormSubmitter:search-Search and generate answer").click().run()
        assert not app.exception
        assert not app.error
        generate.assert_called_once()
        assert any("WalkLite 200" in h.value for h in app.subheader)
        assert "generated" in app.session_state["demo_result"]


def test_empty_retrieval_still_calls_openai_and_generation_failure_retains_evidence():
    result = {
        "question": "Shoes",
        "mode": "semantic",
        "constraints": asdict(Constraints()),
        "products": [],
        "request": {},
        "es_took_ms": 5,
        "elapsed_ms": 10,
    }
    settings = Settings("https://example.com", "fake", "demo", "jina", "fake", "test")
    with (
        patch("src.config.load_settings", return_value=settings),
        patch("src.elastic_client.create_client", return_value=MagicMock()),
        patch("src.search.run_search", return_value=result),
        patch(
            "src.answer.generate_answer", side_effect=RuntimeError("provider failed")
        ) as generate,
    ):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=15).run()
        app.button(key="FormSubmitter:search-Search and generate answer").click().run()
        assert not app.exception
        assert app.error
        generate.assert_called_once()
        assert app.session_state["demo_result"]["context"]["products"] == []
        assert "generated" not in app.session_state["demo_result"]
