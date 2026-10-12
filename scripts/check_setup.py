import argparse
import json

from openai import OpenAI

from src.answer import generate_answer
from src.config import load_settings
from src.diagnostics import error_message, inspect_project
from src.elastic_client import create_client


def main():
    parser = argparse.ArgumentParser(
        description="Check Elastic and OpenAI setup without printing keys."
    )
    parser.add_argument(
        "--live-answer", action="store_true", help="Also make a billable OpenAI test call."
    )
    args = parser.parse_args()
    settings = load_settings()
    with create_client(settings) as client:
        print(json.dumps(inspect_project(client, settings), indent=2, default=str))
    api = OpenAI(api_key=settings.openai_api_key, timeout=settings.timeout)
    api.models.retrieve(settings.openai_model)
    print(f"OpenAI model accessible: {settings.openai_model}")
    print(
        "Model lookup alone does not verify generation access. Use --live-answer to test Responses."
    )
    if args.live_answer:
        context = {
            "question": "Any walking shoes under $1?",
            "constraints": {"max_price": 1},
            "products": [],
        }
        print(json.dumps(generate_answer(settings, context, api), indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(error_message(exc)) from None
