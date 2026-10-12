"""
search.py turns the customer’s question and filters into an 
Elasticsearch request, executes it, and prepares the retrieved 
evidence for the next step
"""

from dataclasses import asdict, dataclass
from math import isfinite
from time import perf_counter

#This class stores the customer’s requirements
@dataclass(frozen=True)
class Constraints:
    max_price: float | None = 100
    currency: str = "USD"
    size: str | None = "9"
    size_system: str = "US"
    in_stock: bool = True

    def __post_init__(self):
        if self.max_price is not None and (self.max_price < 0 or not isfinite(self.max_price)):
            raise ValueError("Budget must be nonnegative and finite.")

#converts requirements into Elasticsearch filterss. 
#This function builds a list of conditions that products must satisfy.
def filters_for(constraints: Constraints) -> list[dict]:
    filters = [{"term": {"currency": constraints.currency}}]
    if constraints.max_price is not None:
        filters.append({"range": {"price": {"lte": constraints.max_price}}})
    variants = []
    if constraints.size:
        variants.extend(
            [
                {"term": {"variants.size": constraints.size}},
                {"term": {"variants.size_system": constraints.size_system}},
            ]
        )
    if constraints.in_stock:
        variants.append({"range": {"variants.stock": {"gt": 0}}})
    if variants:
        filters.append({"nested": {"path": "variants", "query": {"bool": {"filter": variants}}}})
    return filters

#builds the search request, then creates filters and keyword and semantic
def build_request(question: str, mode: str, constraints: Constraints, limit: int = 5) -> dict:
    if not question.strip():
        raise ValueError("Enter a search question.") #rejects An empty question.
    if mode not in {"keyword", "semantic", "hybrid"}: #rejects An unsupported search mode.
        raise ValueError("Unknown search mode.")
    if not 1 <= limit <= 20: #A result limit outside 1–20.
        raise ValueError("Result count must be between 1 and 20.")
    filters = filters_for(constraints)
    keyword = {"multi_match": {"query": question, "fields": ["name^4", "brand^2", "description"]}}
    semantic = {"match": {"searchable_content": question}} #this performs meaning-based

    def branch(query):
        return {"standard": {"query": {"bool": {"must": [query], "filter": filters}}}}

    retriever = (
        {
            "rrf": {
                "retrievers": [branch(keyword), branch(semantic)],
                "rank_window_size": 50,
                "rank_constant": 60,
            }
        }
        if mode == "hybrid"
        else branch(keyword if mode == "keyword" else semantic)
    )
    request = {
        "size": limit,
        "retriever": retriever,
        "_source": [
            "product_id",
            "name",
            "brand",
            "category",
            "description",
            "price",
            "currency",
            "variants",
            "attributes",
        ],
    }
    if mode != "keyword":
        request["highlight"] = {
            "pre_tags": [""],
            "post_tags": [""],
            "fields": {
                "searchable_content": {
                    "type": "semantic",
                    "number_of_fragments": 2,
                    "order": "score",
                }
            },
        }
    return request

#defensively checks a returned product against the constraints
def eligible(product: dict, constraints: Constraints) -> bool:
    if product["currency"] != constraints.currency:
        return False
    if constraints.max_price is not None and product["price"] > constraints.max_price:
        return False
    return any(
        (
            not constraints.size
            or (v["size"] == constraints.size and v["size_system"] == constraints.size_system)
        )
        and (not constraints.in_stock or v["stock"] > 0)
        for v in product["variants"]
    )

#main function called by the application.
#executes retrieval and prepares results
def run_search(
    client, index: str, question: str, mode: str, constraints: Constraints, limit: int = 5
) -> dict:
    request = build_request(question, mode, constraints, limit)
    started = perf_counter()
    response = client.search(index=index, body=request)
    if response.get("timed_out") or response.get("_shards", {}).get("failed", 0):
        raise RuntimeError(
            "Elasticsearch returned incomplete results. Retry before generating an answer."
        )
    products = []
    for hit in response["hits"]["hits"]:
        product = dict(hit["_source"])
        if not eligible(product, constraints):
            raise RuntimeError("A returned product violates constraints. Check the index mapping.")
        product["score"] = hit["_score"]
        product["passages"] = hit.get("highlight", {}).get("searchable_content", [])
        products.append(product)
    return {
        "question": question,
        "mode": mode,
        "constraints": asdict(constraints),
        "products": products,
        "request": request,
        "es_took_ms": response.get("took"),
        "elapsed_ms": round((perf_counter() - started) * 1000, 1),
    }
