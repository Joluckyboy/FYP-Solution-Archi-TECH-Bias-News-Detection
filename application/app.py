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

from api_models import URLInput, NewsItem, URLwithBG
import methods as methods
import dashboard_methods as dashboard_methods
import visualisations as visualisations

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)

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
            if not existing.get("data_summary"):
                missing_analyses.append("data_summary")
            
            # All analyses complete and no force re-analyze
            if not missing_analyses and not force_reanalyze:
                logger.info(f"Article exists with complete results for {url} - returning cached data")
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
                    
                    # Run retry tasks in parallel (except data_summary which depends on others)
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
                    
                    # Data summary depends on other analyses, run last
                    if "data_summary" in missing_analyses:
                        try:
                            logger.info(f"Retrying data summary for {url}")
                            methods.get_data_summary(text, url, title)
                            logger.info(f"✓ Successfully retried data summary for {url}")
                        except Exception as e:
                            logger.error(f"✗ Data summary retry failed: {e}")
                    
                    logger.info(f"Selective retry complete for {url}")
                
                if background:
                    threading.Thread(target=selective_retry, daemon=True).start()
                    logger.info(f"Background selective retry started for {url}")
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
            
            # Group 1: Independent analyses that can run simultaneously
            independent_tasks = [
                (methods.get_sentiment, "sentiment"),
                (methods.get_emotion, "emotion"),
                (methods.get_propaganda, "propaganda"),
                (methods.get_summarise, "summary"),
                (methods.get_fact_check, "fact check"),  # Now optimized to 1 API call per article!
            ]
            
            # Run all independent analyses in parallel using ThreadPoolExecutor
            logger.info(f"Starting parallel analysis for {url} ({len(independent_tasks)} services)")
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {}
                for analysis_method, label in independent_tasks:
                    future = executor.submit(analysis_method, text, url, title)
                    futures[future] = label
                
                # Wait for all to complete and log results
                for future in concurrent.futures.as_completed(futures):
                    label = futures[future]
                    try:
                        result = future.result()
                        if not result:
                            logger.warning(f"⚠️ No result returned for {label}")
                        else:
                            logger.info(f"✓ Completed {label} analysis for {url}")
                    except Exception as e:
                        logger.error(f"✗ Error during {label} analysis for {url}: {e}")
            
            # Group 2: Data summary depends on other analyses, run last
            try:
                logger.info(f"Running data summary analysis for {url}")
                result = methods.get_data_summary(text, url, title)
                if result:
                    logger.info(f"✓ Completed data summary for {url}")
            except Exception as e:
                logger.error(f"✗ Error during data summary analysis for {url}: {e}")

            logger.info(f"✓ Full analysis complete for {url}")

        if background:
            # Run analysis in background thread
            threading.Thread(target=full_analysis, daemon=True).start()
            logger.info(f"Background full analysis started for {url}")
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