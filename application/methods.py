import vars as vars
from typing import Dict, List, Any
from urllib.parse import urlparse
import re

import requests  # type: ignore
from flask import abort

import pprint
import logging

from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# ── Sampling configuration ────────────────────────────────────────────────────
# Articles under this character count are sent as-is (no sampling needed).
# 8000 chars ≈ 1200-1500 words ≈ a full standard news article.
# Most news articles are under this limit, so sampling rarely triggers.
SAMPLE_MAX_CHARS = 8000


def _sample_text(text: str, max_chars: int = SAMPLE_MAX_CHARS) -> str:
    """
    Sample representative sentences from a long article.

    If article is short enough (≤ max_chars), return it unchanged.
    Otherwise, take sentences from 3 zones:
      - Beginning (40%): intro, headline claims, key facts
      - Middle (30%): quotes, reactions, supporting details
      - End (30%): context, consequences, conclusions

    Args:
        text: Full article text
        max_chars: Character limit above which sampling activates

    Returns:
        Original text if short enough, otherwise sampled text
    """
    if len(text) <= max_chars:
        return text  # Short article — no sampling needed, return as-is

    # Split into sentences
    sentences = [
        s.strip()
        for s in re.split(r'(?<=[.!?])\s+', text)
        if s.strip()
    ]

    if not sentences:
        # No sentence boundaries found — fall back to character truncation
        return text[:max_chars]

    n = len(sentences)

    # Define the 3 zones
    begin  = sentences[:int(n * 0.40)]           # First 40%
    middle = sentences[int(n * 0.35):int(n * 0.65)]  # Middle 30% (35%→65%)
    end    = sentences[int(n * 0.70):]           # Last 30%

    # Combine zones
    sampled_sentences = begin + middle + end
    result = ' '.join(sampled_sentences)

    # Final safety check: if still over limit (many short sentences that
    # add up), truncate at the last sentence boundary
    if len(result) > max_chars:
        truncated = result[:max_chars]
        last_period = truncated.rfind('.')
        if last_period > max_chars * 0.8:  # Only use if period is near the end
            result = truncated[:last_period + 1]
        else:
            result = truncated

    return result

def sanitize_factcheck_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sanitizes the fact-check data to ensure it conforms to the FactCheckItem model.

    Args:
        data (List[Dict[str, Any]]): The raw fact-check data.

    Returns:
        List[Dict[str, Any]]: The sanitized fact-check data.
    """
    sanitized_data = []
    for item in data:
        # Prefer new "correctness" field but keep backward compatibility with legacy "accuracy".
        raw_correctness = (item.get("correctness") or item.get("accuracy") or "").lower()
        if raw_correctness not in {"factual", "unfactual", "cannot be determined"}:
            raw_correctness = "cannot be determined"

        raw_citations = item.get("citations") or []
        if isinstance(raw_citations, str):
            raw_citations = [raw_citations]
        elif not isinstance(raw_citations, list):
            raw_citations = []

        sanitized_item = {
            "statement": item.get("statement", ""),
            "correctness": raw_correctness,
            "explanation": item.get("explanation", ""),
            "citations": raw_citations,
        }
        # Ensure all required fields are present and valid
        if isinstance(sanitized_item["statement"], str) and \
           isinstance(sanitized_item["correctness"], str) and \
           isinstance(sanitized_item["explanation"], str) and \
           isinstance(sanitized_item["citations"], list):
            sanitized_data.append(sanitized_item)
    return sanitized_data

# Scraper calls
def extract_news(url):
    query_url = vars.scraper_url + "/scraper/get-article"
    params = {"url": url}

    response = requests.get(query_url, params=params)

    if response.status_code == 400:
        abort(400, description="Invalid URL format")

    text = response.json()
    return text

# Database calls
def check_exists (url):
    
    query_url = vars.database_url + "/database/check_exists/"
    data = {"url": url}

    response = requests.post(query_url, json=data)
    exists = response.json()
    return exists

def get_news (url):
    # get completed news data from the database
    query_url = vars.database_url + "/database/getByURL/"
    data = {"url": url}

    response = requests.post(query_url, json=data)
    news = response.json()
    
    if '_id' in news and '$oid' in news['_id']:
        news['id'] = news['_id']['$oid']
        del news['_id']

    return news

def get_news_by_id (news_id):
    query_url = vars.database_url + "/database/getByID/" + news_id

    response = requests.get(query_url)
    news = response.json()

    if '_id' in news and '$oid' in news['_id']:
        news['id'] = news['_id']['$oid']
        del news['_id']

    return news

def create_news (url, title, content):
    
    query_url = vars.database_url + "/database/"
    data = {"url": url, "title": title, "content": content}

    response = requests.post(query_url, json=data)
    news = response.json()
    # print(response.json())

    # if '_id' in news and '$oid' in news['_id']:
    #     news['id'] = news['_id']['$oid']
    #     del news['_id']

    return news

def get_sentiment(text, url, title: str):
    try:
        query_url = vars.sentiment_url + "/sentiment/analyze_sentiment"
        logger.info(f"[sentiment] Starting analysis for {url}")

        # CHANGED: sample text before sending (only triggers for long articles)
        sampled = _sample_text(text)
        if len(sampled) < len(text):
            logger.info(f"[sentiment] Sampled {len(sampled)}/{len(text)} chars for {url}")

        response = requests.post(
            query_url,
            json={"text": sampled},
            timeout=180
        )
        logger.info(f"[sentiment] Service responded with status {response.status_code} for {url}")
        sentiment = response.json()

        # save to db
        db_url = vars.database_url + "/database/sentiment/"
        data = {
            "url": url,
            "sentiment_result": {
                **sentiment.get("sentiment_result", {}),
                "sentence_sentiments": sentiment.get("sentence_sentiments", [])
            }
        }
        requests.put(db_url, json=data, timeout=60)
        return sentiment

    except Exception as e:
        logger.error(f"[app] Sentiment service error: {e}")
        return {}


def get_emotion(text, url, title: str):
    try:
        query_url = vars.emotion_url + "/emotion/analyze_emotion"

        # ✅ CHANGED: sample text before sending
        sampled = _sample_text(text)
        if len(sampled) < len(text):
            logger.info(f"[emotion] Sampled {len(sampled)}/{len(text)} chars for {url}")

        response = requests.post(
            query_url,
            json={"text": sampled},
            timeout=120  # ✅ CHANGED: increased from 30s to 120s
        )
        emotion = response.json()

        # save to db
        db_url = vars.database_url + "/database/emotion/"
        data = {"url": url, "emotion_result": emotion["emotion_result"]}
        requests.put(db_url, json=data, timeout=30)
        return emotion

    except Exception as e:
        logger.error(f"[app] Emotion service error: {e}")
        return {}

def get_propaganda (text, url, title: str):
    try:
        query_url = vars.propaganda_url + "/propaganda/analyze_propaganda"
        data = {"text": text}

        response = requests.post(query_url, json=data, timeout=120)
        propaganda = response.json()

        # save to db
        db_url = vars.database_url + "/database/propaganda/"
        data = {"url": url, "propaganda_result": propaganda["propaganda_result"]}
        response = requests.put(db_url, json=data, timeout=120)

        return propaganda
    except Exception as e:
        logger.error(f"[app] Propaganda service error: {e}")
        return {}

def get_political_bias(text, url, title: str):
    try:
        # Extract site domain from URL
        site = urlparse(url).netloc.replace("www.", "")
        sampled = _sample_text(text)

        payload = {"site": site, "title": title, "page_text": sampled}

        # 1. Get bias rating (no Perplexity dependency — fast)
        logger.info(f"[political_bias] Starting bias rating for {url}")
        rating_response = requests.post(
            vars.bias_url + "/biasengine/rate_bias_no_perplexity",
            json=payload,
            timeout=30
        )
        rating_data = rating_response.json()
        rating = rating_data.get("rating", "center") if rating_data.get("status") == 200 else "center"

        # 2. Get topics covered/omitted (uses Perplexity, gracefully falls back)
        logger.info(f"[political_bias] Starting topics analysis for {url}")
        try:
            topics_response = requests.post(
                vars.bias_url + "/biasengine/get_topics",
                json=payload,
                timeout=30
            )
            topics_data = topics_response.json()
            topics = topics_data.get("topics", {"covered": [], "omitted": []}) if topics_data.get("status") == 200 else {"covered": [], "omitted": []}
        except Exception as e:
            logger.warning(f"[political_bias] Topics analysis failed (non-critical): {e}")
            topics = {"covered": [], "omitted": []}

        # Combine into single result
        political_bias_result = {
            "rating": rating,
            "topics": topics
        }

        # Save to DB
        db_url = vars.database_url + "/database/political_bias/"
        db_payload = {"url": url, "political_bias_result": political_bias_result}
        requests.put(db_url, json=db_payload, timeout=30)

        logger.info(f"[political_bias] Completed for {url}: rating={rating}")
        return political_bias_result

    except Exception as e:
        logger.error(f"[app] Political bias service error: {e}")
        return {}


def get_fact_check(article_content: str, url: str, title: str ):
    query_url = vars.factcheck_url + "/factcheck/predict/fact-check"
    payload = {
        "title": title, 
        "content": article_content,
        "url": url
    }
    
    try:
        response = requests.post(query_url, json=payload)
        response_json = response.json()
        
        # Check if response contains the expected data
        if "response" not in response_json:
            print(f"[app] Fact-check service error: {response_json}")
            sanitized_data = []
        else:
            data = response_json["response"]
            sanitized_data = sanitize_factcheck_data(data)
    except Exception as e:
        print(f"[app] Error calling fact-check service: {e}")
        sanitized_data = []

    # print ("[app] Fact check response: ", sanitized_data)

    db_url = vars.database_url + "/database/factcheck/"
    db_payload = {"url": url, "factcheck_result": sanitized_data}
    
    # save to db
    try:
        response = requests.put(db_url, json=db_payload)
    except Exception as e:
        print(f"[app] Error saving fact-check to database: {e}")

    return sanitized_data
    
def get_summarise(article_content: str, url: str, title: str) -> Dict:
    query_url = vars.factcheck_url + "/factcheck/summarise"
    payload = {
        "content": article_content
    }
    
    try:
        response = requests.post(query_url, json=payload)
        response_json = response.json()
        
        # Check if response contains the expected data
        if "response" not in response_json:
            # Return empty string if API keys are not configured
            print(f"[app] Summarise service error: {response_json}")
            return {}
            
        data = response_json["response"]
    except Exception as e:
        print(f"[app] Error calling summarise service: {e}")
        return {}
    
    db_url = vars.database_url + "/database/summarise/"
    db_payload = {"url": url, "summarise_result": data}
    
    try:
        response = requests.put(db_url, json=db_payload)
    except Exception as e:
        print(f"[app] Error saving summarise to database: {e}")
    
    return data

def get_data_summary(
    text,
    url,
    title: str,
    trigger: str = "manual",
    sentiment=None,
    emotion=None,
    propaganda=None,
    summarise=None,
    allow_partial_local: bool = False,
):
    """
    Generate and save data summaries for all analysis types.
    
    Now accepts analysis results as parameters to avoid database timing issues.
    If not provided, fetches from database as fallback.
    """
    # If results are not provided, fetch from database
    if sentiment is None or emotion is None or propaganda is None:
        news_data = get_news(url) or {}
        sentiment = sentiment or news_data.get("sentiment_result") or {}
        emotion = emotion or news_data.get("emotion_result") or {}
        propaganda = propaganda or news_data.get("propaganda_result") or {}
        summarise = summarise or news_data.get("summarise_result") or ""
    else:
        summarise = summarise or ""

    has_sentiment = bool(sentiment)
    has_emotion = bool(emotion)
    has_propaganda = bool(propaganda)
    # Required for model-data summary generation:
    # sentiment + emotion + propaganda (fact-check is intentionally excluded).
    has_required_inputs = all([has_sentiment, has_emotion, has_propaganda])

    if not has_required_inputs:
        print(f"[app] Skipping data summary ({trigger}) due to incomplete required analyses")
        return {}

    query_url = vars.factcheck_url + "/factcheck/summarise/model-data"
    payload = {
        "sentiment_result": sentiment,
        "emotion_result": emotion,
        "propaganda_result": propaganda,
        "summarise_result": summarise,
    }

    try:
        response = requests.post(query_url, json=payload)
        response_json = response.json()

        if "response" not in response_json:
            print(f"[app] Data summary service error ({trigger}): {response_json}")
            return {}

        new_summary = response_json["response"]
        if not isinstance(new_summary, dict):
            print(f"[app] Data summary malformed response ({trigger}): {new_summary}")
            return {}
    except Exception as e:
        print(f"[app] Error calling data summary service ({trigger}): {e}")
        return {}

    summary_fields = {"sentiment_summary", "emotion_summary", "propaganda_summary"}
    merged_summary = {key: value for key, value in new_summary.items() if key in summary_fields}

    db_url = vars.database_url + "/database/ModelDataSummary/"
    db_payload = {"url": url, "data_summary": merged_summary}

    try:
        requests.put(db_url, json=db_payload)
        print(f"[app] Saved data summary for {url} ({trigger}): {list(merged_summary.keys())}")
    except Exception as e:
        print(f"[app] Error saving data summary to database ({trigger}): {e}")

    return merged_summary

def get_latest_urls(max_num: int) -> Dict:
    query_url = vars.scraper_url + "/scraper/get-latest-articles"
    payload = {
        "num_articles": max_num
    }
    
    response = requests.get(query_url, payload)
    deserialised_response = response.json()
    
    return deserialised_response

def get_all_quiz(question_type: str | None = None):
    query_url = vars.database_url + "/database/quiz/getAll"
    payload = {
        "question_type": question_type
    }
    
    response = requests.get(query_url, payload)
    deserialised_response = response.json()
    
    return deserialised_response

def get_quiz(number, question_type):
    query_url = vars.database_url + "/database/quiz/getRandom"
    payload = {
        "number": number,
        "question_type": question_type
    }

    response = requests.get(query_url, payload)
    deserialised_response = response.json()

    return deserialised_response


# ── Digest Subscriptions ─────────────────────────────────────────────────────

def subscribe_digest(telegram_user_id: int, chat_id: int):
    query_url = vars.database_url + "/database/subscriptions/"
    data = {"telegram_user_id": telegram_user_id, "chat_id": chat_id}
    response = requests.post(query_url, json=data, timeout=10)
    return response.json()


def unsubscribe_digest(telegram_user_id: int):
    query_url = vars.database_url + f"/database/subscriptions/{telegram_user_id}"
    response = requests.delete(query_url, timeout=10)
    return response.json()


def get_active_subscriptions():
    query_url = vars.database_url + "/database/subscriptions/active"
    response = requests.get(query_url, timeout=10)
    return response.json().get("subscriptions", [])


def get_recent_biased_articles(hours: int = 24):
    query_url = vars.database_url + "/database/articles/recent-biased"
    params = {"hours": hours}
    response = requests.get(query_url, params=params, timeout=15)
    return response.json().get("articles", [])