from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager

import vars as vars

import threading
import time
import json
import asyncio
import logging
import concurrent.futures
import os
import pandas as pd
from pathlib import Path
import s3_sync

import requests  # type: ignore
from api_models import NewsItem, URLwithBG
import methods as methods
import dashboard_methods as dashboard_methods
import visualisations as visualisations
import explanations as explanations
import redis_cache

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Prevent duplicate background jobs for the same article URL.
_analysis_guard_lock = threading.Lock()
_active_retry_urls = set()
_active_full_urls = set()


def _start_unique_background(url: str, job_type: str, target) -> bool:
    """Start background job only if same URL/job_type is not already running."""
    active_set = _active_retry_urls if job_type == "retry" else _active_full_urls

    with _analysis_guard_lock:
        if url in active_set:
            return False
        active_set.add(url)

    def wrapped_target():
        try:
            target()
        finally:
            with _analysis_guard_lock:
                active_set.discard(url)

    threading.Thread(target=wrapped_target, daemon=True).start()
    return True

# ------------------------ KEYWORDS SECTION ----------------------- #

SCRAPER_DATA_DIR = os.getenv("SCRAPER_DATA_DIR", "/app/data")
SCRAPED_ARTICLES_PATH = Path(SCRAPER_DATA_DIR) / "scraped_articles.csv"

def read_scraped_articles():
    """Load scraped articles CSV"""
    s3_sync.ensure_scraped_csv()  
    if not SCRAPED_ARTICLES_PATH.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(SCRAPED_ARTICLES_PATH)
        for col in ['title', 'summary', 'source', 'url', 'published_at', 'country', 'topic', 'politicalbias']:
            if col in df.columns:
                df[col] = df[col].fillna('').astype(str).str.strip()
        return df
    except Exception:
        return pd.DataFrame()

# ------------------------ BACKGROUND THREAD TO PRE-SCRAPE AND ANALYSE ----------------------- #
def periodic_query():
    """
    Runs every `vars.prescrape_interval` minutes, fetches latest URLs, 
    and processes them without returning data.
    """
    if not vars.prescrape_feature_toggle:
        logger.info("Prescrape feature disabled. Background thread not started.")
        return

    while True:
        try:
            logger.info("Fetching latest URLs from CNA and Straits Times...")
            article_dict = methods.get_latest_urls(vars.prescrape_num)

            for provider, url_list in article_dict.items():
                logger.info(f"Processing {len(url_list)} URLs from provider: {provider}...")
                for url in url_list:
                    try:
                        process_url(url, return_news=False)
                    except Exception as e:
                        logger.error(f"Failed to process URL {url}: {e}")
        except Exception as e:
            logger.error(f"Failed to process latest articles: {e}")

        time.sleep(vars.prescrape_interval * 60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    thread = threading.Thread(target=periodic_query, daemon=True)
    thread.start()
    
    yield
    
    # Shutdown logic
    # Thread is daemon, will stop when main application exits
    
# ------------------------ BACKGROUND THREAD TO PRE-SCRAPE AND ANALYSE ----------------------- #

app = FastAPI(
    title="Application layer API",
    description="API for GUIs that houses business logic",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://47.131.119.153:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.get("/application")
def health_check2():
    return {"status": "ok"}

@app.get("/application/check_query")
async def check_query():
    return {"status": "ok"}

@app.get("/application/bias_dashboard")
def get_bias_dashboard():
    """
    Returns aggregated bias metrics for the frontend dashboard (Sprint 1 MVP).
    Data is loaded from datasets/news_outlets_summary.csv via dashboard_methods.py
    """
    try:
        return dashboard_methods.load_dashboard_data()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        logger.exception("Failed to load bias dashboard data")
        raise HTTPException(status_code=500, detail="Failed to load bias dashboard data")
    
@app.get("/application/visualisations")
def get_visualisations():
    try:
        return visualisations.load_visualisations_data()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to load visualisations data")
        raise HTTPException(status_code=500, detail="Failed to load visualisations data")
    
@app.get("/application/articles/keyword/{keyword}")
def get_articles_by_keyword(keyword: str):
    """
    Search articles containing keyword in title OR summary (case-insensitive).
    Matches if: exact phrase OR all words OR at least 2/3 words present.
    """
    try:
        df = read_scraped_articles()
        if df.empty:
            return {"articles": []}
        
        # Normalize keyword: lowercase + split multi-words
        keyword_lower = keyword.lower().strip()
        keywords = [w for w in keyword_lower.split() if w.strip()]
        
        def matches_article(row):
            title_lower = str(row.get('title', '')).lower()
            summary_lower = str(row.get('summary', '')).lower()
            text = title_lower + ' ' + summary_lower
            
            # 1. Exact phrase match (highest priority)
            if keyword_lower and keyword_lower in text:
                return True
            
            # 2. All words present (any order)
            if all(word in text for word in keywords):
                return True
            
            # 3. Exactly 2 out of 3+ words
            if len(keywords) >= 3:
                matches = sum(1 for word in keywords if word in text)
                if matches >= 2:  # At least 2 words from 3+ word query
                    return True
            
            # 4. For 1-2 word queries: require ALL words
            if len(keywords) <= 2:
                return all(word in text for word in keywords)
            
            return False
        
        # Apply matching + select safe columns
        mask = df.apply(matches_article, axis=1)
        
        cols = [
            'title', 'summary', 'source', 'url', 'published_at', 
            'image_url', 'country', 'topic', 'political_bias'
        ]
        
        # Filter to only existing columns (safe)
        available_cols = [col for col in cols if col in df.columns]
        results = df[mask][available_cols].head(50).to_dict('records')
        
        return {"articles": results}
        
    except Exception as e:
        logger.exception("Failed to search articles by keyword")
        raise HTTPException(status_code=500, detail="Search failed")
    
@app.get("/application/scraper_stats")
def get_scraper_stats():
    try:
        return explanations.load_scraper_stats()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to load scraper stats")
        raise HTTPException(status_code=500, detail="Failed to load scraper stats")

# Alias map for common shorthand domain names -> actual URL domains
DOMAIN_ALIASES = {
    # --- Singapore ---
    "cna": "channelnewsasia.com",
    "cna.com": "channelnewsasia.com",
    "channelnewsasia": "channelnewsasia.com",
    "channel newsasia": "channelnewsasia.com",
    "straits": "straitstimes.com",
    "straitstimes": "straitstimes.com",
    "straits times": "straitstimes.com",
    "st": "straitstimes.com",
    "st.com": "straitstimes.com",
    "todayonline": "todayonline.com",
    "today": "todayonline.com",
    "today online": "todayonline.com",
    "mothership": "mothership.sg",
    "businesstimes": "businesstimes.com.sg",
    "business times": "businesstimes.com.sg",
    "bt": "businesstimes.com.sg",
    "yahoo": "yahoo.com",
    "yahoo sg": "sg.news.yahoo.com",
    "yahoo singapore": "sg.news.yahoo.com",
    # --- United States / International ---
    "cnn": "cnn.com",
    "foxnews": "foxnews.com",
    "fox": "foxnews.com",
    "fox news": "foxnews.com",
    "nbcnews": "nbcnews.com",
    "nbc": "nbcnews.com",
    "nbc news": "nbcnews.com",
    "usatoday": "usatoday.com",
    "usa today": "usatoday.com",
    "npr": "npr.org",
    "nytimes": "nytimes.com",
    "nyt": "nytimes.com",
    "new york times": "nytimes.com",
    "washingtonpost": "washingtonpost.com",
    "wapo": "washingtonpost.com",
    "washington post": "washingtonpost.com",
    "wsj": "wsj.com",
    "wall street journal": "wsj.com",
    "ap": "apnews.com",
    "ap news": "apnews.com",
    "apnews": "apnews.com",
    "associated press": "apnews.com",
    "reuters": "reuters.com",
    "bbc": "bbc.com",
    "bbc news": "bbc.com",
    "abcnews": "abcnews.go.com",
    "abc news": "abcnews.go.com",
    "abc": "abcnews.go.com",
    "cbsnews": "cbsnews.com",
    "cbs": "cbsnews.com",
    "cbs news": "cbsnews.com",
    "msnbc": "msnbc.com",
    "politico": "politico.com",
    "breitbart": "breitbart.com",
    "huffpost": "huffpost.com",
    "huffington post": "huffpost.com",
    "thehill": "thehill.com",
    "the hill": "thehill.com",
    "vox": "vox.com",
    "axios": "axios.com",
}


def _find_similar_aliases(query: str, max_results: int = 5) -> list:
    """Find alias keys that are similar to the query using substring and word overlap matching."""
    query_lower = query.lower().strip()
    query_words = set(query_lower.split())
    scored = []

    for alias_key in DOMAIN_ALIASES:
        alias_words = set(alias_key.split())
        # Check if query is a substring of alias or vice versa
        if query_lower in alias_key or alias_key in query_lower:
            scored.append((alias_key, 0.8))
            continue
        # Check word overlap
        overlap = query_words & alias_words
        if overlap:
            score = len(overlap) / max(len(query_words), len(alias_words))
            scored.append((alias_key, score))
            continue
        # Check if any query word is a substring of any alias word or vice versa
        for qw in query_words:
            for aw in alias_words:
                if len(qw) >= 3 and (qw in aw or aw in qw):
                    scored.append((alias_key, 0.4))
                    break
            else:
                continue
            break

    # Sort by score descending, deduplicate by resolved domain
    scored.sort(key=lambda x: x[1], reverse=True)
    seen_domains = set()
    results = []
    for alias_key, score in scored:
        resolved = DOMAIN_ALIASES[alias_key]
        if resolved not in seen_domains and score >= 0.3:
            seen_domains.add(resolved)
            results.append(alias_key)
            if len(results) >= max_results:
                break
    return results


@app.get("/application/source_credibility")
def get_source_credibility(domain: str = Query(..., description="Domain to check credibility for")):
    """
    Calculate credibility score for a news source based on historical analysis data.
    Queries all analyzed articles from the given domain and aggregates metrics.
    """
    from urllib.parse import urlparse

    # Keep original input for fuzzy matching before normalization
    original_input = domain.strip().lower()

    # Normalize domain: strip protocol, www, trailing slashes
    domain = original_input
    if "://" in domain:
        domain = urlparse(domain).netloc or domain
    domain = domain.removeprefix("www.")
    domain = domain.rstrip("/")

    if not domain:
        raise HTTPException(status_code=400, detail="Domain is required")

    # Resolve aliases (e.g. "cna" -> "channelnewsasia.com")
    resolved = DOMAIN_ALIASES.get(domain, None)
    if not resolved:
        # No exact alias match - find suggestions
        suggestions = _find_similar_aliases(domain)
        if suggestions:
            domain_to_query = domain  # Still try the raw domain against DB
        else:
            domain_to_query = domain
    else:
        suggestions = []
        domain_to_query = resolved

    domain = domain_to_query

    try:
        response = requests.get(f"{vars.database_url}/database/getByDomain/{domain}")
        articles = response.json().get("articles", [])
    except Exception as e:
        logger.error(f"Failed to fetch articles for domain {domain}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch source data")

    if not articles:
        result = {
            "domain": domain,
            "status": "no_data",
            "message": "No data available for this source yet. Submit an article from this source to start building its profile.",
        }
        if suggestions:
            result["suggestions"] = suggestions
        return result

    # Filter to articles that have at least some analysis data
    analyzed = [a for a in articles if a.get("sentiment_result") or a.get("propaganda_result") or a.get("factcheck_result")]
    total_articles = len(analyzed)

    if total_articles == 0:
        result = {
            "domain": domain,
            "status": "no_data",
            "message": "No data available for this source yet. Submit an article from this source to start building its profile.",
        }
        if suggestions:
            result["suggestions"] = suggestions
        return result

    if total_articles < 3:
        label = "Insufficient Data"
    else:
        label = None  # Will be calculated

    # Calculate averages
    propaganda_probs = []
    factual_counts = {"total": 0, "factual": 0}
    sentiment_totals = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
    sentiment_count = 0
    technique_counts = {}

    for article in analyzed:
        # Propaganda
        prop = article.get("propaganda_result")
        if prop and isinstance(prop, dict):
            prob = prop.get("propaganda_probability")
            if prob is not None:
                propaganda_probs.append(float(prob))
            # Count techniques
            techniques = prop.get("formatted_result") or []
            for item in techniques:
                if isinstance(item, list) and len(item) >= 1:
                    tech_name = item[0]
                    technique_counts[tech_name] = technique_counts.get(tech_name, 0) + 1

        # Fact-check
        facts = article.get("factcheck_result")
        if facts and isinstance(facts, list):
            for fact in facts:
                if isinstance(fact, dict) and "correctness" in fact:
                    factual_counts["total"] += 1
                    correctness = fact["correctness"].lower()
                    if correctness in ("factual", "mostly factual"):
                        factual_counts["factual"] += 1

        # Sentiment
        sent = article.get("sentiment_result")
        if sent and isinstance(sent, dict):
            for key in ("positive", "negative", "neutral"):
                val = sent.get(key)
                if isinstance(val, (int, float)):
                    sentiment_totals[key] += val
            sentiment_count += 1

    avg_propaganda = sum(propaganda_probs) / len(propaganda_probs) if propaganda_probs else 0.0
    factual_accuracy = (factual_counts["factual"] / factual_counts["total"]) if factual_counts["total"] > 0 else 0.0

    avg_sentiment = {}
    if sentiment_count > 0:
        avg_sentiment = {k: round(v / sentiment_count, 4) for k, v in sentiment_totals.items()}

    # Sentiment skew: how far from perfectly neutral (0.33/0.33/0.33)
    # Skew = 0 means perfectly balanced, 1 means extremely skewed
    if avg_sentiment:
        ideal = 1.0 / 3.0
        skew = sum(abs(avg_sentiment.get(k, ideal) - ideal) for k in ("positive", "negative", "neutral")) / 2.0
    else:
        skew = 0.0

    # Credibility score (0-100):
    # - Low propaganda = good (weight 40%)
    # - High factual accuracy = good (weight 40%)
    # - Low sentiment skew = good (weight 20%)
    if label is None:
        propaganda_score = (1.0 - avg_propaganda) * 40
        accuracy_score = factual_accuracy * 40
        skew_score = (1.0 - min(skew, 1.0)) * 20
        credibility_score = round(propaganda_score + accuracy_score + skew_score, 1)

        if credibility_score >= 80:
            label = "Highly Credible"
        elif credibility_score >= 60:
            label = "Moderately Credible"
        elif credibility_score >= 40:
            label = "Questionable"
        else:
            label = "Low Credibility"
    else:
        credibility_score = None

    # Determine political leaning from sentiment distribution
    if avg_sentiment:
        pos = avg_sentiment.get("positive", 0)
        neg = avg_sentiment.get("negative", 0)
        diff = pos - neg
        if abs(diff) < 0.05:
            leaning = "Neutral"
        elif diff > 0.15:
            leaning = "Leans Positive (Right-leaning tendency)"
        elif diff > 0.05:
            leaning = "Slightly Positive-leaning"
        elif diff < -0.15:
            leaning = "Leans Negative (Left-leaning tendency)"
        else:
            leaning = "Slightly Negative-leaning"
    else:
        leaning = "Unknown"

    # Top techniques
    top_techniques = sorted(technique_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "domain": domain,
        "status": "ok",
        "label": label,
        "credibility_score": credibility_score,
        "articles_analyzed": total_articles,
        "avg_propaganda_probability": round(avg_propaganda, 4),
        "factual_accuracy_rate": round(factual_accuracy, 4),
        "avg_sentiment": avg_sentiment,
        "sentiment_leaning": leaning,
        "top_propaganda_techniques": [{"technique": t, "count": c} for t, c in top_techniques],
    }


@app.post("/application/new_query", response_model=NewsItem, responses={
    200: {
        "description": "News data"
    },
    404: {
        "description": "URL does not exist"
    },
    400:{
        "description": "Invalid URL"
    }
})
def new_query(input: URLwithBG):
    """
    Processes a news article URL, retrieving or extracting news data.
    """
    if input.url is None:
        raise HTTPException(status_code=400, detail="URL is required")
    return process_url(
        input.url,
        return_news=True,
        background=input.background if input.background is not None else True,
        force_reanalyze=input.force if hasattr(input, 'force') and input.force is not None else False,
    )

@app.get("/application/retrieve_exisiting")
async def retrieve_query(news_id: str):
    news = methods.get_news_by_id(news_id)
    return news

@app.get("/application/stream_news")
async def stream_news(news_id: str):
    """
    Streams updates for a single news document by ID and stops after 4 minutes.
    """
    async def event_stream(news_id):
        last_data = None
        start_time = time.time()
        timeout = 4 * 60  # 4 minutes

        while time.time() - start_time < timeout:
            news = methods.get_news_by_id(news_id)

            if news and news != last_data:
                last_data = news
                yield f"data: {json.dumps(news)}\n\n"

            await asyncio.sleep(5)

        yield "event: close\ndata: Stream timeout\n\n"

    return StreamingResponse(event_stream(news_id), media_type="text/event-stream")

@app.get("/application/get_all_quiz")
async def get_all_quiz(question_type: str = Query(None, description="Type of questions")):
    quiz = methods.get_all_quiz(question_type=question_type)
    return quiz

@app.get("/application/get_quiz")
async def get_quiz(number: int = Query(..., description="Number of questions"),
                   question_type: str = Query(..., description="Type of questions")):
    quiz = methods.get_quiz(number=number, question_type=question_type)
    return quiz


# ── Digest Subscriptions ─────────────────────────────────────────────────────

@app.post("/application/digest/subscribe")
async def digest_subscribe(telegram_user_id: int, chat_id: int):
    """Subscribe a Telegram user to the daily bias digest."""
    result = methods.subscribe_digest(telegram_user_id, chat_id)
    return result


@app.post("/application/digest/unsubscribe")
async def digest_unsubscribe(telegram_user_id: int):
    """Unsubscribe a Telegram user from the daily bias digest."""
    result = methods.unsubscribe_digest(telegram_user_id)
    return result


@app.get("/application/digest/subscriptions")
async def digest_get_subscriptions():
    """Get all active digest subscriptions."""
    subs = methods.get_active_subscriptions()
    return {"subscriptions": subs}


@app.get("/application/digest/recent-biased")
async def digest_recent_biased(hours: int = 24):
    """Get recently analyzed articles with non-center political bias."""
    articles = methods.get_recent_biased_articles(hours=hours)
    return {"articles": articles}

def process_url(url: str, return_news: bool = False, background: bool = True, force_reanalyze: bool = False):
    """
    Core function that processes a news URL with smart retry logic.
    
    Args:
        url: Article URL
        return_news: Whether to return news data (for API responses)
        background: Whether to run analysis in background thread
        force_reanalyze: Force re-analysis of all services
    
    Smart Retry Logic:
        - If article exists with complete data -> return cached
        - If article exists with missing data -> retry ONLY missing services
        - If force_reanalyze=True -> re-run ALL services
        - If new article -> run ALL services
    """
    try:
        logger.info(f"Processing URL: {url}")

        # --- Redis cache check (fast path) ---
        if not force_reanalyze:
            cached = redis_cache.get_cached_result(url)
            if cached and redis_cache.is_analysis_complete(cached):
                logger.info(f"Returning Redis-cached result for {url}")
                if return_news:
                    return cached
                return
        else:
            redis_cache.delete_cached_result(url)

        exists = methods.check_exists(url)

        if exists["exists"]:
            existing = methods.get_news(url)

            # Identify which analyses are missing
            missing_analyses = []
            if not existing.get("sentiment_result"):
                missing_analyses.append("sentiment")
            if not existing.get("emotion_result"):
                missing_analyses.append("emotion")
            if not existing.get("propaganda_result"):
                missing_analyses.append("propaganda")
            if not existing.get("factcheck_result"):
                missing_analyses.append("factcheck")
            if not existing.get("summarise_result"):
                missing_analyses.append("summarise")
            political_bias = existing.get("political_bias_result")
            if not political_bias or (isinstance(political_bias, dict) and len(political_bias) == 0):
                missing_analyses.append("political_bias")
            # Check for empty dict or None/null data_summary
            data_summary = existing.get("data_summary")
            if not data_summary or (isinstance(data_summary, dict) and len(data_summary) == 0):
                missing_analyses.append("data_summary")

            # All analyses complete and no force re-analyze
            if not missing_analyses and not force_reanalyze:
                logger.info(f"Article exists with complete results for {url} - returning cached data")
                # Cache in Redis for future fast lookups
                redis_cache.cache_result(url, existing)
                if return_news:
                    return existing
                return
            
            # Get content for retry/re-analysis
            text = existing.get("content", "")
            title = existing.get("title", "")
            
            # Fallback to scrape if stored content is missing
            if not text or not title:
                logger.warning(f"Stored content missing for {url}, re-scraping...")
                data = methods.extract_news(url)
                text = data.get("body", "")
                title = data.get("headline", "")
                if not text or not title:
                    raise HTTPException(status_code=400, detail="Invalid URL")
            
            # AUTO-RETRY: Only retry missing analyses IN PARALLEL
            if missing_analyses and not force_reanalyze:
                logger.info(f"Auto-retrying {len(missing_analyses)} missing service(s): {', '.join(missing_analyses)}")
                
                def selective_retry():
                    """Only re-run the failed/missing analyses in parallel"""
                    retry_tasks = []
                    
                    if "sentiment" in missing_analyses:
                        retry_tasks.append((methods.get_sentiment, "sentiment"))
                    if "emotion" in missing_analyses:
                        retry_tasks.append((methods.get_emotion, "emotion"))
                    if "propaganda" in missing_analyses:
                        retry_tasks.append((methods.get_propaganda, "propaganda"))
                    if "summarise" in missing_analyses:
                        retry_tasks.append((methods.get_summarise, "summarise"))
                    if "factcheck" in missing_analyses:
                        retry_tasks.append((methods.get_fact_check, "fact check"))
                    if "political_bias" in missing_analyses:
                        retry_tasks.append((methods.get_political_bias, "political bias"))
                    
                    # Run retry tasks in parallel.
                    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                        futures = {}
                        for task_method, label in retry_tasks:
                            future = executor.submit(task_method, text, url, title)
                            futures[future] = label
                        
                        for future in concurrent.futures.as_completed(futures):
                            label = futures[future]
                            try:
                                future.result()
                                logger.info(f"✓ Successfully retried {label} for {url}")
                            except Exception as e:
                                logger.error(f"✗ {label.capitalize()} retry failed: {e}")
                    
                    # Generate data summary once.
                    # Hybrid mode: if some analyses are missing, save a partial local summary.
                    try:
                        fresh_data = methods.get_news(url) or {}
                        logger.info(f"Generating final data summary after retries for {url}")
                        methods.get_data_summary(
                            text,
                            url,
                            title,
                            trigger="retry-final",
                            sentiment=fresh_data.get("sentiment_result"),
                            emotion=fresh_data.get("emotion_result"),
                            propaganda=fresh_data.get("propaganda_result"),
                            summarise=fresh_data.get("summarise_result"),
                            allow_partial_local=True,
                        )
                        logger.info(f"✓ Completed final/partial data summary after retries for {url}")
                    except Exception as e:
                        logger.error(f"✗ Data summary regeneration failed: {e}")
                    
                    logger.info(f"Selective retry complete for {url}")
                    # Cache the completed result in Redis
                    completed = methods.get_news(url) or {}
                    if redis_cache.is_analysis_complete(completed):
                        redis_cache.cache_result(url, completed)

                if background:
                    started = _start_unique_background(url, "retry", selective_retry)
                    if started:
                        logger.info(f"Background selective retry started for {url}")
                    else:
                        logger.info(f"Background selective retry already running for {url}; skipping duplicate trigger")
                    if return_news:
                        return existing
                    return
                else:
                    selective_retry()
                    if return_news:
                        return methods.get_news(url)
                    return
            
            # FORCE RE-ANALYZE: User explicitly requested full re-analysis
            if force_reanalyze:
                logger.info(f"Force re-analyzing ALL services for {url}")
                # Continue to full analysis below
                initial_save = existing
            
        else:
            # NEW ARTICLE: Scrape and save content
            logger.info(f"New article detected: {url}")
            data = methods.extract_news(url)
            text = data.get("body", "")
            title = data.get("headline", "")
            
            if not text or not title:
                raise HTTPException(status_code=400, detail="Invalid URL - could not extract content")
            
            # Save article content to database
            initial_save = methods.create_news(url, title, text)
            logger.info(f"Article content saved for {url}")

        # FULL ANALYSIS: Run all services IN PARALLEL (for new articles or force re-analyze)
        def full_analysis():
            """Run all analysis services in parallel for maximum speed"""
            # Track results as they complete
            completed_results = {}
            
            # Group 1: Independent analyses that can run simultaneously
            independent_tasks = [
                (methods.get_sentiment, "sentiment"),
                (methods.get_emotion, "emotion"),
                (methods.get_propaganda, "propaganda"),
                (methods.get_summarise, "summary"),
                (methods.get_fact_check, "fact check"),
                (methods.get_political_bias, "political bias"),
            ]
            
            # Run all independent analyses in parallel using ThreadPoolExecutor
            logger.info(f"Starting parallel analysis for {url} ({len(independent_tasks)} services)")
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {}
                for analysis_method, label in independent_tasks:
                    future = executor.submit(analysis_method, text, url, title)
                    futures[future] = label
                
                # Wait for all to complete and log results.
                for future in concurrent.futures.as_completed(futures):
                    label = futures[future]
                    try:
                        result = future.result()
                        if not result:
                            logger.warning(f"⚠️ No result returned for {label}")
                        else:
                            logger.info(f"✓ Completed {label} analysis for {url}")
                            completed_results[label] = result
                    except Exception as e:
                        logger.error(f"✗ Error during {label} analysis for {url}: {e}")
            
            # Group 2: Data summary depends on other analyses, run last
            try:
                # Get fresh data from database now that all analyses are complete
                fresh_data = methods.get_news(url) or {}
                logger.info(f"Running final data summary analysis for {url}")
                result = methods.get_data_summary(
                    text,
                    url,
                    title,
                    trigger="final",
                    sentiment=fresh_data.get("sentiment_result"),
                    emotion=fresh_data.get("emotion_result"),
                    propaganda=fresh_data.get("propaganda_result"),
                    summarise=fresh_data.get("summarise_result"),
                    allow_partial_local=True,
                )
                if result:
                    logger.info(f"✓ Completed data summary for {url}: {list(result.keys())}")
                else:
                    logger.warning(f"⚠️ Data summary returned empty for {url}")
            except Exception as e:
                logger.error(f"✗ Error during data summary analysis for {url}: {e}")

            # Cache the completed result in Redis
            completed = methods.get_news(url) or {}
            if redis_cache.is_analysis_complete(completed):
                redis_cache.cache_result(url, completed)

            logger.info(f"✓ Full analysis complete for {url}")

        if background:
            # Run analysis in background thread
            started = _start_unique_background(url, "full", full_analysis)
            if started:
                logger.info(f"Background full analysis started for {url}")
            else:
                logger.info(f"Background full analysis already running for {url}; skipping duplicate trigger")
            if return_news:
                return initial_save
            return
        else:
            # Run analysis synchronously
            full_analysis()
            if return_news:
                return methods.get_news(url)
            return

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as error:
        logger.error(f"Error processing {url}: {error}", exc_info=True)
        if return_news:
            if hasattr(error, 'description') and str(error.description) == "Invalid URL format":
                raise HTTPException(status_code=400, detail="Invalid URL")
            else:
                error_message = str(error) if str(error) else "Internal Server Error"
                raise HTTPException(status_code=500, detail=error_message)