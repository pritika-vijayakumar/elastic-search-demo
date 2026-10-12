import argparse
import json
from datetime import UTC, datetime

from src.answer import generate_answer
from src.config import ROOT, load_settings
from src.context import build_context
from src.diagnostics import error_message, verify_index
from src.elastic_client import create_client
from src.search import Constraints, eligible, run_search


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate retrieval; optionally include billable OpenAI answers."
    )
    parser.add_argument("--answers", action="store_true")
    args = parser.parse_args()
    settings = load_settings(require_openai=args.answers)
    cases = json.loads((ROOT / "data" / "evaluation_queries.json").read_text(encoding="utf-8"))
    rows = []
    with create_client(settings) as client:
        verify_index(client, settings)
        for case in cases:
            constraints = Constraints(**case["constraints"])
            result = run_search(
                client, settings.es_index, case["question"], case["mode"], constraints
            )
            ids = [p["product_id"] for p in result["products"]]
            relevant = set(case["relevant_ids"])
            matched = relevant.intersection(ids)
            row = {
                "case": case["id"],
                "returned_ids": ids,
                "elapsed_ms": result["elapsed_ms"],
                "precision_at_5": len(matched) / len(ids) if ids else None,
                "recall_at_5": len(matched) / len(relevant) if relevant else None,
                "constraints_pass": all(eligible(p, constraints) for p in result["products"]),
                "empty_expectation_pass": not ids if case.get("expect_empty") else None,
            }
            if args.answers:
                row["generation"] = generate_answer(settings, build_context(result))
            rows.append(row)
    report = {
        "created_utc": datetime.now(UTC).isoformat(),
        "note": "Curated relevance judgments; inspect results manually. No latency SLA implied.",
        "results": rows,
    }
    path = ROOT / "reports" / "evaluation.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Evaluated {len(rows)} cases. Report: {path}")
    if any(not r["constraints_pass"] or r["empty_expectation_pass"] is False for r in rows):
        raise ValueError("Evaluation found a constraint or empty-result failure.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(error_message(exc)) from None
