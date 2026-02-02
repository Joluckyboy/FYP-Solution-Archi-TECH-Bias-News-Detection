import pytest
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
