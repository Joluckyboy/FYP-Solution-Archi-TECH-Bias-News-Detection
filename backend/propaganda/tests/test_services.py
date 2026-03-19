import pytest
import torch
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app import app


@pytest.fixture
def client():
    return TestClient(app)

@pytest.mark.asyncio
async def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_health_check2(client):
    response = client.get("/propaganda")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
@pytest.mark.skip(reason="Skipped due to pytest-cov/transformers tokenizer compatibility issue in CI")
async def test_analyze_propaganda(client):
    # Test with real model inference (model is loaded at module level)
    input_text = {"text": "This is an example propaganda statement."}

    response = client.post("/propaganda/analyze_propaganda", json=input_text)

    assert response.status_code == 200
    data = response.json()

    assert "propaganda_result" in data
    assert "non_propaganda_probability" in data["propaganda_result"]
    assert "propaganda_probability" in data["propaganda_result"]
    assert "formatted_result" in data["propaganda_result"]

    # Validate probabilities
    assert isinstance(data["propaganda_result"]["non_propaganda_probability"], float)
    assert isinstance(data["propaganda_result"]["propaganda_probability"], float)
    assert 0.0 <= data["propaganda_result"]["non_propaganda_probability"] <= 1.0
    assert 0.0 <= data["propaganda_result"]["propaganda_probability"] <= 1.0


def test_analyze_propaganda_missing_text_field(client):
    response = client.post("/propaganda/analyze_propaganda", json={})
    assert response.status_code == 422


def test_analyze_propaganda_mocked_inference(client):
    tokenizer_mock = MagicMock()
    tokenizer_mock.cls_token_id = 101
    tokenizer_mock.sep_token_id = 102
    tokenizer_mock.return_value = MagicMock(input_ids=torch.tensor([[11, 12]]))
    tokenizer_mock.convert_ids_to_tokens.return_value = ["test", "phrase"]

    output_mock = MagicMock(
        sequence_logits=torch.tensor([[0.2, 0.8]]),
        token_logits=torch.tensor([[[1.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 0.0]]]),
    )
    model_mock = MagicMock(return_value=output_mock)
    model_mock.token_tags = ["O", "Repetition"]

    with patch("app.tokenizer", tokenizer_mock), patch("app.model", model_mock):
        response = client.post("/propaganda/analyze_propaganda", json={"text": "Test text."})
        assert response.status_code == 200
        payload = response.json()["propaganda_result"]
        assert "non_propaganda_probability" in payload
        assert "propaganda_probability" in payload
        assert "formatted_result" in payload
        assert "techniques" in payload
