import os
import sys
from unittest.mock import patch

from fastapi.testclient import TestClient

POLITICAL_BIAS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if POLITICAL_BIAS_DIR not in sys.path:
    sys.path.insert(0, POLITICAL_BIAS_DIR)

import main



def _client():
    fake_state = {
        "device": "cpu",
        "model": object(),
        "tokenizer": object(),
        "pkey": "fake-key",
    }
    with patch.object(main, "get_model", return_value=fake_state):
        with TestClient(main.app) as client:
            yield client


def test_health_root():
    client = next(_client())
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_service():
    client = next(_client())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "political_bias"


def test_biasengine_hello():
    client = next(_client())
    response = client.get("/biasengine/hello")
    assert response.status_code == 200
    assert response.json() == "Hello"


def test_rate_bias_missing_fields():
    client = next(_client())
    response = client.get("/biasengine/rate_bias")
    assert response.status_code == 400


@patch("app.blueprints.biasengine._run_bert", return_value=[[0.1, 0.2, 0.5, 0.1, 0.1]])
def test_rate_bias_get(mock_bert):
    client = next(_client())
    response = client.get(
        "/biasengine/rate_bias_no_perplexity",
        params={"site": "cna", "title": "t", "page_text": "p"},
    )
    assert response.status_code == 200
    assert response.json()["rating"] == "center"


@patch("app.blueprints.biasengine._run_bert", return_value=[[0.9, 0.0, 0.0, 0.0, 0.0]])
def test_rate_bias_post(mock_bert):
    client = next(_client())
    response = client.post(
        "/biasengine/rate_bias_no_perplexity",
        json={"site": "cna", "title": "t", "page_text": "p"},
    )
    assert response.status_code == 200
    assert response.json()["rating"] == "left"


@patch("app.blueprints.biasengine._run_bert", side_effect=RuntimeError("boom"))
def test_rate_bias_error_path(mock_bert):
    client = next(_client())
    response = client.post(
        "/biasengine/rate_bias_no_perplexity",
        json={"site": "cna", "title": "t", "page_text": "p"},
    )
    assert response.status_code == 500


def test_get_topics_missing_fields():
    client = next(_client())
    response = client.get("/biasengine/get_topics")
    assert response.status_code == 400


def test_get_topics_no_api_key():
    fake_state = {
        "device": "cpu",
        "model": object(),
        "tokenizer": object(),
        "pkey": None,
    }
    with patch.dict(os.environ, {"API_KEY": "", "KEY": ""}, clear=False), patch.object(main, "get_model", return_value=fake_state):
        with TestClient(main.app) as client:
            response = client.post(
                "/biasengine/get_topics",
                json={"site": "cna", "title": "t", "page_text": "p"},
            )
            assert response.status_code == 500
