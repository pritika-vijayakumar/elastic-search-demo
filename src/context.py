"""
context.py prepares the evidence that OpenAI receives.
It takes the search results and keeps the product facts, relevant passages, and eligible sizes needed to answer the customer.
"""

def build_context(result: dict) -> dict:
    constraints = result["constraints"]
    evidence = []
    for product in result["products"]:
        variants = [
            v
            for v in product["variants"]
            if (
                not constraints["size"]
                or (
                    v["size"] == constraints["size"]
                    and v["size_system"] == constraints["size_system"]
                )
            )
            and (not constraints["in_stock"] or v["stock"] > 0)
        ]
        evidence.append(
            {
                "product_id": product["product_id"],
                "name": product["name"],
                "price": product["price"],
                "currency": product["currency"],
                "eligible_variants": variants,
                "attributes": product["attributes"],
                "passages": product["passages"] or [product["description"]],
            }
        )
    return {
        "question": result["question"],
        "constraints": constraints,
        "products": evidence,
        "inventory_note": "Availability reflects the indexed demo catalog, not a stock reservation.",
    }
