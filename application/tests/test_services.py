import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app import app
from api_models import URLwithBG
import json
import pandas as pd

client = TestClient(app)

@pytest.fixture
def mock_methods():
    with patch("app.methods") as mock, patch("app.redis_cache") as mock_cache:
        mock_cache.get_cached_result.return_value = None
        mock_cache.is_analysis_complete.return_value = False
        yield mock

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_health_check2():
    response = client.get("/application")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_check_query():
    response = client.get("/application/check_query")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_new_query_existing_url(mock_methods):
    mock_methods.check_exists.return_value = {"exists": True}
    mock_methods.get_news.return_value = {"url": "test_url", "title": "test_title", "content": "test_content"}
    response = client.post("/application/new_query", json={"url": "test_url", "background": True})
    assert response.status_code == 200
    assert response.json() == {'url': 'test_url', 'id': None, 'title': 'test_title', 'content': 'test_content', 'sentiment_result': None, 'emotion_result': None, 'propaganda_result': None, 'factcheck_result': None, 'summarise_result': None, 'data_summary': None}

def test_new_query_new_url(mock_methods):
    mock_methods.check_exists.return_value = {"exists": False}
    mock_methods.extract_news.return_value = {"body": "test_content", "headline": "test_title"}
    mock_methods.create_news.return_value = {"id": "new_id"}
    response = client.post("/application/new_query", json={"url": "test_url", "background": True})
    assert response.status_code == 200
    assert response.json() == {'url': None, 'id': 'new_id', 'title': None, 'content': None, 'sentiment_result': None, 'emotion_result': None, 'propaganda_result': None, 'factcheck_result': None, 'summarise_result': None, 'data_summary': None}

def test_retrieve_query(mock_methods):
    mock_methods.get_news_by_id.return_value = {"id": "test_id", "url": "test_url", "title": "test_title"}
    response = client.get("/application/retrieve_exisiting?news_id=test_id")
    assert response.status_code == 200
    assert response.json() == {"id": "test_id", "url": "test_url", "title": "test_title"}

def test_stream_news(mock_methods):
    def mock_generator(news_id):
        yield b'data: {"url": "test_url", "title": "test_title"}\n\n'
        yield b'data: {"url": "test_url2", "title": "test_title2"}\n\n'
        yield b'event: close\ndata: Stream timeout\n\n'

    mock_methods.get_news_by_id.side_effect = lambda news_id: {"url": "test_url", "title": "test_title"}
    with patch("app.StreamingResponse") as mock_streaming:
        mock_streaming.return_value.body = b'data: {"url": "test_url", "title": "test_title"}\n\ndata: {"url": "test_url2", "title": "test_title2"}\n\nevent: close\ndata: Stream timeout\n\n'
        response = client.get("/application/stream_news?news_id=test_id")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"


def test_get_bias_dashboard_success():
    with patch("app.dashboard_methods.load_dashboard_data", return_value={"rows": []}):
        response = client.get("/application/bias_dashboard")
        assert response.status_code == 200
        assert response.json() == {"rows": []}


def test_get_visualisations_success():
    with patch("app.visualisations.load_visualisations_data", return_value={"charts": []}):
        response = client.get("/application/visualisations")
        assert response.status_code == 200
        assert response.json() == {"charts": []}


def test_get_articles_by_keyword_empty_df():
    with patch("app.read_scraped_articles", return_value=pd.DataFrame()):
        response = client.get("/application/articles/keyword/election")
        assert response.status_code == 200
        assert response.json() == {"articles": []}


def test_get_scraper_stats_success():
    with patch("app.explanations.load_scraper_stats", return_value={"total_articles": 10}):
        response = client.get("/application/scraper_stats")
        assert response.status_code == 200
        assert response.json()["total_articles"] == 10


def test_get_source_credibility_no_data():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"articles": []}
    with patch("app.requests.get", return_value=mock_resp):
        response = client.get("/application/source_credibility?domain=cna")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "no_data"
        assert body["domain"] == "channelnewsasia.com"


def test_get_source_credibility_ok_with_metrics():
    articles = [
        {
            "sentiment_result": {"positive": 0.5, "negative": 0.2, "neutral": 0.3},
            "propaganda_result": {"propaganda_probability": 0.2, "formatted_result": [["Bandwagon", "x"]]},
            "factcheck_result": [{"correctness": "factual"}],
        },
        {
            "sentiment_result": {"positive": 0.4, "negative": 0.3, "neutral": 0.3},
            "propaganda_result": {"propaganda_probability": 0.3, "formatted_result": [["Bandwagon", "y"]]},
            "factcheck_result": [{"correctness": "mostly factual"}],
        },
        {
            "sentiment_result": {"positive": 0.3, "negative": 0.4, "neutral": 0.3},
            "propaganda_result": {"propaganda_probability": 0.1, "formatted_result": [["Name_Calling,Labeling", "z"]]},
            "factcheck_result": [{"correctness": "factual"}],
        },
    ]
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"articles": articles}
    with patch("app.requests.get", return_value=mock_resp):
        response = client.get("/application/source_credibility?domain=channelnewsasia.com")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["articles_analyzed"] == 3
        assert body["credibility_score"] is not None


def test_get_all_quiz_with_question_type(mock_methods):
    mock_methods.get_all_quiz.return_value = [{"question": "q1"}]
    response = client.get("/application/get_all_quiz?question_type=bias")
    assert response.status_code == 200
    assert response.json() == [{"question": "q1"}]


def test_get_quiz_with_number_and_type(mock_methods):
    mock_methods.get_quiz.return_value = [{"question": "q1"}]
    response = client.get("/application/get_quiz?number=3&question_type=emotion")
    assert response.status_code == 200
    assert response.json() == [{"question": "q1"}]


def test_digest_subscribe(mock_methods):
    mock_methods.subscribe_digest.return_value = {"ok": True}
    response = client.post("/application/digest/subscribe?telegram_user_id=1&chat_id=2")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_digest_unsubscribe(mock_methods):
    mock_methods.unsubscribe_digest.return_value = {"ok": True}
    response = client.post("/application/digest/unsubscribe?telegram_user_id=1")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_digest_get_subscriptions(mock_methods):
    mock_methods.get_active_subscriptions.return_value = [{"telegram_user_id": 1}]
    response = client.get("/application/digest/subscriptions")
    assert response.status_code == 200
    assert response.json() == {"subscriptions": [{"telegram_user_id": 1}]}


def test_digest_recent_biased(mock_methods):
    mock_methods.get_recent_biased_articles.return_value = [{"url": "u"}]
    response = client.get("/application/digest/recent-biased?hours=12")
    assert response.status_code == 200
    assert response.json() == {"articles": [{"url": "u"}]}


def test_related_coverage_no_title_after_fallback(mock_methods):
    mock_methods.get_news.return_value = {}
    mock_methods.extract_news.return_value = {}
    response = client.get("/application/related_coverage?url=https://example.com/a")
    assert response.status_code == 200
    body = response.json()
    assert body["matched"] is False


def test_related_coverage_success(mock_methods):
    mock_methods.get_news.return_value = {"title": "T", "content": "C"}
    analyzer_resp = MagicMock()
    analyzer_resp.status_code = 200
    analyzer_resp.json.return_value = {
        "articles": [{"title": "A"}],
        "cluster_title": "Cluster",
        "matched": True,
        "reason": "",
    }
    with patch("app._requests.post", return_value=analyzer_resp):
        response = client.get("/application/related_coverage?url=https://example.com/a")
        assert response.status_code == 200
        body = response.json()
        assert body["matched"] is True
        assert body["articles"] == [{"title": "A"}]
