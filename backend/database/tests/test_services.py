import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from db_app import app
from api_models import NewsItem
import json

client = TestClient(app)


@pytest.fixture
def mock_db_methods():
    with patch("db_app.news_methods") as mock:
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
    response = client.post(
        "/database/", json={"url": "test_url", "title": "test_title", "content": "test_content"})
    assert response.status_code == 200
    assert response.json() == {"id": "new_id"}


def test_create_news_existing_url(mock_db_methods):
    mock_db_methods.check_url_exists.return_value = True
    mock_db_methods.read_document_by_url.return_value = {
        "url": "test_url", "title": "existing_title", "content": "existing_content"}
    response = client.post(
        "/database/", json={"url": "test_url", "title": "test_title", "content": "test_content"})
    assert response.status_code == 201
    assert response.json() == {
        "url": "test_url", "title": "existing_title", "content": "existing_content"}


def test_get_all_news(mock_db_methods):
    mock_db_methods.read_all_documents.return_value = [{"url": "url1", "title": "title1", "content": "content1"}, {
        "url": "url2", "title": "title2", "content": "content2"}]
    response = client.get("/database/getAll/")
    assert response.status_code == 200
    assert response.json() == {"news_id": [{"url": "url1", "title": "title1", "content": "content1"}, {
        "url": "url2", "title": "title2", "content": "content2"}]}


def test_get_news_by_filter_exists(mock_db_methods):
    mock_db_methods.read_document_by_url.return_value = {
        "url": "test_url", "title": "test_title", "content": "test_content"}
    response = client.post("/database/getByURL/", json={"url": "test_url"})
    assert response.status_code == 200
    assert response.json() == {"url": "test_url",
                               "title": "test_title", "content": "test_content"}


def test_get_news_by_filter_not_exists(mock_db_methods):
    mock_db_methods.read_document_by_url.return_value = None
    response = client.post("/database/getByURL/", json={"url": "test_url"})
    assert response.status_code == 404
    assert response.json() == {"detail": "News not found"}


def test_get_news_by_id_exists(mock_db_methods):
    mock_db_methods.read_document_by_id.return_value = {
        "url": "test_url", "title": "test_title", "content": "test_content"}
    response = client.get("/database/getByID/test_id")
    assert response.status_code == 200
    assert response.json() == {"url": "test_url",
                               "title": "test_title", "content": "test_content"}


def test_get_news_by_id_not_exists(mock_db_methods):
    mock_db_methods.read_document_by_id.return_value = None
    response = client.get("/database/getByID/test_id")
    assert response.status_code == 404
    assert response.json() == {"detail": "News not found"}


def test_update_news_summary_by_url(mock_db_methods):
    mock_db_methods.update_summary_by_url.return_value = None
    response = client.put("/database/summarise/",
                          json={"url": "test_url", "summarise_result": "test_summary"})
    assert response.status_code == 200
    assert response.json() == {
        "message": "Summary result updated successfully"}


def test_update_news_data_summary_by_url(mock_db_methods):
    mock_db_methods.update_model_data_summary_by_url.return_value = None
    response = client.put("/database/ModelDataSummary/",
                          json={"url": "test_url", "data_summary": {"key": "value"}})
    assert response.status_code == 200
    assert response.json() == {
        "message": "Model data summary result updated successfully"}


def test_update_news_factcheck_by_url(mock_db_methods):
    mock_db_methods.update_factcheck_by_url.return_value = None
    response = client.put("/database/factcheck/", json={"url": "test_url", "factcheck_result": [
                          {"statement": "test", "correctness": "true", "explanation": "test", "citations": []}]})
    assert response.status_code == 200
    assert response.json() == {
        "message": "Fact-check result updated successfully"}


def test_update_news_sentiment_by_url(mock_db_methods):
    mock_db_methods.update_sentiment_by_url.return_value = None
    response = client.put("/database/sentiment/",
                          json={"url": "test_url", "sentiment_result": {"positive": 0.5}})
    assert response.status_code == 200
    assert response.json() == {
        "message": "Sentiment result updated successfully"}


def test_update_news_emotion_by_url(mock_db_methods):
    mock_db_methods.update_emotion_by_url.return_value = None
    response = client.put(
        "/database/emotion/", json={"url": "test_url", "emotion_result": {"joy": 0.5}})
    assert response.status_code == 200
    assert response.json() == {
        "message": "Emotion result updated successfully"}


def test_update_news_propaganda_by_url(mock_db_methods):
    mock_db_methods.update_propaganda_by_url.return_value = None
    response = client.put("/database/propaganda/",
                          json={"url": "test_url", "propaganda_result": {"propaganda": True}})
    assert response.status_code == 200
    assert response.json() == {
        "message": "Propaganda result updated successfully"}


def test_update_news_political_bias_by_url(mock_db_methods):
    mock_db_methods.update_political_bias_by_url.return_value = None
    response = client.put(
        "/database/political_bias/",
        json={"url": "test_url", "political_bias_result": {"rating": "center"}},
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": "Political bias result updated successfully"}


def test_update_news_sentiment(mock_db_methods):
    mock_db_methods.update_sentiment_result.return_value = None
    response = client.put("/database/test_id/sentiment/",
                          json={"sentiment_result": {"positive": 0.5}})
    assert response.status_code == 200
    assert response.json() == {
        "message": "Sentiment result updated successfully"}


def test_update_news_emotion(mock_db_methods):
    mock_db_methods.update_emotion_result.return_value = None
    response = client.put("/database/test_id/emotion/",
                          json={"emotion_result": {"joy": 0.5}})
    assert response.status_code == 200
    assert response.json() == {
        "message": "Emotion result updated successfully"}


def test_update_news_propaganda(mock_db_methods):
    mock_db_methods.update_propaganda_result.return_value = None
    response = client.put("/database/test_id/propaganda/",
                          json={"propaganda_result": {"propaganda": True}})
    assert response.status_code == 200
    assert response.json() == {
        "message": "Propaganda result updated successfully"}


def test_delete_news_by_id(mock_db_methods):
    mock_db_methods.delete_document_by_id.return_value = 1
    response = client.delete("/database/test_id")
    assert response.status_code == 200
    assert response.json() == {"deleted_count": 1}


def test_get_news_by_domain(mock_db_methods):
    mock_db_methods.read_documents_by_domain.return_value = [{"url": "u1"}]
    response = client.get("/database/getByDomain/channelnewsasia.com")
    assert response.status_code == 200
    assert response.json() == {"articles": [{"url": "u1"}]}


def test_delete_news_by_filter(mock_db_methods):
    mock_db_methods.delete_documents.return_value = 2
    response = client.request(
        "DELETE",
        "/database/",
        json={"url": "https://example.com", "title": "t", "content": "c"},
    )
    assert response.status_code == 200
    assert response.json() == {"deleted_count": 2}


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


def test_add_quiz(mock_db_methods):
    with patch("db_app.quiz_methods") as mock_quiz_methods:
        mock_quiz_methods.add_quiz_data.return_value = "quiz-1"
        response = client.post(
            "/database/quiz/add",
            json={
                "question": "Q?",
                "options": ["A", "B", "C"],
                "answer": [0],
                "question_type": "bias",
                "debrief": "D",
            },
        )
        assert response.status_code == 200
        assert response.json() == {"quiz_id": "quiz-1"}


def test_get_all_quiz(mock_db_methods):
    with patch("db_app.quiz_methods") as mock_quiz_methods:
        mock_quiz_methods.get_all_quiz_data.return_value = [{"question": "Q1"}]
        response = client.get("/database/quiz/getAll?question_type=bias")
        assert response.status_code == 200
        assert response.json() == {"quiz": [{"question": "Q1"}]}


def test_get_random_quiz(mock_db_methods):
    with patch("db_app.quiz_methods") as mock_quiz_methods:
        mock_quiz_methods.get_random_quiz_data.return_value = [{"question": "Q1"}]
        response = client.get("/database/quiz/getRandom?number=2&question_type=bias")
        assert response.status_code == 200
        assert response.json() == {"quiz": [{"question": "Q1"}]}


def test_create_subscription(mock_db_methods):
    mock_db_methods.create_subscription.return_value = {"telegram_user_id": 1, "chat_id": 2}
    response = client.post("/database/subscriptions/", json={"telegram_user_id": 1, "chat_id": 2})
    assert response.status_code == 200
    assert response.json()["message"] == "Subscribed successfully"


def test_remove_subscription(mock_db_methods):
    mock_db_methods.remove_subscription.return_value = True
    response = client.delete("/database/subscriptions/1")
    assert response.status_code == 200
    assert response.json() == {"message": "Unsubscribed successfully"}


def test_get_active_subscriptions(mock_db_methods):
    mock_db_methods.get_active_subscriptions.return_value = [{"telegram_user_id": 1}]
    response = client.get("/database/subscriptions/active")
    assert response.status_code == 200
    assert response.json() == {"subscriptions": [{"telegram_user_id": 1}]}


def test_get_recent_biased_articles(mock_db_methods):
    mock_db_methods.get_recent_biased_articles.return_value = [{"url": "u"}]
    response = client.get("/database/articles/recent-biased?hours=48")
    assert response.status_code == 200
    assert response.json() == {"articles": [{"url": "u"}]}


def test_add_multiple_quiz(mock_db_methods):
    with patch("db_app.quiz_methods") as mock_quiz_methods:
        mock_quiz_methods.add_quiz_data.side_effect = ["q1", "q2"]
        response = client.post(
            "/database/quiz/addMultiple",
            json=[
                {"question": "Q1", "options": ["A", "B"], "answer": [0], "question_type": "bias", "debrief": "d1"},
                {"question": "Q2", "options": ["A", "B"], "answer": [1], "question_type": "bias", "debrief": "d2"},
            ],
        )
        assert response.status_code == 200
        assert response.json() == {"quiz_id": ["q1", "q2"]}


def test_generate_and_save_quiz(mock_db_methods):
    with patch("db_app.quiz_templates.generate_quiz_from_analysis") as mock_gen, patch("db_app.quiz_methods") as mock_quiz_methods:
        mock_gen.return_value = [
            {
                "question": "Q",
                "options": ["A", "B"],
                "correct_answer": "A",
                "debrief": "D",
            }
        ]
        mock_quiz_methods.add_quiz_data.return_value = "qid-1"
        response = client.post("/database/quiz/generate-and-save?question_type=bias")
        assert response.status_code == 200
        assert response.json()["count"] == 1


def test_seed_quiz_category(mock_db_methods):
    with patch("db_app.quiz_templates.generate_ai_quiz_questions") as mock_gen, patch("db_app.quiz_methods") as mock_quiz_methods:
        mock_gen.return_value = [
            {
                "question": "Q",
                "options": ["A", "B"],
                "answer": [0],
                "debrief": "D",
            }
        ]
        mock_quiz_methods.add_quiz_data.return_value = "qid-1"
        response = client.post("/database/quiz/seed/bias")
        assert response.status_code == 200
        assert response.json() == {"quiz_ids": ["qid-1"], "category": "bias"}
