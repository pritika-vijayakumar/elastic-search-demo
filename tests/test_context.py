from dataclasses import asdict

from src.catalog import load_catalog
from src.config import ROOT
from src.context import build_context
from src.search import Constraints


def test_context_preserves_unknown_and_eligible_variants_without_vectors():
    product = load_catalog(ROOT / "data" / "products.jsonl")[1].model_dump()
    product.update(passages=["Wipe them with a damp cloth and mild soap."], score=0.5)
    context = build_context(
        {
            "question": "How to clean insoles?",
            "constraints": asdict(Constraints()),
            "products": [product],
        }
    )
    evidence = context["products"][0]
    assert evidence["attributes"]["waterproof"] is None
    assert all(v["size"] == "9" and v["stock"] > 0 for v in evidence["eligible_variants"])
    assert evidence["passages"] == product["passages"]
    assert "score" not in evidence
    assert "product_guide" not in evidence


def test_empty_evidence_is_preserved():
    assert (
        build_context({"question": "Shoes", "constraints": asdict(Constraints()), "products": []})[
            "products"
        ]
        == []
    )
