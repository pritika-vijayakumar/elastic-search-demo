"""
ingest.py uploads your local product catalog into Elasticsearch. This makes the products available for keyword and semantic search.
"""


from elasticsearch.helpers import streaming_bulk

from src.catalog import index_document, load_catalog
from src.config import ROOT, load_settings
from src.diagnostics import error_message, inspect_endpoint, verify_index
from src.elastic_client import create_client


def main():
    settings = load_settings(require_openai=False)
    products = load_catalog(ROOT / "data" / "products.jsonl")
    successes, failures = 0, []
    with create_client(settings) as client:
        #Check Elasticsearch before uploading
        inspect_endpoint(client, settings)
        verify_index(client, settings)
        # create prevents accidental overwrites. Duplicate IDs fail visibly on a second run.
        actions = (
            {
                "_op_type": "create",
                "_index": settings.es_index,
                "_id": p.product_id,
                "_source": index_document(p),
            }
            for p in products
        )
        for ok, item in streaming_bulk(
            client, actions, chunk_size=10, raise_on_error=False, max_retries=2
        ):
            detail = item["create"]
            if ok:
                successes += 1
            else:
                failures.append(
                    {
                        "id": detail.get("_id"),
                        "status": detail.get("status"),
                        "error_type": detail.get("error", {}).get("type", "unknown"),
                    }
                )
        client.indices.refresh(index=settings.es_index)
        print(f"Created {successes} products; {len(failures)} failures.")
        for failure in failures:
            print(failure)
        if failures:
            raise ValueError(
                "Ingestion incomplete. 409 means the product already exists; no overwrite occurred."
            )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(error_message(exc)) from None
