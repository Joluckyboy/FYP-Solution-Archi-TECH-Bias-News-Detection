import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app import app

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_health_check2():
    response = client.get("/emotion")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch('app.model.chunk_text')
@patch('app.model.tokenizer')
@patch('app.model.classifier')
@patch('app.predict')
@patch('app.hybrid_aggregation')
def test_analyze_emotion(mock_hybrid_aggregation, mock_predict, mock_classifier, mock_tokenizer, mock_chunk_text):
    # Mock the behavior of the model and tokenizer
    mock_chunk_text.return_value = ["chunk1", "chunk2"]
    mock_tokenizer.decode.side_effect = lambda x, skip_special_tokens: x
    mock_classifier.side_effect = lambda x: [{"label": "happy", "score": 0.9}]
    mock_predict.return_value = [[{"label": "happy", "score": 0.9}], [{"label": "sad", "score": 0.1}]]
    mock_hybrid_aggregation.return_value = ({"happy": 0.9, "sad": 0.1}, [["happy", 1]])

    response = client.post("/emotion/analyze_emotion", json={"text": "I am happy today!"})

    assert response.status_code == 200
    payload = response.json()
    assert "emotion_result" in payload

    result = payload["emotion_result"]
    assert result["weighted_avg"] == {"happy": 0.9, "sad": 0.1}
    assert result["majority_vote"] == [["happy", 1]]

    # New enriched fields should be present
    assert "dominant_emotion" in result
    assert "dominant_score" in result
    assert "section_emotions" in result
    assert "sentence_emotions" in result


def test_analyze_emotion_missing_text_field():
    response = client.post("/emotion/analyze_emotion", json={})
    assert response.status_code == 422


@patch('app.predict')
@patch('app.hybrid_aggregation')
@patch('app.model.chunk_text')
def test_analyze_emotion_sentence_top_emotions(mock_chunk_text, mock_hybrid, mock_predict):
    mock_chunk_text.return_value = ["chunk"]
    mock_predict.return_value = [[{"label": "joy", "score": 0.9}]]

    def agg_side_effect(results, weights):
        return ({"joy": 0.9, "neutral": 0.05, "sadness": 0.05}, [["joy", 1]])

    mock_hybrid.side_effect = agg_side_effect

    response = client.post(
        "/emotion/analyze_emotion",
        json={"text": "This sentence is definitely long enough to be analyzed by the model."},
    )
    assert response.status_code == 200
    body = response.json()["emotion_result"]
    assert isinstance(body["section_emotions"], list)
    assert isinstance(body["sentence_emotions"], list)
    if body["sentence_emotions"]:
        assert "top_emotions" in body["sentence_emotions"][0]


@patch('app.predict')
@patch('app.hybrid_aggregation')
@patch('app.model.chunk_text')
def test_analyze_emotion_short_sentences_filtered(mock_chunk_text, mock_hybrid, mock_predict):
    mock_chunk_text.return_value = ["chunk"]
    mock_predict.return_value = [[{"label": "neutral", "score": 0.99}]]
    mock_hybrid.return_value = ({"neutral": 0.99}, [["neutral", 1]])

    response = client.post("/emotion/analyze_emotion", json={"text": "Too short."})
    assert response.status_code == 200
    result = response.json()["emotion_result"]
    assert result["sentence_emotions"] == []