import pytest

from src.catalog import load_catalog
from src.config import ROOT
from src.search import Constraints, build_request, eligible, run_search


def test_size_stock_cannot_match_different_variants():
    plus = load_catalog(ROOT / "data" / "products.jsonl")[3].model_dump()
    assert not eligible(plus, Constraints(size="9"))
    assert eligible(plus, Constraints(size="10"))
    assert eligible(plus, Constraints(size="9", in_stock=False))
    assert not eligible(plus, Constraints(size="10", max_price=98))


def test_hybrid_both_branches_have_same_nested_constraints():
    request = build_request("Walking shoes", "hybrid", Constraints())
    branches = request["retriever"]["rrf"]["retrievers"]
    for branch in branches:
        filters = branch["standard"]["query"]["bool"]["filter"]
        assert {"range": {"price": {"lte": 100}}} in filters
        variant_filters = filters[-1]["nested"]["query"]["bool"]["filter"]
        assert {"term": {"variants.size": "9"}} in variant_filters
        assert {"range": {"variants.stock": {"gt": 0}}} in variant_filters


def test_incomplete_search_fails_before_answer():
    class Client:
        def search(self, **kwargs):
            return {"timed_out": True, "hits": {"hits": []}}

    with pytest.raises(RuntimeError, match="incomplete"):
        run_search(Client(), "demo", "walking", "semantic", Constraints())


def test_wrong_currency_rejected():
    product = load_catalog(ROOT / "data" / "products.jsonl")[0].model_dump()
    product["currency"] = "EUR"
    assert not eligible(product, Constraints())
