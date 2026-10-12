"""
catalog.py defines what a valid product looks like, reads and validates
the catalog, and prepares each product for Elasticsearch ingestion.
"""

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

#Define one available size-and-stock variant
class Variant(BaseModel):
    model_config = ConfigDict(extra="forbid") #Rejects fields that are not defined in this model.
    size_system: str = "US"
    size: str
    stock: int = Field(ge=0)

#Defines a separate model for product characteristics.
class Attributes(BaseModel):
    model_config = ConfigDict(extra="forbid") #Rejects undeclared attributes.
    waterproof: bool | None

#Define a complete product
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

#Read and validate the catalog: Expects a path pointing to catalog and It returns a list of validated Product objects.
def load_catalog(path: Path) -> list[Product]:
    products = [
        Product.model_validate(json.loads(line))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    """
    products = []

    contents = path.read_text(encoding="utf-8")

    for line in contents.splitlines():
        if line.strip():
            record = json.loads(line)
            product = Product.model_validate(record)
            products.append(product)
    """
    ids = [p.product_id for p in products] #Builds a list of product IDs.
    if len(set(ids)) != len(ids):
        raise ValueError("Catalog contains duplicate product IDs.")
    for p in products:
        sizes = [(v.size_system, v.size) for v in p.variants]
        if len(sizes) != len(set(sizes)):
            raise ValueError(f"Duplicate variant size for {p.product_id}")
    if not products:
        raise ValueError("Catalog is empty.")
    return products

#creates semantic_text as searchable_content for ingestion into Elasticsearch. It concatenates the product name, description, and product guide into a single string, separated by double newlines. This field is used for semantic search in Elasticsearch.
#Prepare a product for Elasticsearch-Defines a function that accepts a validated Product and returns a dictionary suitable for ingestion.
def index_document(product: Product) -> dict:
    document = product.model_dump() #Converts the Pydantic object into a Python dictionary.
    document["searchable_content"] = "\n\n".join(
        text for text in [product.name, product.description, product.product_guide] if text
    )#[product.name, product.description, product.product_guide]
    return document
"""
Result might look like this:

WalkLite 200

Lightweight sneakers with cushioned soles for everyday comfort.

WalkLite 200: Cleaning
Remove the removable insoles...
"""
