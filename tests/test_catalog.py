import json

import pytest

from src.catalog import index_document, load_catalog
from src.config import ROOT


def test_catalog_is_valid_with_real_demo_edge_cases():
    products = load_catalog(ROOT / "data" / "products.jsonl")
    assert len(products) == 60
    assert len({p.product_id for p in products}) == 60
    by_id = {p.product_id: p for p in products}
    assert by_id["shoe-003"].price > 100
    plus = by_id["shoe-004"]
    assert next(v.stock for v in plus.variants if v.size == "9") == 0
    assert next(v.stock for v in plus.variants if v.size == "10") > 0
    assert by_id["shoe-002"].attributes.waterproof is None
    assert len(by_id["shoe-002"].product_guide.split()) > 300
    assert "Cleaning" in index_document(by_id["shoe-002"])["searchable_content"]


def test_duplicate_product_ids_rejected(tmp_path):
    product = load_catalog(ROOT / "data" / "products.jsonl")[0].model_dump()
    path = tmp_path / "duplicate.jsonl"
    path.write_text((json.dumps(product) + "\n") * 2)
    with pytest.raises(ValueError, match="duplicate product"):
        load_catalog(path)
