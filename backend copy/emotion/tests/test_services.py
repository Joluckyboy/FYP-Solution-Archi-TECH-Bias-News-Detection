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
    assert response.json() == {
        "emotion_result": {
            "weighted_avg": {"happy": 0.9, "sad": 0.1},
            "majority_vote": [["happy", 1]]
        }
    }