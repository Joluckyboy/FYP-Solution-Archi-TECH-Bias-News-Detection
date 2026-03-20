import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

@pytest.fixture
def mock_model():
    with patch("app.model") as mock:
        mock.predict_sentiment_batch_sentences.return_value = [
            [0.2, 0.7, 0.1],  # [negative, neutral, positive] for one sentence
        ]
        yield mock

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_health_check2():
    response = client.get("/sentiment")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_analyze_sentiment(mock_model):
    payload = {"text": "This is a test sentence."}
    response = client.post("/sentiment/analyze_sentiment", json=payload)

    assert response.status_code == 200
    result = response.json()["sentiment_result"]

    assert "positive" in result
    assert "negative" in result
    assert "neutral" in result

    # Ensure the new batched model method was called
    mock_model.predict_sentiment_batch_sentences.assert_called_once_with([payload["text"]])

    # Check the values of the sentiment results
    total_weight = 3
    positive_score = 0.1
    negative_score = 0.2
    neutral_score = 0.7

    assert result["positive"] == pytest.approx(positive_score, rel=1e-2)
    assert result["negative"] == pytest.approx(negative_score, rel=1e-2)
    assert result["neutral"] == pytest.approx(neutral_score, rel=1e-2)


def test_analyze_sentiment_missing_text_field():
    response = client.post("/sentiment/analyze_sentiment", json={})
    assert response.status_code == 422


def test_analyze_sentiment_empty_text_returns_neutral():
    response = client.post("/sentiment/analyze_sentiment", json={"text": "   "})
    assert response.status_code == 200
    payload = response.json()
    result = payload["sentiment_result"]
    assert result["positive"] == 0.0
    assert result["negative"] == 0.0
    assert result["neutral"] == 1.0
    assert result["sentence_sentiments"] == []


def test_analyze_sentiment_multiple_sentences_batch_call():
    with patch("app.model") as mock_model:
        mock_model.predict_sentiment_batch_sentences.return_value = [
            [0.1, 0.2, 0.7],
            [0.7, 0.2, 0.1],
        ]
        response = client.post(
            "/sentiment/analyze_sentiment",
            json={"text": "First sentence. Second sentence."},
        )

        assert response.status_code == 200
        mock_model.predict_sentiment_batch_sentences.assert_called_once()
        called_sentences = mock_model.predict_sentiment_batch_sentences.call_args[0][0]
        assert len(called_sentences) == 2


def test_analyze_sentiment_max_sentences_cap():
    long_text = " ".join([f"This is a sufficiently long sentence number {i}." for i in range(60)])
    with patch("app.model") as mock_model:
        mock_model.predict_sentiment_batch_sentences.return_value = [
            [0.2, 0.6, 0.2 + (i * 0.0001)] for i in range(50)
        ]
        response = client.post("/sentiment/analyze_sentiment", json={"text": long_text})
        assert response.status_code == 200
        called_sentences = mock_model.predict_sentiment_batch_sentences.call_args[0][0]
        assert len(called_sentences) == 50