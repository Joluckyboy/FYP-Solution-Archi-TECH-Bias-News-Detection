import mongoengine

from db_collections import NewsData
import vars as vars

import json

sample_news_data = {
    "url": "https://example.com/database1",
    "title": "Sample News Title",
    "content": "This is the content of the sample news article.",
    "sentiment_result": {"positive": 0.8, "negative": 0.1, "neutral": 0.1},
    "emotion_result": {"joy": 0.7, "sadness": 0.2, "anger": 0.1},
    "propaganda_result": {"propaganda": False}
}

# Connect to the MongoDB database
mongoengine.connect(
    db="app",  # Replace with your database name
    host=vars.mongo_server
)

def get_news_collection():
    return mongoengine.get_db()["news_data"]

# Create
def create_document(data):
    # Create a new document
    news = NewsData(**data)
    news.save()
    return str(news.id)

## check if ID exists
def check_id_exists(id):
    news = NewsData.objects(id=id).first()
    if news:
        return True
    return False

## check if url exists
def check_url_exists(url):
    news = NewsData.objects(url=url).first()
    if news:
        return True
    return False

# Read
def read_all_documents():
    # Read all documents
    news = NewsData.objects
    return news

def read_documents(filter_data):
    # Read documents
    news = NewsData.objects(**filter_data)
    # news = [news_item.to_mongo().to_dict() for news_item in news]
    try:
        news = [json.loads(news_item.to_json()) for news_item in news]
        return news
    except:
        return None

def read_document_by_id(id):
    # Read a document by ID
    news = NewsData.objects(id=id).first()
    try:
        news = json.loads(news.to_json())
        return news
    except: 
        return None
    
async def stream_document_by_id(id):
    """Stream MongoDB changes for a specific news_id."""
    collection = get_news_collection()
    pipeline = [{"$match": {"documentKey._id": id}}]  # Filter by news_id

    async with collection.watch(pipeline) as stream:
        async for change in stream:
            yield f"data: {json.dumps(change['fullDocument'])}\n\n"

def read_document_by_url(url):
    # Read a document by URL
    news = NewsData.objects(url=url).first()

    try:
        news = json.loads(news.to_json())
        return news
    except:
        return None

# Update
def update_documents(filter_data, update_data):
    # Update documents
    news = NewsData.objects(**filter_data)  
    modified_count = news.update(**update_data)
    return modified_count

def update_sentiment_result(id, sentiment_result):
    # Update the sentiment result of a document
    news = NewsData.objects(id=id).first()
    news.sentiment_result = sentiment_result
    news.save()

def update_emotion_result(id, emotion_result):
    # Update the emotion result of a document
    news = NewsData.objects(id=id).first()
    news.emotion_result = emotion_result
    news.save()

def update_propaganda_result(id, propaganda_result):
    # Update the propaganda result of a document
    news = NewsData.objects(id=id).first()
    news.propaganda_result = propaganda_result
    news.save()

def update_sentiment_by_url(url, update_data):
    # Update the sentiment result of a document by URL
    news = NewsData.objects(url=url).first()
    news.sentiment_result = update_data
    news.save()

def update_emotion_by_url(url, update_data):
    # Update the emotion result of a document by URL
    news = NewsData.objects(url=url).first()
    news.emotion_result = update_data
    news.save()

def update_propaganda_by_url(url, update_data):
    # Update the propaganda result of a document by URL
    news = NewsData.objects(url=url).first()
    news.propaganda_result = update_data
    news.save()

def update_factcheck_by_url(url, update_data):
    news = NewsData.objects(url=url).first()
    news.factcheck_result = update_data
    news.save()
    
def update_summary_by_url(url, update_data):
    news = NewsData.objects(url=url).first()
    news.summarise_result = update_data
    news.save()

def update_model_data_summary_by_url(url, update_data):
    news = NewsData.objects(url=url).first()
    news.data_summary = update_data
    news.save()

# Delete
def delete_documents(filter_data):
    # Delete documents
    news = NewsData.objects(**filter_data)
    deleted_count = news.delete()
    return deleted_count

def delete_document_by_id(id):
    # Delete a document by ID
    news = NewsData.objects(id=id).first()
    deleted_count = news.delete()
    return deleted_count

