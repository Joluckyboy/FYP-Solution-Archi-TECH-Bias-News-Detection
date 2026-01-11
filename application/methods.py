import vars as vars
from typing import Dict, List, Any

import requests
from flask import abort 

import pprint
import logging

from typing import List, Dict, Any

logger = logging.getLogger(__name__)

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
        sanitized_item = {
            "statement": item.get("statement", ""),
            "correctness": item.get("accuracy", "").lower(),  # Map 'accuracy' to 'correctness'
            "explanation": item.get("explanation", ""),
            "citations": item.get("citations", [])
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

def get_sentiment (text, url, title: str):
    try:
        query_url = vars.sentiment_url + "/sentiment/analyze_sentiment"
        data = {"text": text}

        response = requests.post(query_url, json=data, timeout=30)
        sentiment = response.json()

        # save to db
        db_url = vars.database_url + "/database/sentiment/"
        data = {"url": url, "sentiment_result": sentiment["sentiment_result"]}

        response = requests.put(db_url, json=data, timeout=30)

        return sentiment
    except Exception as e:
        logger.error(f"[app] Sentiment service error: {e}")
        return {}

def get_emotion (text, url, title: str):
    try:
        query_url = vars.emotion_url + "/emotion/analyze_emotion"
        data = {"text": text}

        response = requests.post(query_url, json=data, timeout=30)
        emotion = response.json()

        # save to db
        db_url = vars.database_url + "/database/emotion/"
        data = {"url": url, "emotion_result": emotion["emotion_result"]}
        response = requests.put(db_url, json=data, timeout=30)

        return emotion
    except Exception as e:
        logger.error(f"[app] Emotion service error: {e}")
        return {}

def get_propaganda (text, url, title: str):
    try:
        query_url = vars.propaganda_url + "/propaganda/analyze_propaganda"
        data = {"text": text}

        response = requests.post(query_url, json=data, timeout=30)
        propaganda = response.json()

        # save to db
        db_url = vars.database_url + "/database/propaganda/"
        data = {"url": url, "propaganda_result": propaganda["propaganda_result"]}
        response = requests.put(db_url, json=data, timeout=30)

        return propaganda
    except Exception as e:
        logger.error(f"[app] Propaganda service error: {e}")
        return {}

def get_fact_check(article_content: str, url: str, title: str ):
    query_url = vars.factcheck_url + "/factcheck/predict/fact-check"
    payload = {
        "title": title, 
        "content": article_content
    }
    
    try:
        response = requests.post(query_url, json=payload)
        response_json = response.json()
        
        # Check if response contains the expected data
        if "response" not in response_json:
            # Return empty list if API keys are not configured
            print(f"[app] Fact-check service error: {response_json}")
            return []
            
        data = response_json["response"]
        sanitized_data = sanitize_factcheck_data(data)
    except Exception as e:
        print(f"[app] Error calling fact-check service: {e}")
        return []

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
            return ""
            
        data = response_json["response"]
    except Exception as e:
        print(f"[app] Error calling summarise service: {e}")
        return ""
    
    db_url = vars.database_url + "/database/summarise/"
    db_payload = {"url": url, "summarise_result": data}
    
    try:
        response = requests.put(db_url, json=db_payload)
    except Exception as e:
        print(f"[app] Error saving summarise to database: {e}")
    
    return data

def get_data_summary(text, url, title: str):
    data = get_news(url)

    query_url = vars.factcheck_url + "/factcheck/summarise/model-data"
    payload = {
        "sentiment_result": data["sentiment_result"],
        "emotion_result": data["emotion_result"],
        "propaganda_result": data["propaganda_result"],
        "summarise_result": data["summarise_result"]
    }

    try:
        response = requests.post(query_url, json=payload)
        response_json = response.json()
        
        # Check if response contains the expected data
        if "response" not in response_json:
            # Return empty string if API keys are not configured
            print(f"[app] Data summary service error: {response_json}")
            return ""
            
        data = response_json["response"]
    except Exception as e:
        print(f"[app] Error calling data summary service: {e}")
        return ""

    db_url = vars.database_url + "/database/ModelDataSummary/"
    db_payload = {"url": url, "data_summary": data}

    try:
        response = requests.put(db_url, json=db_payload)
    except Exception as e:
        print(f"[app] Error saving data summary to database: {e}")

    return data

def get_latest_urls(max_num: int) -> Dict:
    query_url = vars.scraper_url + "/scraper/get-latest-articles"
    payload = {
        "num_articles": max_num
    }
    
    response = requests.get(query_url, payload)
    deserialised_response = response.json()
    
    return deserialised_response

def get_all_quiz(question_type: str = None) :
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