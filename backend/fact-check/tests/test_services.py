import pytest
import asyncio
import json
import re
from unittest.mock import patch, AsyncMock, MagicMock, ANY
from fastapi.testclient import TestClient

from service.predict_service import processStatement, summarise, summarise_data, getStatement, fact_check
from models.datapayload import DataPayload, ModelDataPayload
from config.config import Config
from app.main import app as api_app

client = TestClient(api_app)

@pytest.mark.parametrize("content, expected", [
    ('```json[{"statement": "Fact 1"}, {"statement": "Fact 2"}]```', ["Fact 1", "Fact 2"]),
    ('[{"statement": "Only Fact"}]', ["Only Fact"]),
    ('```json[{"statement": "Test"}]```', ["Test"]),
])
def test_processStatement(content, expected):
    assert processStatement(content) == expected


def test_processStatement_empty_payload():
    assert processStatement("[]") == []

@patch("requests.post")
def test_summarise(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "<think>irrelevant</think> Summary result"}}]
    }
    mock_post.return_value = mock_response

    text = "This is a long article that needs summarization."
    result = asyncio.run(summarise(text))

    assert result == "<think>irrelevant</think> Summary result"
    mock_post.assert_called_once_with(Config.DEEPSEEK_URL, headers=Config.HEADERS_DS, json=ANY)

@patch("requests.post")
def test_summarise_data(mock_post):
    json_payload = ModelDataPayload(
        sentiment_result={"Positive": 0.9},
        emotion_result={"Happy": 0.8},
        propaganda_result={"None": 0.95},
        political_bias_result={"rating": "center", "topics": {"covered": ["A"], "omitted": ["B"]}},
        summarise_result="This is the summary."
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"sentiment_summary": "Positive", "emotion_summary": "Happy", "propaganda_summary": "None", "political_bias_summary": "Center"}'}}]
    }
    mock_post.return_value = mock_response

    result = asyncio.run(summarise_data(json_payload))

    assert result == '{"sentiment_summary": "Positive", "emotion_summary": "Happy", "propaganda_summary": "None", "political_bias_summary": "Center"}'
    mock_post.assert_called_once_with(Config.DEEPSEEK_URL, headers=Config.HEADERS_DS, json=ANY)

@patch("requests.post")
def test_getStatement(mock_post):
    json_payload = DataPayload(content="This is a test article.", title="Test Title")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "```json[{\"statement\": \"Test statement 1\"}, {\"statement\": \"Test statement 2\"}]```"}}]
    }
    mock_post.return_value = mock_response

    result = asyncio.run(getStatement(json_payload))

    assert result == ["Test statement 1", "Test statement 2"]
    mock_post.assert_called_once_with(
        Config.PERPLEXITY_URL if Config.MODEL == "sonar" else Config.DEEPSEEK_URL,
        headers=Config.HEADERS if Config.MODEL == "sonar" else Config.HEADERS_DS,
        json=ANY
    )

@patch("requests.post")
def test_fact_check(mock_post):
    statements = ["Statement 1"]
    original_article_title = "Fake News Example"
    original_article_url = "https://example.com/fake-news"  # ADD THIS

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": json.dumps([{
                    "statement": "Statement 1",
                    "correctness": "factual",
                    "explanation": "This statement is factual according to [1]."
                }])
            }
        }],
        "citations": [
            "https://other-source.com/article",  # Different source
            "https://example.com/fake-news"      # Original (will be filtered)
        ]
    }
    mock_post.return_value = mock_response

    # UPDATE THIS LINE - now requires 3 parameters
    result = asyncio.run(fact_check(statements, original_article_title, original_article_url))
    
    print("Mocked API Response:", result)
    
    # Verify the original article URL was filtered out
    assert len(result) == 1
    assert result[0]["statement"] == "Statement 1"
    assert "https://other-source.com/article" in result[0]["citations"]
    assert "https://example.com/fake-news" not in result[0]["citations"]  # Filtered!
    
    mock_post.assert_called_once_with(
        Config.PERPLEXITY_URL, headers=Config.HEADERS, json=ANY
    )


def test_api_health_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_health_factcheck():
    response = client.get("/factcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("app.main.getStatement", new_callable=AsyncMock)
def test_api_predict_statements(mock_get_statements):
    mock_get_statements.return_value = ["s1", "s2"]
    response = client.post(
        "/factcheck/predict/statements",
        json={"content": "article content", "title": "title", "url": "https://example.com"},
    )
    assert response.status_code == 200
    assert response.json() == {"response": ["s1", "s2"]}


@patch("app.main.summarise", new_callable=AsyncMock)
def test_api_summarise(mock_summarise):
    mock_summarise.return_value = "summary text"
    response = client.post("/factcheck/summarise", json={"content": "abc"})
    assert response.status_code == 200
    assert response.json() == {"response": "summary text"}


@patch("app.main.summarise_data", new_callable=AsyncMock)
def test_api_summarise_model_data(mock_summarise_data):
    mock_summarise_data.return_value = '{"sentiment_summary":"ok"}'
    response = client.post(
        "/factcheck/summarise/model-data",
        json={
            "sentiment_result": {},
            "emotion_result": {},
            "propaganda_result": {},
            "political_bias_result": {},
            "summarise_result": "",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"response": {"sentiment_summary": "ok"}}


@patch("app.main.getStatement", new_callable=AsyncMock)
@patch("app.main.fact_check", new_callable=AsyncMock)
def test_api_predict_fact_check(mock_fact_check, mock_get_statements):
    mock_get_statements.return_value = ["claim"]
    mock_fact_check.return_value = [{"statement": "claim", "correctness": "factual", "explanation": "ok", "citations": []}]
    response = client.post(
        "/factcheck/predict/fact-check",
        json={"content": "article", "title": "title", "url": "https://example.com"},
    )
    assert response.status_code == 200
    assert isinstance(response.json()["response"], list)


@patch("app.main.fact_check", new_callable=AsyncMock)
def test_api_claim_short_input_returns_400(mock_fact_check):
    response = client.post("/factcheck/claim", json={"claim": "short", "page_title": "t", "page_url": "u"})
    assert response.status_code == 400


@patch("app.main.fact_check", new_callable=AsyncMock)
def test_api_claim_success(mock_fact_check):
    mock_fact_check.return_value = [{
        "statement": "This is a long enough claim",
        "correctness": "factual",
        "explanation": "checked",
        "citations": ["https://source.com"],
    }]
    response = client.post(
        "/factcheck/claim",
        json={"claim": "This is a long enough claim", "page_title": "t", "page_url": "https://x.com"},
    )
    assert response.status_code == 200
    body = response.json()["response"]
    assert body["correctness"] == "factual"