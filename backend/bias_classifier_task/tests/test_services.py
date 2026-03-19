import os
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

os.environ.setdefault("S3_BUCKET", "test-bucket")

BIAS_TASK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BIAS_TASK_DIR not in sys.path:
    sys.path.insert(0, BIAS_TASK_DIR)

import classify_task



def test_classify_article_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"rating": "leaning_right"}

    with patch("classify_task.requests.get", return_value=mock_response):
        article = {"source": "CNA", "title": "T", "summary": "S"}
        label = classify_task.classify_article(article)
        assert label == "leaning-right"


def test_classify_article_invalid_returns_empty():
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("classify_task.requests.get", return_value=mock_response):
        label = classify_task.classify_article({"source": "CNA", "title": "T", "summary": "S"})
        assert label == ""


def test_classify_all_only_missing_bias():
    articles = [
        {"title": "A", "political_bias": "center", "source": "CNA", "summary": "s"},
        {"title": "B", "political_bias": "", "source": "CNA", "summary": "s"},
    ]

    with patch("classify_task.classify_article", return_value="left"):
        updated = classify_task.classify_all(articles)

    assert updated[0]["political_bias"] == "center"
    assert updated[1]["political_bias"] == "left"


def test_remove_old_articles_filters_by_date():
    articles = [
        {"title": "A", "published_at": "01/01/2020"},
        {"title": "B", "published_at": "2099-01-01"},
        {"title": "C", "published_at": ""},
    ]

    kept = classify_task.remove_old_articles(articles)
    titles = {a["title"] for a in kept}
    assert "A" not in titles
    assert "B" in titles
    assert "C" in titles


def test_upload_csv_writes_expected_headers():
    s3 = MagicMock()
    articles = [{
        "title": "T",
        "source": "S",
        "url": "U",
        "published_at": "2026-03-19",
        "summary": "sum",
        "image_url": "img",
        "country": "SG",
        "topic": "Politics",
        "political_bias": "center",
    }]

    classify_task.upload_csv(s3, articles)

    assert s3.put_object.called
    kwargs = s3.put_object.call_args.kwargs
    body = kwargs["Body"].decode("utf-8")
    assert "title,source,url,published_at,summary,image_url,country,topic,political_bias" in body
    assert "T,S,U,2026-03-19,sum,img,SG,Politics,center" in body


def test_trigger_clustering_calls_analyzer():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"clusters": 2, "articles": 10}

    with patch("classify_task.requests.post", return_value=mock_response) as mock_post:
        classify_task.trigger_clustering()
        assert mock_post.called
