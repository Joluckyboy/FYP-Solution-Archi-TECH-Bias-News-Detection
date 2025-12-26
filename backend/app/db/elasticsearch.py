from elasticsearch import Elasticsearch
from app.core.config import settings

es_client = Elasticsearch([settings.ELASTICSEARCH_URL])

def get_elasticsearch():
    return es_client
