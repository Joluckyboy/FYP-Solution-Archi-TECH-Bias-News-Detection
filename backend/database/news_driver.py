from supabase_client import get_supabase_client
import json

sample_news_data = {
    "url": "https://example.com/database1",
    "title": "Sample News Title",
    "content": "This is the content of the sample news article.",
    "sentiment_result": {"positive": 0.8, "negative": 0.1, "neutral": 0.1},
    "emotion_result": {"joy": 0.7, "sadness": 0.2, "anger": 0.1},
    "propaganda_result": {"propaganda": False}
}

# Get Supabase client
supabase = get_supabase_client()

# Create
def create_document(data):
    """Create a new news document in Supabase."""
    try:
        result = supabase.table("news_data").insert(data).execute()
        if result.data:
            return str(result.data[0]["id"])
        return None
    except Exception as e:
        print(f"Error creating document: {e}")
        return None

# check if ID exists
def check_id_exists(id):
    """Check if a news document with the given ID exists."""
    try:
        result = supabase.table("news_data").select(
            "id").eq("id", id).execute()
        return len(result.data) > 0
    except Exception as e:
        print(f"Error checking ID exists: {e}")
        return False

# check if url exists
def check_url_exists(url):
    """Check if a news document with the given URL exists."""
    try:
        result = supabase.table("news_data").select(
            "id").eq("url", url).execute()
        return len(result.data) > 0
    except Exception as e:
        print(f"Error checking URL exists: {e}")
        return False

# Read
def read_all_documents():
    """Read all news documents."""
    try:
        result = supabase.table("news_data").select("*").execute()
        return result.data
    except Exception as e:
        print(f"Error reading all documents: {e}")
        return []


def read_documents(filter_data):
    """Read news documents with filters."""
    try:
        query = supabase.table("news_data").select("*")

        # Apply filters dynamically
        for key, value in filter_data.items():
            query = query.eq(key, value)

        result = query.execute()
        return result.data
    except Exception as e:
        print(f"Error reading documents: {e}")
        return None


def read_document_by_id(id):
    """Read a news document by ID."""
    try:
        result = supabase.table("news_data").select("*").eq("id", id).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Error reading document by ID: {e}")
        return None


async def stream_document_by_id(id):
    """Stream news data changes for a specific news_id."""
    # Note: Supabase Realtime requires additional setup
    # For now, we'll implement a basic polling approach
    # You may need to enable Realtime in Supabase dashboard for proper streaming

    try:
        channel = supabase.channel(f'news-{id}')

        def handle_changes(payload):
            yield f"data: {json.dumps(payload['new'])}\n\n"

        channel.on_postgres_changes(
            event='UPDATE',
            schema='public',
            table='news_data',
            filter=f'id=eq.{id}',
            callback=handle_changes
        ).subscribe()

    except Exception as e:
        print(f"Error streaming document: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


def read_document_by_url(url):
    """Read a news document by URL."""
    try:
        result = supabase.table("news_data").select(
            "*").eq("url", url).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Error reading document by URL: {e}")
        return None

# Update
def update_documents(filter_data, update_data):
    """Update news documents matching filters."""
    try:
        query = supabase.table("news_data").update(update_data)

        # Apply filters
        for key, value in filter_data.items():
            query = query.eq(key, value)

        result = query.execute()
        return len(result.data) if result.data else 0
    except Exception as e:
        print(f"Error updating documents: {e}")
        return 0


def update_sentiment_result(id, sentiment_result):
    """Update the sentiment result of a document."""
    try:
        supabase.table("news_data").update({
            "sentiment_result": sentiment_result
        }).eq("id", id).execute()
    except Exception as e:
        print(f"Error updating sentiment result: {e}")


def update_emotion_result(id, emotion_result):
    """Update the emotion result of a document."""
    try:
        supabase.table("news_data").update({
            "emotion_result": emotion_result
        }).eq("id", id).execute()
    except Exception as e:
        print(f"Error updating emotion result: {e}")


def update_propaganda_result(id, propaganda_result):
    """Update the propaganda result of a document."""
    try:
        supabase.table("news_data").update({
            "propaganda_result": propaganda_result
        }).eq("id", id).execute()
    except Exception as e:
        print(f"Error updating propaganda result: {e}")


def update_sentiment_by_url(url, update_data):
    """Update the sentiment result of a document by URL."""
    try:
        supabase.table("news_data").update({
            "sentiment_result": update_data
        }).eq("url", url).execute()
    except Exception as e:
        print(f"Error updating sentiment by URL: {e}")


def update_emotion_by_url(url, update_data):
    """Update the emotion result of a document by URL."""
    try:
        supabase.table("news_data").update({
            "emotion_result": update_data
        }).eq("url", url).execute()
    except Exception as e:
        print(f"Error updating emotion by URL: {e}")


def update_propaganda_by_url(url, update_data):
    """Update the propaganda result of a document by URL."""
    try:
        supabase.table("news_data").update({
            "propaganda_result": update_data
        }).eq("url", url).execute()
    except Exception as e:
        print(f"Error updating propaganda by URL: {e}")


def update_factcheck_by_url(url, update_data):
    """Update the factcheck result of a document by URL."""
    try:
        supabase.table("news_data").update({
            "factcheck_result": update_data
        }).eq("url", url).execute()
    except Exception as e:
        print(f"Error updating factcheck by URL: {e}")


def update_summary_by_url(url, update_data):
    """Update the summary of a document by URL."""
    try:
        supabase.table("news_data").update({
            "summarise_result": update_data
        }).eq("url", url).execute()
    except Exception as e:
        print(f"Error updating summary by URL: {e}")


def update_model_data_summary_by_url(url, update_data):
    """Update the model data summary of a document by URL."""
    try:
        supabase.table("news_data").update({
            "data_summary": update_data
        }).eq("url", url).execute()
    except Exception as e:
        print(f"Error updating model data summary by URL: {e}")

# Delete
def delete_documents(filter_data):
    """Delete news documents matching filters."""
    try:
        query = supabase.table("news_data").delete()

        # Apply filters
        for key, value in filter_data.items():
            query = query.eq(key, value)

        result = query.execute()
        return len(result.data) if result.data else 0
    except Exception as e:
        print(f"Error deleting documents: {e}")
        return 0


def delete_document_by_id(id):
    """Delete a news document by ID."""
    try:
        result = supabase.table("news_data").delete().eq("id", id).execute()
        return len(result.data) if result.data else 0
    except Exception as e:
        print(f"Error deleting document by ID: {e}")
        return 0
