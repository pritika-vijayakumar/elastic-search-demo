"""
elastic_client.py creates the authenticated client that the 
application uses to communicate with Elasticsearch
Settings → create_client() → Elasticsearch client → indexing and search requests
"""

from elasticsearch import Elasticsearch

from src.config import Settings

"""
Accepts your configuration as settings.
Returns an Elasticsearch client object.
"""
def create_client(settings: Settings) -> Elasticsearch:
    return Elasticsearch(
        settings.es_url, #Chooses the Elasticsearch project endpoint
        api_key=settings.es_api_key,#Authenticates requests using your encoded Elastic key
        request_timeout=settings.timeout,#Sets the timeout for each request attempt
        max_retries=2,
        retry_on_timeout=True,
    )
