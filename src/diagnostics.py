"""
diagnostics.py checks whether the Elastic configuration matches what this demo expects and turns errors into readable messages.
"""
import json

from src.config import ROOT, Settings


def inspect_endpoint(client, settings: Settings) -> dict:
    response = client.inference.get(inference_id=settings.inference_id)
    endpoints = response.get("endpoints", [])
    endpoint = next((e for e in endpoints if e.get("inference_id") == settings.inference_id), None)
    if endpoint is None:
        raise ValueError("Configured inference endpoint was not found.")
    service = endpoint.get("service")
    model = endpoint.get("service_settings", {}).get("model_id", "")
    task = endpoint.get("task_type")
    if service != "elastic" or "jina" not in model.lower() or task != "text_embedding":
        raise ValueError(
            "This demo requires a Jina text_embedding endpoint on EIS (service: elastic)."
        )
    return {
        "inference_id": settings.inference_id,
        "service": service,
        "model_id": model,
        "task_type": task,
    }


def index_definition(settings: Settings) -> dict:
    definition = json.loads((ROOT / "config" / "products-index.json").read_text(encoding="utf-8"))
    definition["mappings"]["properties"]["searchable_content"]["inference_id"] = (
        settings.inference_id
    )
    return definition


def verify_index(client, settings: Settings) -> dict:
    mapping = client.indices.get_mapping(index=settings.es_index)[settings.es_index]["mappings"]
    expected = index_definition(settings)["mappings"]["properties"]
    actual = mapping.get("properties", {})
    for name, field in expected.items():
        if actual.get(name, {}).get("type") != field.get("type"):
            raise ValueError(f"Index field {name} has a different type. Use a new demo index name.")
    semantic = actual["searchable_content"]
    if semantic.get("inference_id") != settings.inference_id:
        raise ValueError(
            "Existing index uses a different inference endpoint; use a new index name."
        )
    variant_fields = actual["variants"].get("properties", {})
    if any(
        variant_fields.get(k, {}).get("type") != v["type"]
        for k, v in expected["variants"]["properties"].items()
    ):
        raise ValueError("Variant mapping does not match the demo schema.")
    return {"semantic_field": semantic, "variant_field": actual["variants"]}


def inspect_project(client, settings: Settings) -> dict:
    result = {"endpoint": inspect_endpoint(client, settings), "index_exists": False}
    if client.indices.exists(index=settings.es_index):
        result["index_exists"] = True
        result["mapping"] = verify_index(client, settings)
        index_settings = client.indices.get_settings(index=settings.es_index)
        result["index_settings"] = dict(index_settings[settings.es_index]["settings"]["index"])
        result["product_count"] = client.count(index=settings.es_index)["count"]
    return result


def error_message(error: Exception) -> str:
    """Avoid displaying raw provider errors, which can include request data or secrets."""
    if isinstance(error, ValueError):
        return str(error)
    status = getattr(error, "status_code", None)
    hints = {
        401: "Check the API key for the failing service.",
        403: "Check API-key permissions and feature access.",
        404: "Check the project, index, inference endpoint, and OpenAI model names.",
        429: "Check quota, billing, and rate limits; then retry.",
        400: "Check deployment support for semantic_text, RRF, and vector index mode.",
    }
    return (
        f"{type(error).__name__}"
        + (f" (HTTP {status})" if status else "")
        + ": "
        + hints.get(status, "Check connectivity and service status. See README troubleshooting.")
    )
