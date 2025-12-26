import dramatiq
from dramatiq.brokers.redis import RedisBroker
from datetime import datetime
from app.core.config import settings
from app.db.session import get_supabase_admin

# Set up Redis broker for Dramatiq
redis_broker = RedisBroker(url=settings.REDIS_URL)
dramatiq.set_broker(redis_broker)

@dramatiq.actor
def process_news_ingestion(source_url: str):
    """Background task to ingest news from a source using Supabase"""
    print(f"Processing news from {source_url}")
    
    supabase = get_supabase_admin()
    
    try:
        # Placeholder data (replace with actual scraping logic)
        article_data = {
            'title': f'News from {source_url}',
            'content': 'Article content would be scraped here...',
            'source': source_url,
            'url': source_url
        }
        
        # Insert into Supabase
        response = supabase.table('news_articles').insert(article_data).execute()
        print(f"Article inserted: {response.data}")
        
        # Trigger bias analysis for the new article
        if response.data:
            article_id = response.data[0]['id']
            analyze_article_bias.send(article_id)
        
        return {"status": "completed", "source": source_url}
    except Exception as e:
        print(f"Error ingesting news: {e}")
        return {"status": "failed", "error": str(e)}

@dramatiq.actor
def analyze_article_bias(article_id: int):
    """Background task to analyze bias in an article using Supabase"""
    print(f"Analyzing bias for article {article_id}")
    
    supabase = get_supabase_admin()
    
    try:
        # Fetch article from Supabase
        article_response = supabase.table('news_articles')\
            .select('*')\
            .eq('id', article_id)\
            .execute()
        
        if not article_response.data:
            return {"status": "failed", "error": "Article not found"}
        
        article = article_response.data[0]
        
        # Placeholder bias analysis (replace with actual ML model)
        bias_data = {
            'article_id': article_id,
            'bias_score': 0.5,
            'bias_type': 'neutral',
            'confidence': 0.8,
            'analysis_details': {
                'content_length': len(article.get('content', '')),
                'source': article.get('source', 'unknown')
            }
        }
        
        # Save analysis to Supabase
        supabase.table('bias_analyses').insert(bias_data).execute()
        
        # Trigger Elasticsearch indexing
        index_article_elasticsearch.send(article_id, article['content'])
        
        return {"status": "completed", "article_id": article_id}
    except Exception as e:
        print(f"Error analyzing bias: {e}")
        return {"status": "failed", "error": str(e)}

@dramatiq.actor
def index_article_elasticsearch(article_id: int, content: str):
    """Background task to index article in Elasticsearch"""
    print(f"Indexing article {article_id} in Elasticsearch")
    
    from app.db.elasticsearch import get_elasticsearch
    
    try:
        es = get_elasticsearch()
        
        # Index document
        es.index(
            index='news_articles',
            id=article_id,
            body={
                'article_id': article_id,
                'content': content,
                'indexed_at': datetime.now().isoformat()
            }
        )
        
        return {"status": "completed", "article_id": article_id}
    except Exception as e:
        print(f"Error indexing to Elasticsearch: {e}")
        return {"status": "failed", "error": str(e)}
