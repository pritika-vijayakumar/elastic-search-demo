import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class Variant(BaseModel):
    model_config = ConfigDict(extra="forbid")
    size_system: str = "US"
    size: str
    stock: int = Field(ge=0)


class Attributes(BaseModel):
    model_config = ConfigDict(extra="forbid")
    waterproof: bool | None


class Product(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: str = Field(min_length=1)
    name: str
    brand: str
    category: str
    description: str = Field(min_length=1)
    product_guide: str = ""
    price: float = Field(ge=0)
    currency: str = "USD"
    variants: list[Variant] = Field(min_length=1)
    attributes: Attributes


def load_catalog(path: Path) -> list[Product]:
    products = [
        Product.model_validate(json.loads(line))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    ids = [p.product_id for p in products]
    if len(set(ids)) != len(ids):
        raise ValueError("Catalog contains duplicate product IDs.")
    for p in products:
        sizes = [(v.size_system, v.size) for v in p.variants]
        if len(sizes) != len(set(sizes)):
            raise ValueError(f"Duplicate variant size for {p.product_id}")
    if not products:
        raise ValueError("Catalog is empty.")
    return products


def index_document(product: Product) -> dict:
    document = product.model_dump()
    document["searchable_content"] = "\n\n".join(
        text for text in [product.name, product.description, product.product_guide] if text
    )
    return document
