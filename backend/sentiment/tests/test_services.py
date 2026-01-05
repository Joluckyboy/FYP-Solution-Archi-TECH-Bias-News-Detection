import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

@pytest.fixture
def mock_model():
    with patch("app.model") as mock:
        mock.chunk_text.return_value = [
            {"input_ids": [[1, 2, 3]], "attention_mask": [[1, 1, 1]]},
        ]
        mock.predict_sentiment.side_effect = [
            [0.2, 0.7, 0.1],  # Mocked sentiment scores for first chunk
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

    # Ensure the model methods were called
    mock_model.chunk_text.assert_called_once_with(payload["text"])
    assert mock_model.predict_sentiment.call_count == 1

    # Check the values of the sentiment results
    total_weight = 3
    positive_score = 0.1
    negative_score = 0.2
    neutral_score = 0.7

    assert result["positive"] == pytest.approx(positive_score, rel=1e-2)
    assert result["negative"] == pytest.approx(negative_score, rel=1e-2)
    assert result["neutral"] == pytest.approx(neutral_score, rel=1e-2)