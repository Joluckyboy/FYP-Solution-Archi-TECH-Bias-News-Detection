from supabase_client import get_supabase_client
from datetime import datetime, timedelta, timezone
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

def update_uploader_by_url(url: str, uploader: str):
    """Update the uploader field for a news document by URL."""
    try:
        supabase.table("news_data").update({
            "uploader": uploader
        }).eq("url", url).execute()
    except Exception as e:
        print(f"Error updating uploader by URL: {e}")

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


def update_political_bias_by_url(url, update_data):
    """Update the political bias result of a document by URL."""
    try:
        supabase.table("news_data").update({
            "political_bias_result": update_data
        }).eq("url", url).execute()
    except Exception as e:
        print(f"Error updating political bias by URL: {e}")

def read_documents_by_domain(domain):
    try:
        cols = "url,title,sentiment_result,propaganda_result,factcheck_result"

        # Match: cnn.com/...
        result_exact = supabase.table("news_data").select(cols).ilike(
            "url", f"%://{domain}/%"
        ).execute()

        # Match: www.cnn.com/...
        result_www = supabase.table("news_data").select(cols).ilike(
            "url", f"%://www.{domain}/%"
        ).execute()

        # Match: edition.cnn.com/..., lite.cnn.com/... (any subdomain)  ← ADD THIS
        result_sub = supabase.table("news_data").select(cols).ilike(
            "url", f"%://%.{domain}/%"
        ).execute()

        # Deduplicate by URL
        seen = set()
        combined = []
        all_results = (
            (result_exact.data or []) +
            (result_www.data or []) +
            (result_sub.data or [])         # ← ADD THIS
        )
        for article in all_results:
            if article["url"] not in seen:
                seen.add(article["url"])
                combined.append(article)

        return combined
    except Exception as e:
        print(f"Error reading documents by domain: {e}")
        return []

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


# ── Digest Subscriptions ─────────────────────────────────────────────────────

def create_subscription(telegram_user_id, chat_id):
    """Create or re-activate a digest subscription."""
    try:
        result = supabase.table("digest_subscriptions").upsert({
            "telegram_user_id": telegram_user_id,
            "chat_id": chat_id,
            "is_active": True,
            "subscribed_at": datetime.now(timezone.utc).isoformat()
        }, on_conflict="telegram_user_id").execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error creating subscription: {e}")
        return None


def remove_subscription(telegram_user_id):
    """Soft-delete a subscription by setting is_active to False."""
    try:
        result = supabase.table("digest_subscriptions").update({
            "is_active": False
        }).eq("telegram_user_id", telegram_user_id).execute()
        return len(result.data) > 0 if result.data else False
    except Exception as e:
        print(f"Error removing subscription: {e}")
        return False


def get_active_subscriptions():
    """Get all active digest subscriptions."""
    try:
        result = supabase.table("digest_subscriptions").select(
            "telegram_user_id, chat_id"
        ).eq("is_active", True).execute()
        return result.data or []
    except Exception as e:
        print(f"Error getting active subscriptions: {e}")
        return []


def get_recent_biased_articles(hours=24):
    """Get recently analyzed articles that have a non-center political bias rating."""
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        result = supabase.table("news_data").select(
            "id, url, title, political_bias_result, summarise_result, updated_at"
        ).gte("updated_at", cutoff).execute()

        # Non-center ratings, ordered by how far from center
        bias_severity = {"left": 2, "right": 2, "leaning-left": 1, "leaning-right": 1}

        articles = []
        for article in (result.data or []):
            bias = article.get("political_bias_result") or {}
            rating = bias.get("rating", "center")
            if rating in bias_severity:
                article["bias_rating"] = rating
                article["bias_severity"] = bias_severity[rating]
                articles.append(article)

        # Sort by severity descending (left/right first, then leaning)
        articles.sort(key=lambda a: a["bias_severity"], reverse=True)
        return articles
    except Exception as e:
        print(f"Error getting recent biased articles: {e}")
        return []
