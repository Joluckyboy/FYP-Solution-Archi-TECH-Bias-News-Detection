from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
from flask_swagger_ui import get_swaggerui_blueprint
from youtube_transcript_api import YouTubeTranscriptApi
from flask_cors import CORS
from urllib.parse import urlparse
import logging
import csv
import os
import time
import json

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
import pytesseract
import uuid

# Import refactored modules
from config.sources import SINGAPORE_SOURCES, US_SOURCES
from utils.csv_handler import CSVHandler
from utils.topic_classifier import assign_topic
from utils.background_jobs import create_scrape_job, get_job_status
from scrapers.custom_scrapers import (
    retrieve_straits_urls, retrieve_cna_urls,
    scrape_straits_times, scrape_cna, scrape_fox_news
)
from scrapers.generic_scraper import scrape_generic_source, scrape_generic_article
from bs4 import BeautifulSoup as bs
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

api = Api(
    app,
    version="1.0",
    title="Scraper API",
    description="Scrapes news articles for their body text",
)

ns = api.namespace("scraper", description="Scraping news articles and transcripts")



# # Model for the response of get-transcript
transcript_model = api.model(
    "Transcript",
    {
        "headline": fields.String(description="Full title of the video"),
        "body": fields.String(description="Full transcript of the video"),
    },
)

# API Models
article_model = api.model(
    "Article", 
    {
        "headline": fields.String(description="Article headline"),
        "body": fields.String(description="Article body"),
        "publish_date": fields.String(description="Article publish date"),
        "summary": fields.String(description="Article summary"),
        "topic": fields.String(description="Article topic"),
        "image_url": fields.String(description="Image URL")
    }
)

error_model = api.model("Error", {"error": fields.String(description="Error message")})

def get_requested_article_count(default: int | None = None) -> int | None:
    """Get requested article count from query params"""
    raw = request.args.get("num_articles")
    
    if isinstance(raw, str) and raw.lower() in {"max", "all"}:
        logger.info("Unlimited scraping requested")
        return None
    
    try:
        value = int(raw) if raw else (default if default is not None else 100)
    except ValueError:
        value = default if default is not None else 100
    
    if value is None or value <= 0:
        return None
    
    logger.info(f"Article limit: {value}")
    return value


@ns.route("/")
class HealthCheck(Resource):
    def get(self):
        return jsonify({"status": "ok", "version": "2.0-complete"})


@ns.route("/get-latest-articles")
class LatestArticleScraper(Resource):
    @api.doc(
            description="Get latest article URLs from CNA and Straits Times"
    )
    @api.param(
        "num_articles", "Number of articles per source", required=False
    )
    def get(self):
        article_nums = get_requested_article_count(default=30)
        try:
            cna_urls = retrieve_cna_urls(article_nums)
            straits_urls = retrieve_straits_urls(article_nums)
            return jsonify({
                "cna": cna_urls,
                "straits_times": straits_urls
            })
        except Exception as e:
            return {"error": str(e)}, 500

# ---------------------------------------
# Endpoint to get article from specific sites (Straits Times | OR | CNA)
@ns.route("/get-article")
class ArticleScraper(Resource):
    @api.doc(description="Scrape article from any supported source (including YouTube)")
    @api.param("url", "Article URL", required=True)
    def get(self):
        url = request.args.get("url")
        if not url:
            return {"error": "URL required"}, 400
        
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return {"error": "Invalid URL"}, 400
        
        return check_which_site(url)


def check_which_site(url):
    """Route URL to appropriate scraper - INCLUDING YouTube"""
    parse = urlparse(url).netloc
    
    # YouTube detection
    if "youtube" in parse.split(".") or "youtu" in parse.split("."):
        video_url = url
        
        # Extract video ID first (needed for caching)
        try:
            if "youtube.com" in video_url:
                if "/shorts/" in video_url:
                    video_id = video_url.split("/shorts/")[1]
                else:
                    video_id = video_url.split("v=")[-1]
                if "&" in video_id:
                    video_id = video_id.split("&")[0]
            elif "youtu.be" in video_url:
                video_id = video_url.split("/")[-1].split("?")[0]
            else:
                return {"error": "Invalid YouTube URL"}, 400
        except:
            return {"error": "Invalid YouTube URL"}, 400
        
        # Check cache first (avoid rate limiting)
        cache_file = f'data/youtube_cache_{video_id}.json'
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                logger.info(f"✓ Loaded transcript from cache: {video_id}")
                return cached_data
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        
        try:
            # Extract video ID
            if "youtube.com" in video_url:
                if "/shorts/" in video_url:
                    video_id = video_url.split("/shorts/")[1]
                else:
                    video_id = video_url.split("v=")[-1]
                if "&" in video_id:
                    video_id = video_id.split("&")[0]
            elif "youtu.be" in video_url:
                video_id = video_url.split("/")[-1].split("?")[0]
            else:
                return {"error": "Invalid YouTube URL"}, 400
            
            logger.info(f"Extracting YouTube video: {video_id}")
            
            # Get title from page with better headers (mimic browser)
            title = f"YouTube Video ({video_id})"  # default
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                res = requests.get(video_url, headers=headers, timeout=5)
                if res.status_code == 200:
                    try:
                        soup = bs(res.text, "html.parser")
                        title_tag = soup.title
                        if title_tag and title_tag.string:
                            title_text = str(title_tag.string).strip()
                            if "-" in title_text:
                                title = "-".join(title_text.split("-")[:-1]).strip()
                            else:
                                title = title_text
                        logger.info(f"Extracted title: {title}")
                    except Exception as parse_err:
                        logger.warning(f"BeautifulSoup parsing failed: {parse_err}, using default")
            except Exception as req_err:
                logger.warning(f"Could not fetch page: {req_err}, using default title")
            
            # Get transcript with improved retry logic for rate limiting
            logger.info(f"Getting transcript for video {video_id}...")
            import time as time_module
            max_retries = 3
            retry_delays = [3, 5, 10]  # Longer delays for YouTube rate limiting
            
            transcript = None
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    transcript = YouTubeTranscriptApi.get_transcript(video_id)
                    full_text = " ".join([segment["text"] for segment in transcript])
                    logger.info(f"✓ Transcript extracted: {len(full_text)} characters on attempt {attempt + 1}")
                    break
                except Exception as transcript_err:
                    error_msg = str(transcript_err)
                    last_error = error_msg
                    
                    # Check if it's a rate limit error (429)
                    if "429" in error_msg or "Too Many Requests" in error_msg:
                        if attempt < max_retries - 1:
                            delay = retry_delays[attempt]
                            logger.warning(f"⏱️ Rate limited (429), waiting {delay}s before retry (attempt {attempt + 1}/{max_retries})")
                            time_module.sleep(delay)
                            continue
                        else:
                            logger.error(f"⚠️ Rate limited after {max_retries} attempts")
                            return {
                                "error": f"YouTube API rate limited due to too many transcript requests. This is a YouTube API limitation when accessing transcripts programmatically. Please wait a few minutes and try again, or use a different video.",
                                "hint": "This happens when multiple requests are made to YouTube's transcript API. Consider: 1) waiting 5-10 minutes, 2) using a different video URL, 3) trying again at a different time"
                            }, 429
                    
                    # Not a rate limit error - try alternative languages
                    logger.warning(f"Transcript fetch failed: {error_msg[:100]}")
                    try:
                        logger.info(f"Attempting alternative transcripts...")
                        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                        
                        # Try manually created first (highest quality)
                        if transcript_list.manually_created_transcripts:
                            transcript = transcript_list.manually_created_transcripts[0].fetch()
                            logger.info(f"✓ Using manually created transcript")
                        # Then auto-generated
                        elif transcript_list.generated_transcripts:
                            transcript = transcript_list.generated_transcripts[0].fetch()
                            logger.info(f"✓ Using auto-generated transcript")
                        else:
                            raise Exception("No transcripts available")
                        
                        full_text = " ".join([segment["text"] for segment in transcript])
                        logger.info(f"✓ Alternative transcript extracted: {len(full_text)} characters")
                        break
                    except Exception as alt_err:
                        logger.error(f"No alternative transcripts: {str(alt_err)[:100]}")
                        last_error = str(alt_err)
                        # Continue to next retry attempt
                        if attempt < max_retries - 1:
                            delay = retry_delays[attempt]
                            logger.info(f"Retrying in {delay}s...")
                            time_module.sleep(delay)
            
            if transcript is None:
                return {"error": f"Could not retrieve transcript: {last_error[:100]}"}, 400
            
            # Prepare response
            response_data = {
                "headline": title,
                "body": full_text,
                "publish_date": None,
                "summary": None,
                "topic": None,
                "image_url": None
            }
            
            # Cache successful transcripts to avoid rate limiting on future requests
            try:
                os.makedirs('data', exist_ok=True)
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(response_data, f, ensure_ascii=False, indent=2)
                logger.info(f"✓ Cached transcript for {video_id}")
            except Exception as cache_err:
                logger.warning(f"Failed to cache transcript: {cache_err}")
            
            # Return with all required fields for article_model
            return response_data
        except Exception as e:
            logger.error(f"YouTube scraper error: {e}", exc_info=True)
            return {"error": str(e)}, 500
    
    # Regular article scrapers
    if "straitstimes" in parse:
        return scrape_straits_times(url)
    elif "channelnewsasia" in parse:
        return scrape_cna(url)
    elif "fox" in parse:
        return scrape_fox_news(url)
    else:
        return scrape_generic_article(url)


@ns.route("/get-transcript")
class TranscriptScraper(Resource):
    @api.doc(description="Get YouTube video transcript")
    @api.param("url", "YouTube video URL", required=True)
    @api.marshal_with(transcript_model)
    def get(self):
        """Extract transcript from YouTube video"""
        video_url = request.args.get('url')
        if not video_url:
            return {"error": "No URL provided"}, 400
        
        try:
            # Extract video ID
            if "youtube.com" in video_url:
                if "/shorts/" in video_url:
                    video_id = video_url.split("/shorts/")[1]
                else:
                    video_id = video_url.split("v=")[-1]
                if "&" in video_id:
                    video_id = video_id.split("&")[0]
            elif "youtu.be" in video_url:
                video_id = video_url.split("/")[-1].split("?")[0]
            else:
                return {"error": "Invalid YouTube URL"}, 400
            
            # Get title
            res = requests.get(video_url)
            soup = bs(res.text, "html.parser")
            title = str(soup.title.text)
            title = title.split("-")[:-1]
            title = "-".join(title)
            
            # Get transcript
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            full_text = " ".join([segment["text"] for segment in transcript])
            
            return {"headline": title, "body": full_text}
        except Exception as e:
            return {"error": str(e)}, 500


@ns.route("/get-article-screenscraper")
class ScreenScraperArticle(Resource):
    @api.doc(description="Screen scrape article using Selenium + OCR (Tesseract)")
    @api.param("url", "Article URL to screenshot and OCR", required=True)
    def get(self):
        """Screenshot entire page and extract text using OCR"""
        url = request.args.get("url")
        if not url:
            return {"error": "URL parameter is required"}, 400

        random_uuid = uuid.uuid4()
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("blink-settings=imagesEnabled=false")

        driver = webdriver.Chrome(options=options)

        try:
            driver.get(url)
            time.sleep(3)
            page_height = driver.execute_script("return document.body.scrollHeight")
            driver.set_window_size(1920, page_height)

            image_name = f"{random_uuid}.png"
            driver.get_screenshot_as_file(image_name)

            extracted_text = (
                pytesseract.image_to_string(Image.open(image_name))
                .strip()
                .replace("\n", " ")
            )
            
            # Clean up screenshot file
            try:
                os.remove(image_name)
            except:
                pass
            
            return {"body": extracted_text}
        except Exception as e:
            return {"error": f"An error occurred: {str(e)}"}, 500
        finally:
            driver.quit()


@ns.route('/scrape-all-sources')
class ScrapeAllSources(Resource):
    @api.doc(description="Scrape articles from all sources (synchronous - like original code)")
    @api.param('num_articles', 'Articles per source (default: 100)', required=False)
    @api.param('sg_only', 'Singapore sources only (default: false)', required=False)
    @api.param('async_mode', 'Use background job (true) or wait for completion (false, DEFAULT)', required=False)
    def post(self):
        """
        RESTORED ORIGINAL BEHAVIOR: Runs synchronously and returns full results
        - Default: Waits for completion (like app_old.py)
        - Use async_mode=true: Run in background job
        
        NOTE: Increase Gunicorn timeout if needed:
        gunicorn --timeout 900 app:app
        """
        try:
            num_articles = get_requested_article_count(default=100)
            sg_only = request.args.get('sg_only', 'false').lower() == 'true'
            # Default to async to avoid long-running sync timeouts
            async_mode = request.args.get('async_mode', 'true').lower() == 'true'
            
            # OPTIONAL: Async mode with background job
            if async_mode:
                job_id = create_scrape_job(num_articles, sg_only)
                return jsonify({
                    'success': True,
                    'job_id': job_id,
                    'status': 'started',
                    'message': f'Background job started. Check status at /scraper/job-status/{job_id}'
                })
            
            # Synchronous execution (blocks until completion)
            logger.info("Running synchronous scraping")
            job_id = create_scrape_job(num_articles, sg_only)
            
            # Wait for completion
            max_wait_time = 1800  # 30 minutes (adjust Gunicorn timeout accordingly)
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                status = get_job_status(job_id)
                
                if status.get('status') == 'completed':
                    return jsonify({
                        'success': True,
                        'log': {
                            'timestamp': status.get('started_at'),
                            'sources_scraped': status.get('sources_scraped', []),
                            'sources_failed': status.get('sources_failed', []),
                            'total_articles': status.get('saved_articles', 0),
                            'new_articles': status.get('saved_articles', 0)
                        },
                        'csv_file': CSVHandler.CSV_FILE,
                        'message': f'Scraping complete! {status.get("saved_articles", 0)} articles saved'
                    })
                
                if status.get('status') == 'failed':
                    return jsonify({
                        'success': False,
                        'error': status.get('error', 'Unknown error')
                    }), 500
                
                time.sleep(2)  # Poll every 2 seconds
            
            # Timeout - return what we have
            status = get_job_status(job_id)
            return jsonify({
                'success': True,
                'status': 'timeout',
                'message': f'Still running after {max_wait_time}s',
                'partial_results': {
                    'saved_articles': status.get('saved_articles', 0),
                    'completed_sources': status.get('completed_sources', 0)
                },
                'job_id': job_id
            }), 202
            
        except Exception as e:
            logger.error(f"Failed to run scrape job: {e}")
            return {"error": str(e)}, 500


@ns.route('/job-status/<string:job_id>')
class JobStatus(Resource):
    @api.doc(description="Check status of a background scraping job")
    @api.param('job_id', 'Job ID from /scrape-all-sources response', required=True)
    def get(self, job_id):
        """Get real-time progress of scraping job"""
        try:
            status = get_job_status(job_id)
            return jsonify(status)
        except Exception as e:
            return {"error": str(e)}, 500

@ns.route('/view-scraped-articles')
class ViewScrapedArticles(Resource):
    @api.doc(description="View all articles in CSV")
    def get(self):
        try:
            if not os.path.exists(CSVHandler.CSV_FILE):
                return jsonify({'articles': [], 'count': 0})
            
            articles = []
            with open(CSVHandler.CSV_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                articles = list(reader)
            
            return jsonify({
                'articles': articles,
                'count': len(articles)
            })
        except Exception as e:
            return {"error": str(e)}, 500


@ns.route('/article-stats')
class ArticleStats(Resource):
    @api.doc(description="Get statistics about scraped articles")
    def get(self):
        try:
            if not os.path.exists(CSVHandler.CSV_FILE):
                return jsonify({'error': 'No data available'})
            
            articles = []
            with open(CSVHandler.CSV_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                articles = list(reader)
            
            # Calculate stats
            from collections import Counter
            topic_dist = Counter(a['topic'] for a in articles)
            source_dist = Counter(a['source'] for a in articles)
            country_dist = Counter(a['country'] for a in articles)
            
            return jsonify({
                'total_articles': len(articles),
                'by_topic': dict(topic_dist),
                'by_source': dict(source_dist),
                'by_country': dict(country_dist)
            })
        except Exception as e:
            return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(debug=True)
