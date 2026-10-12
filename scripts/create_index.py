from src.config import load_settings
from src.diagnostics import error_message, index_definition, inspect_endpoint
from src.elastic_client import create_client


def main():
    settings = load_settings(require_openai=False)
    with create_client(settings) as client:
        inspect_endpoint(client, settings)
        if client.indices.exists(index=settings.es_index):
            raise ValueError(
                "Index already exists. No changes made. Choose a new ES_INDEX to start fresh."
            )
        client.indices.create(index=settings.es_index, body=index_definition(settings))
        print(
            f"Created {settings.es_index}; semantic_text will generate embeddings during ingestion."
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(error_message(exc)) from None
