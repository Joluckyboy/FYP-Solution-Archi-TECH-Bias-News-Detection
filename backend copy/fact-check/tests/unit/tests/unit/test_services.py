import pytest
import json
import re
from unittest.mock import patch, AsyncMock, MagicMock, ANY

from service.predict_service import processStatement, summarise, summarise_data, getStatement, fact_check
from models.datapayload import DataPayload, ModelDataPayload
from config.config import Config

pytestmark = pytest.mark.asyncio  # Ensures pytest handles async functions

@pytest.mark.parametrize("content, expected", [
    ('```json[{"statement": "Fact 1"}, {"statement": "Fact 2"}]```', ["Fact 1", "Fact 2"]),
    ('[{"statement": "Only Fact"}]', ["Only Fact"]),
    ('```json[{"statement": "Test"}]```', ["Test"]),
])
def test_processStatement(content, expected):
    assert processStatement(content) == expected

@patch("requests.post")
async def test_summarise(mock_post):
    mock_response = {
        "choices": [{"message": {"content": "<think>irrelevant</think> Summary result"}}]
    }
    mock_post.return_value.json.return_value = mock_response

    text = "This is a long article that needs summarization."
    result = await summarise(text)

    assert result == "Summary result"
    mock_post.assert_called_once_with(Config.DEEPSEEK_URL, headers=Config.HEADERS_DS, json=ANY)

@patch("requests.post")
async def test_summarise_data(mock_post):
    json_payload = ModelDataPayload(
        sentiment_result={"Positive": 0.9},
        emotion_result={"Happy": 0.8},
        propaganda_result={"None": 0.95},
        summarise_result="This is the summary."
    )

    mock_response = {
        "choices": [{"message": {"content": "<think>ignore</think> {\"sentiment_summary\": \"Positive\", \"emotion_summary\": \"Happy\", \"propaganda_summary\": \"None\"}"}}]
    }
    mock_post.return_value.json.return_value = mock_response

    result = await summarise_data(json_payload)

    assert result == '{"sentiment_summary": "Positive", "emotion_summary": "Happy", "propaganda_summary": "None"}'
    mock_post.assert_called_once_with(Config.DEEPSEEK_URL, headers=Config.HEADERS_DS, json=ANY)

@patch("requests.post")
async def test_getStatement(mock_post):
    json_payload = DataPayload(content="This is a test article.", title="Test Title")

    mock_response = {
        "choices": [{"message": {"content": "```json[{\"statement\": \"Test statement 1\"}, {\"statement\": \"Test statement 2\"}]```"}}]
    }
    mock_post.return_value.json.return_value = mock_response

    result = await getStatement(json_payload)

    assert result == ["Test statement 1", "Test statement 2"]
    mock_post.assert_called_once_with(
        Config.PERPLEXITY_URL if Config.MODEL == "sonar" else Config.DEEPSEEK_URL,
        headers=Config.HEADERS if Config.MODEL == "sonar" else Config.HEADERS_DS,
        json=ANY
    )

@patch("requests.post")
async def test_fact_check(mock_post):
    statements = ["Statement 1"]
    original_article = "Fake News Example"

    mock_response = {
        "choices": [{
            "message": {
                "content": json.dumps([{
                    "statement": "Statement 1",
                    "correctness": "factual",
                    "explanation": "This statement is factual."
                }])
            }
        }],
        "citations": [{"source": "straitstimes.com"}]
    }
    mock_post.return_value.json.return_value = mock_response

    result = await fact_check(statements, original_article)
    print("Mocked API Response:", result)
    mock_post.assert_called_once_with(
        Config.PERPLEXITY_URL, headers=Config.HEADERS, json=ANY
    )
