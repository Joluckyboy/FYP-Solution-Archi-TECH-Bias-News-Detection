import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from db_app import app
from api_models import NewsItem
import json

client = TestClient(app)

@pytest.fixture
def mock_db_methods():
    with patch("db_app.db_methods") as mock:
        yield mock

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_health_check2():
    response = client.get("/database")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_check_url_exists_exists(mock_db_methods):
    mock_db_methods.check_url_exists.return_value = True
    response = client.post("/database/check_exists/", json={"url": "test_url"})
    assert response.status_code == 200
    assert response.json() == {"exists": True}

def test_check_url_exists_not_exists(mock_db_methods):
    mock_db_methods.check_url_exists.return_value = False
    response = client.post("/database/check_exists/", json={"url": "test_url"})
    assert response.status_code == 404
    assert response.json() == {"exists": False}

def test_create_news_new_url(mock_db_methods):
    mock_db_methods.check_url_exists.return_value = False
    mock_db_methods.create_document.return_value = "new_id"
    response = client.post("/database/", json={"url": "test_url", "title": "test_title", "content": "test_content"})
    assert response.status_code == 200
    assert response.json() == {"id": "new_id"}

def test_create_news_existing_url(mock_db_methods):
    mock_db_methods.check_url_exists.return_value = True
    mock_db_methods.read_document_by_url.return_value = {"url": "test_url", "title": "existing_title", "content": "existing_content"}
    response = client.post("/database/", json={"url": "test_url", "title": "test_title", "content": "test_content"})
    assert response.status_code == 201
    assert response.json() == {"url": "test_url", "title": "existing_title", "content": "existing_content"}

def test_get_all_news(mock_db_methods):
    mock_db_methods.read_all_documents.return_value = [{"url": "url1", "title": "title1", "content": "content1"}, {"url": "url2", "title": "title2", "content": "content2"}]
    response = client.get("/database/getAll/")
    assert response.status_code == 200
    assert response.json() == {"news_id": [{"url": "url1", "title": "title1", "content": "content1"}, {"url": "url2", "title": "title2", "content": "content2"}]}

def test_get_news_by_filter_exists(mock_db_methods):
    mock_db_methods.read_document_by_url.return_value = {"url": "test_url", "title": "test_title", "content": "test_content"}
    response = client.post("/database/getByURL/", json={"url": "test_url"})
    assert response.status_code == 200
    assert response.json() == {"url": "test_url", "title": "test_title", "content": "test_content"}

def test_get_news_by_filter_not_exists(mock_db_methods):
    mock_db_methods.read_document_by_url.return_value = None
    response = client.post("/database/getByURL/", json={"url": "test_url"})
    assert response.status_code == 404
    assert response.json() == {"detail": "News not found"}

def test_get_news_by_id_exists(mock_db_methods):
    mock_db_methods.read_document_by_id.return_value = {"url": "test_url", "title": "test_title", "content": "test_content"}
    response = client.get("/database/getByID/test_id")
    assert response.status_code == 200
    assert response.json() == {"url": "test_url", "title": "test_title", "content": "test_content"}

def test_get_news_by_id_not_exists(mock_db_methods):
    mock_db_methods.read_document_by_id.return_value = None
    response = client.get("/database/getByID/test_id")
    assert response.status_code == 404
    assert response.json() == {"detail": "News not found"}

def test_update_news_summary_by_url(mock_db_methods):
    mock_db_methods.update_summary_by_url.return_value = None
    response = client.put("/database/summarise/", json={"url": "test_url", "summarise_result": "test_summary"})
    assert response.status_code == 200
    assert response.json() == {"message": "Summary result updated successfully"}

def test_update_news_data_summary_by_url(mock_db_methods):
    mock_db_methods.update_model_data_summary_by_url.return_value = None
    response = client.put("/database/ModelDataSummary/", json={"url": "test_url", "data_summary": {"key": "value"}})
    assert response.status_code == 200
    assert response.json() == {"message": "Model data summary result updated successfully"}

def test_update_news_factcheck_by_url(mock_db_methods):
    mock_db_methods.update_factcheck_by_url.return_value = None
    response = client.put("/database/factcheck/", json={"url": "test_url", "factcheck_result": [{"statement": "test", "correctness": "true", "explanation": "test", "citations": []}]})
    assert response.status_code == 200
    assert response.json() == {"message": "Fact-check result updated successfully"}

def test_update_news_sentiment_by_url(mock_db_methods):
    mock_db_methods.update_sentiment_by_url.return_value = None
    response = client.put("/database/sentiment/", json={"url": "test_url", "sentiment_result": {"positive": 0.5}})
    assert response.status_code == 200
    assert response.json() == {"message": "Sentiment result updated successfully"}

def test_update_news_emotion_by_url(mock_db_methods):
    mock_db_methods.update_emotion_by_url.return_value = None
    response = client.put("/database/emotion/", json={"url": "test_url", "emotion_result": {"joy": 0.5}})
    assert response.status_code == 200
    assert response.json() == {"message": "Emotion result updated successfully"}

def test_update_news_propaganda_by_url(mock_db_methods):
    mock_db_methods.update_propaganda_by_url.return_value = None
    response = client.put("/database/propaganda/", json={"url": "test_url", "propaganda_result": {"propaganda": True}})
    assert response.status_code == 200
    assert response.json() == {"message": "Propaganda result updated successfully"}

def test_update_news_sentiment(mock_db_methods):
    mock_db_methods.update_sentiment_result.return_value = None
    response = client.put("/database/test_id/sentiment/", json={"sentiment_result": {"positive": 0.5}})
    assert response.status_code == 200
    assert response.json() == {"message": "Sentiment result updated successfully"}

def test_update_news_emotion(mock_db_methods):
    mock_db_methods.update_emotion_result.return_value = None
    response = client.put("/database/test_id/emotion/", json={"emotion_result": {"joy": 0.5}})
    assert response.status_code == 200
    assert response.json() == {"message": "Emotion result updated successfully"}

def test_update_news_propaganda(mock_db_methods):
    mock_db_methods.update_propaganda_result.return_value = None
    response = client.put("/database/test_id/propaganda/", json={"propaganda_result": {"propaganda": True}})
    assert response.status_code == 200
    assert response.json() == {"message": "Propaganda result updated successfully"}

def test_delete_news_by_id(mock_db_methods):
    mock_db_methods.delete_document_by_id.return_value = 1
    response = client.delete("/database/test_id")
    assert response.status_code == 200
    assert response.json() == {"deleted_count": 1}

def test_stream_news(mock_db_methods):
    def mock_generator():
        yield b'data: {"url": "test_url", "title": "test_title"}\n\n'
        yield b'data: {"url": "test_url2", "title": "test_title2"}\n\n'

    mock_db_methods.stream_document_by_id.return_value = mock_generator()

    response = client.get("/database/stream_news?news_id=test_id")
    assert response.status_code == 200

    lines = [line for line in response.iter_lines()]
    assert lines == [
        'data: {"url": "test_url", "title": "test_title"}',
        '',
        'data: {"url": "test_url2", "title": "test_title2"}',
        '',
        ]
