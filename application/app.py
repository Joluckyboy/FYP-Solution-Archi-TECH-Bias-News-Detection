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

from api_models import URLInput, NewsItem, URLwithBG
import methods as methods

logging.basicConfig(
    level=logging.INFO,  # or DEBUG
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
    # If needed, you can add code here to stop or clean up resources.
    # However, since your thread is daemon, it will stop when the main application exits.
    
# ------------------------ BACKGROUND THREAD TO PRE-SCRAPE AND ANALYSE ----------------------- #

logger = logging.getLogger(__name__)

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
    # return 200
    return {"status": "ok"}

@app.get("/application")
def health_check2():
    # return 200
    return {"status": "ok"}

@app.get("/application/check_query")
async def check_query():
    return {"status": "ok"}

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
    return process_url(input.url, return_news=True, background=input.background)

@app.get("/application/retrieve_exisiting")
async def retrieve_query(news_id: str):
    news = methods.get_news_by_id(news_id)
    return news

@app.get("/application/stream_news")
async def stream_news(news_id: str):
    """
    Streams updates for a single news document by ID and stops after 5 minutes.
    """
    async def event_stream(news_id):
        last_data = None  # Store last known state to prevent redundant updates
        start_time = time.time()  # Record the start time
        timeout = 4 * 60  # multiplier x sec

        while time.time() - start_time < timeout:  # Run for 5 minutes
            news = methods.get_news_by_id(news_id)  # Fetch latest data

            if news and news != last_data:  # Send only if data has changed
                last_data = news
                yield f"data: {json.dumps(news)}\n\n"

            await asyncio.sleep(5)  # Polling interval (adjust if needed)

        yield "event: close\ndata: Stream timeout\n\n"  # Signal client to close

    return StreamingResponse(event_stream(news_id), media_type="text/event-stream")

@app.get("/application/get_all_quiz")
async def get_all_quiz(question_type: str = None):
    quiz = methods.get_all_quiz(question_type=question_type)
    return quiz


@app.get("/application/get_quiz")
async def get_quiz(number: int = Query(..., description="Number of questions"), 
                   question_type: str = Query(..., description="Type of questions")):
    quiz = methods.get_quiz(number=number, question_type=question_type)
    return quiz

def process_url(url: str, return_news: bool = False, background: bool = True):
    """
    Core function that processes a news URL.
    If `return_news` is True, it returns the news data (for API responses).
    If `return_news` is False, it only performs data extraction & analysis.
    """
    try:
        logger.info("Checking if article exists...")
        exists = methods.check_exists(url)

        if exists["exists"]:
            logger.info(f"News already exists for {url}")
            if return_news:
                return methods.get_news(url)
            return  # If called from the background task, no return is needed.

        logger.info("New article, processing...")

        # Extract article content
        data = methods.extract_news(url)
        text = data.get("body", "")
        title = data.get("headline", "")
        
        if text == "" or title == "":
            raise HTTPException(status_code=400, detail="Invalid URL")

        # Save article content
        initial_save = methods.create_news(url, title, text)

        # Define the remaining processing as a separate function
        def remaining_processing():
            analysis_methods = [
                (methods.get_sentiment, "sentiment"),
                (methods.get_emotion, "emotion"),
                (methods.get_propaganda, "propaganda"),
                (methods.get_summarise, "summary"),
                (methods.get_data_summary, "data summary"),
                (methods.get_fact_check, "fact check")
            ]

            for analysis_method, label in analysis_methods:
                try:
                    result = analysis_method(text, url, title)
                    if not result:
                        logger.warning(f"No result returned for {label}.")
                except Exception as e:
                    logger.error(f"Error getting {label} for {url}: {e}")
                    return {"error": f"Failed at {label}: {str(e)}"}

            logger.info(f"Finished processing {url}")

            if return_news:
                return methods.get_news(url)

        if background:
            # Run the remaining processing in a separate thread
            threading.Thread(target=remaining_processing).start()
            # Return the initial save result immediately
            return initial_save
        else:
            # Perform the remaining processing synchronously
            result = remaining_processing()
            if return_news:
                return methods.get_news(url)
            return result

    except Exception as error:
        logger.error(f"Error processing {url}: {error}")
        if return_news:
            # Check if the error is an HTTPException with a description
            if hasattr(error, 'description') and str(error.description) == "Invalid URL format":
                raise HTTPException(status_code=400, detail="Invalid URL")
            else:
                # Handle other errors including ConnectionError
                error_message = str(error) if str(error) else "Internal Server Error"
                raise HTTPException(status_code=500, detail=error_message)
