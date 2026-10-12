"""Deterministically rebuild the fictional demo data; never calls an external service."""

import json

from src.config import ROOT

SEEDS = [
    (
        "WalkLite 200",
        89,
        "walking",
        "Lightweight sneakers with cushioned soles for everyday comfort. "
        "A flexible sole and padded collar support long strolls on city sidewalks.",
        None,
    ),
    (
        "CityStride Comfort",
        95,
        "walking",
        "An airy mesh upper and soft foam midsole provide a "
        "gentle feel during extended urban sightseeing. Built for daily pavement use.",
        None,
    ),
    (
        "MetroCloud Premium",
        180,
        "walking",
        "Premium all-day city walking shoes with plush cushioning "
        "and a padded footbed for long New York sightseeing days.",
        False,
    ),
    (
        "WalkLite 200 Plus",
        99,
        "walking",
        "Comfortable walking sneakers with extra heel cushioning for all-day city exploration.",
        None,
    ),
    (
        "CourtEdge Formal",
        79,
        "formal",
        "Polished dress shoes with a structured upper and firm sole "
        "for office meetings and formal events.",
        False,
    ),
    (
        "RainRoute Walker",
        98,
        "walking",
        "Waterproof walking shoes with a cushioned footbed and "
        "sealed upper for damp city sidewalks.",
        True,
    ),
    (
        "StrideFlex Daily",
        72,
        "walking",
        "Supple everyday sneakers with a soft insole, low weight, "
        "and an easy bend through the forefoot for neighborhood walks.",
        False,
    ),
    (
        "PavementEase Knit",
        100,
        "walking",
        "Breathable knit sneakers with padded soles for extended "
        "city strolls and everyday comfort.",
        None,
    ),
    (
        "SprintEdge Track",
        110,
        "running",
        "Responsive running shoes for short fast track sessions, "
        "with a firm race-oriented platform.",
        False,
    ),
    (
        "SummitGrip Trail",
        135,
        "trail",
        "Rugged hiking footwear with aggressive lugs for rocky paths and a stiff protective upper.",
        True,
    ),
    (
        "StudioFlat Canvas",
        45,
        "casual",
        "Simple canvas slip-ons with thin flat soles for casual indoor wear and short errands.",
        False,
    ),
    (
        "HarborRest Sandal",
        55,
        "sandal",
        "Open sandals with adjustable straps and a molded footbed for warm-weather leisure.",
        None,
    ),
]


def guide(name: str, description: str) -> str:
    sections = [
        (
            "Intended use",
            description + " Choose footwear according to the intended activity. "
            "Try the fit before extended use; no shoe can guarantee comfort for every person.",
        ),
        (
            "Fit",
            "Check length and width while wearing the socks you intend to use. Leave room "
            "for the toes and confirm that the heel does not slip. This catalog uses US sizes.",
        ),
        (
            "City surfaces",
            "Pavement, subway stairs, and standing in queues can feel different. "
            "Start with a short outing to assess fit. Alternate footwear if rubbing develops.",
        ),
        (
            "Cleaning",
            "Remove the removable insoles after a long city walk. Wipe them with a "
            "damp cloth and mild soap, then air-dry away from direct heat. Do not machine-wash "
            "the insoles or put them in a tumble dryer. Brush loose dirt off the upper.",
        ),
        (
            "Drying and storage",
            "Allow the shoes to dry at room temperature in a ventilated "
            "space. Do not place them on a radiator. Store them away from prolonged direct sunlight.",
        ),
        (
            "Weather information",
            "Check the structured waterproof attribute. If it is unknown, "
            "this guide does not establish waterproofing. A mesh upper alone proves no weather rating.",
        ),
        (
            "Inventory",
            "Availability is tracked per size. Stock in one size does not establish "
            "availability in another. This fictional catalog has no live checkout or stock reservation.",
        ),
        (
            "Wear checks",
            "Inspect the outsole and upper periodically. Replace worn footwear "
            "based on its actual condition. No mileage lifetime or medical benefit is claimed.",
        ),
    ]
    # Long enough to exercise default chunking without hand-made passage boundaries.
    return "\n\n".join(
        f"{name}: {title}\n{text} "
        "These instructions apply to this demo listing. Consult a real manufacturer "
        "for product-specific guidance before buying actual footwear."
        for title, text in sections
    )


def make_products() -> list[dict]:
    products = []
    for batch in range(5):
        for i, (name, price, category, description, waterproof) in enumerate(SEEDS):
            number = batch * len(SEEDS) + i + 1
            full_name = name if batch == 0 else f"{name} Edition {batch + 1}"
            sizes = [
                {
                    "size_system": "US",
                    "size": str(size),
                    "stock": 0 if (number + size) % 7 == 0 else 2 + number % 9,
                }
                for size in range(7, 13)
            ]
            if i == 3:
                for v in sizes:
                    v["stock"] = 0 if v["size"] == "9" else 5
            if number in {1, 2, 6, 7, 8}:
                for v in sizes:
                    if v["size"] == "9":
                        v["stock"] = 8
            if batch == 4:
                for v in sizes:
                    v["stock"] = 0
            products.append(
                {
                    "product_id": f"shoe-{number:03d}",
                    "name": full_name,
                    "brand": "DemoFootwear",
                    "category": category,
                    "description": description,
                    "product_guide": guide(full_name, description) if number in {1, 2, 6} else "",
                    "price": price if batch == 0 else price + 12 * batch,
                    "currency": "USD",
                    "variants": sizes,
                    "attributes": {"waterproof": waterproof},
                }
            )
    return products


def make_cases(products: list[dict]) -> list[dict]:
    from src.search import Constraints, eligible

    specifications = [
        (
            "meaning",
            "Comfortable shoes for walking around New York all day",
            "semantic",
            100,
            "9",
            "walking",
        ),
        ("hybrid-city", "Comfortable city walking sneakers", "hybrid", 100, "9", "walking"),
        ("exact-name", "WalkLite 200", "keyword", 100, "9", ["shoe-001"]),
        ("exact-hybrid", "WalkLite 200", "hybrid", 100, "9", ["shoe-001"]),
        ("price-boundary", "PavementEase Knit", "hybrid", 100, "9", ["shoe-008"]),
        ("over-budget", "MetroCloud Premium", "keyword", 200, "9", ["shoe-003"]),
        ("size-nine", "WalkLite 200 Plus", "hybrid", 100, "9", ["shoe-001"]),
        ("size-ten", "WalkLite 200 Plus", "hybrid", 100, "10", ["shoe-004"]),
        ("rain", "Waterproof walking shoes for damp sidewalks", "semantic", 100, "9", ["shoe-006"]),
        (
            "unknown-weather",
            "Are CityStride Comfort shoes waterproof?",
            "hybrid",
            100,
            "9",
            ["shoe-002"],
        ),
        (
            "guide",
            "How do I clean CityStride Comfort insoles after a city walk?",
            "semantic",
            100,
            "9",
            ["shoe-002"],
        ),
        ("formal", "Polished dress shoes for office meetings", "semantic", 100, "10", "formal"),
        ("no-budget-match", "Comfortable walking shoes", "hybrid", 1, "9", []),
        ("missing-size", "Everyday sneakers", "semantic", 100, "99", []),
        (
            "no-size-filter",
            "Flexible lightweight everyday sneakers",
            "hybrid",
            100,
            None,
            "walking",
        ),
    ]
    cases = []
    for name, question, mode, budget, size, relevance in specifications:
        constraints = Constraints(max_price=budget, size=size)
        relevant_ids = [
            p["product_id"]
            for p in products
            if eligible(p, constraints)
            and (
                p["category"] == relevance
                if isinstance(relevance, str)
                else p["product_id"] in relevance
            )
        ]
        cases.append(
            {
                "id": name,
                "question": question,
                "mode": mode,
                "constraints": {"max_price": budget, "size": size},
                "relevant_ids": relevant_ids,
                "expect_empty": name in {"no-budget-match", "missing-size"},
            }
        )
    return cases


def main():
    products = make_products()
    folder = ROOT / "data"
    folder.mkdir(exist_ok=True)
    (folder / "products.jsonl").write_text(
        "".join(json.dumps(p, ensure_ascii=False) + "\n" for p in products), encoding="utf-8"
    )
    (folder / "evaluation_queries.json").write_text(
        json.dumps(make_cases(products), indent=2), encoding="utf-8"
    )
    print(f"Wrote {len(products)} fictional products and 15 evaluation cases.")


if __name__ == "__main__":
    main()
