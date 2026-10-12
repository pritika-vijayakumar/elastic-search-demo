from elasticsearch import Elasticsearch

from src.config import Settings


def create_client(settings: Settings) -> Elasticsearch:
    return Elasticsearch(
        settings.es_url,
        api_key=settings.es_api_key,
        request_timeout=settings.timeout,
        max_retries=2,
        retry_on_timeout=True,
    )
