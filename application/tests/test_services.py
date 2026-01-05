import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app import app
from api_models import URLwithBG
import json

client = TestClient(app)

@pytest.fixture
def mock_methods():
    with patch("app.methods") as mock:
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
