import os
import sys
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import analyzer.app as analyzer_app_module



def _client():
    with patch.object(analyzer_app_module.s3_sync, "ensure_scraped_csv", return_value=None):
        with TestClient(analyzer_app_module.app) as client:
            yield client


def test_health_root():
    client = next(_client())
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_service():
    client = next(_client())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "analyzer"


@patch("analyzer.app.fetch_topics_data")
def test_dashboard_topics(mock_fetch):
    mock_fetch.return_value = ([
        {
            "id": 1,
            "title": "Topic 1",
            "topic_name": "Politics",
            "image": None,
            "all_images": [],
            "source_count": 2,
            "bias_distribution": {"left": 0.2, "center": 0.5, "right": 0.3},
            "latest_date": "2026-03-19",
            "articles": [{"url": "https://example.com/a"}],
        }
    ], None)
    client = next(_client())
    response = client.get("/dashboard/topics")
    assert response.status_code == 200
    body = response.json()
    assert "topics" in body
    assert body["topics"][0]["id"] == 1


@patch("analyzer.app.fetch_topics_data")
def test_dashboard_topic_details_not_found(mock_fetch):
    mock_fetch.return_value = ([], None)
    client = next(_client())
    response = client.get("/dashboard/topic_details/999")
    assert response.status_code == 404


@patch("analyzer.app.fetch_topics_data")
@patch("analyzer.app.get_summary_service")
def test_dashboard_topic_enrichment(mock_summary_service, mock_fetch):
    topic = {"id": 1, "title": "Topic 1", "articles": []}
    mock_fetch.return_value = ([topic], None)

    summary_service = MagicMock()
    summary_service.enrich_topic_with_deep_summary.return_value = {
        **topic,
        "contextual_insight": "context",
        "has_deep_summary": True,
    }
    summary_service.generate_comparative_analysis.return_value = {
        **topic,
        "contextual_insight": "context",
        "comparative_analysis": "analysis",
        "has_deep_summary": True,
    }
    mock_summary_service.return_value = summary_service

    client = next(_client())
    response = client.get("/dashboard/topic_enrichment/1")
    assert response.status_code == 200
    body = response.json()
    assert body["has_deep_summary"] is True


@patch("analyzer.app._safe_read_csv")
def test_trending_keywords_empty(mock_csv):
    mock_csv.return_value = None
    client = next(_client())
    response = client.get("/dashboard/trending_keywords")
    assert response.status_code == 200
    assert response.json() == {"keywords": []}


@patch("analyzer.app._safe_read_csv")
def test_topic_coverage_empty(mock_csv):
    mock_csv.return_value = None
    client = next(_client())
    response = client.get("/dashboard/topic_coverage")
    assert response.status_code == 200
    assert response.json() == {"topics": [], "coverage": []}


@patch.dict(os.environ, {"S3_BUCKET": "test-bucket", "AWS_REGION": "ap-southeast-1"}, clear=False)
@patch("boto3.client")
@patch("analyzer.app._safe_read_csv")
@patch("analyzer.core.services.get_topic_service")
def test_cluster_endpoint_success(mock_get_topic_service, mock_safe_csv, mock_boto_client):
    import pandas as pd

    mock_s3 = MagicMock()
    mock_boto_client.return_value = mock_s3

    df = pd.DataFrame([
        {"title": "A", "source": "CNA", "topic": "Politics", "published_at": "2026-03-19"}
    ])
    mock_safe_csv.return_value = df

    topic_service = MagicMock()
    topic_service.cluster_articles.return_value = [{"id": 1, "articles": [{"title": "A"}]}]
    mock_get_topic_service.return_value = topic_service

    client = next(_client())
    response = client.post("/dashboard/cluster")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@patch("analyzer.app.os.path.exists")
def test_related_articles_requires_title(mock_exists):
    mock_exists.return_value = True
    client = next(_client())
    response = client.post("/dashboard/related_articles", json={"title": ""})
    assert response.status_code == 400


@patch("analyzer.app.os.path.exists")
def test_related_articles_missing_csv(mock_exists):
    mock_exists.return_value = False
    client = next(_client())
    response = client.post("/dashboard/related_articles", json={"title": "Any title"})
    assert response.status_code == 200
    assert response.json()["matched"] is False
