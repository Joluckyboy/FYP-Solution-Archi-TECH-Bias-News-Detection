import csv
import json
import logging
import os
import time
import uuid
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup as bs
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from youtube_transcript_api import YouTubeTranscriptApi

from config.sources import SINGAPORE_SOURCES, US_SOURCES
from scrapers.custom_scrapers import (
    retrieve_cna_urls,
    retrieve_straits_urls,
    scrape_cna,
    scrape_fox_news,
    scrape_straits_times,
    scrape_video_with_ytdlp,   # ← add
    _is_video_url,              # ← add
)
from scrapers.generic_scraper import scrape_generic_article, scrape_generic_source
from utils.background_jobs import create_scrape_job, get_job_status
from utils.csv_handler import CSVHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Scraper API",
    version="1.0",
    description="Scrapes news articles for their body text",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_article_count(num_articles: str | None, default: int | None = 100) -> int | None:
    if isinstance(num_articles, str) and num_articles.lower() in {"max", "all"}:
        return None
    try:
        value = int(num_articles) if num_articles else (default if default is not None else 100)
    except (ValueError, TypeError):
        value = default if default is not None else 100
    if value is None or value <= 0:
        return None
    return value

def _scrape_hosted_video_page(url: str):
    """
    Scrape a non-YouTube hosted video page by extracting metadata + caption text.
    These pages don't have transcripts, so we extract og:description + any <p> text.
    """
    try:
        import requests as _requests
        from bs4 import BeautifulSoup as bs
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = _requests.get(url, headers=headers, timeout=10)
        soup = bs(res.content, "html.parser")

        # Headline from og:title
        headline = ""
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            headline = og_title["content"].strip()
        if not headline:
            h1 = soup.find("h1")
            headline = h1.get_text(strip=True) if h1 else "Video"

        # Body: og:description + all <p> text
        body_parts = []
        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            body_parts.append(og_desc["content"].strip())

        paras = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 20]
        body_parts.extend(paras)

        body = " ".join(body_parts).strip()

        if not body:
            logger.warning(f"Hosted video page: no content extracted from {url}")
            return None

        # Image
        image_url = ""
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            image_url = og_image["content"]

        # Date
        publish_date = None
        for time_elem in soup.find_all("time"):
            dt = time_elem.get("datetime")
            if dt:
                try:
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                    publish_date = date_obj.strftime("%Y-%m-%d")
                    break
                except Exception:
                    continue

        logger.info(f"Hosted video page scraped: '{headline[:60]}' ({len(body)} chars)")

        return {
            "headline": headline.replace("\n", " "),
            "body": body,
            "summary": body[:300] + "..." if len(body) > 300 else body,
            "publish_date": publish_date,
            "image_url": image_url,
            "topic": None,  # will be derived downstream
        }

    except Exception as e:
        logger.error(f"Hosted video page scraping error for {url}: {e}")
        return None


def _check_which_site(url: str, skip_age_check: bool = False):
    parse = urlparse(url).netloc.lower()

    # 1. YouTube
    if 'youtube' in parse.split('.') or 'youtu.be' in parse:
        result = scrape_video_with_ytdlp(url, skip_age_check=skip_age_check)
        if result:
            return result
        return _scrape_youtube(url)

    # 2. Straits Times — video pages first, then articles
    if 'straitstimes' in parse:
        if _is_video_url(url):                                    # ← ADD THIS
            result = scrape_video_with_ytdlp(url, skip_age_check=skip_age_check)
            if result:
                return result
            return _scrape_hosted_video_page(url)
        return scrape_straits_times(url, skip_age_check=skip_age_check)

    # 3. CNA — video pages first, then articles
    if 'channelnewsasia' in parse:
        if _is_video_url(url):                                    # ← ADD THIS
            result = scrape_video_with_ytdlp(url, skip_age_check=skip_age_check)
            if result:
                return result
            return _scrape_hosted_video_page(url)
        return scrape_cna(url, skip_age_check=skip_age_check)

    # 4. Fox News
    if 'foxnews' in parse or 'fox' in parse.split('.'):
        if _is_video_url(url):                                    # ← ADD THIS
            result = scrape_video_with_ytdlp(url, skip_age_check=skip_age_check)
            if result:
                return result
            return _scrape_hosted_video_page(url)
        return scrape_fox_news(url, skip_age_check=skip_age_check)

    # 5. Any other video page URL
    if _is_video_url(url):
        result = scrape_video_with_ytdlp(url, skip_age_check=skip_age_check)
        if result:
            return result
        return _scrape_hosted_video_page(url)

    # 6. Generic article
    result = scrape_generic_article(url, skip_age_check=skip_age_check)
    if result is None and _is_video_url(url):
        result = scrape_video_with_ytdlp(url, skip_age_check=skip_age_check)
    if result is None and _is_video_url(url):
        result = _scrape_hosted_video_page(url)
    return result
    
def _scrape_youtube(video_url: str):
    """Extract YouTube transcript with caching and retry logic."""
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
    except Exception:
        return {"error": "Invalid YouTube URL"}, 400

    cache_file = f"data/youtube_cache_{video_id}.json"
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")

    # Fetch title
    title = f"YouTube Video ({video_id})"
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        res = requests.get(video_url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = bs(res.text, "html.parser")
            title_tag = soup.title
            if title_tag and title_tag.string:
                title_text = str(title_tag.string).strip()
                title = "-".join(title_text.split("-")[:-1]).strip() if "-" in title_text else title_text
    except Exception as req_err:
        logger.warning(f"Could not fetch page title: {req_err}")

    # Fetch transcript
    max_retries = 3
    retry_delays = [3, 5, 10]
    transcript = None
    last_error = None

    for attempt in range(max_retries):
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            break
        except Exception as err:
            error_msg = str(err)
            last_error = error_msg
            if "429" in error_msg or "Too Many Requests" in error_msg:
                if attempt < max_retries - 1:
                    time.sleep(retry_delays[attempt])
                    continue
                return {
                    "error": (
                        "YouTube API rate limited. Please wait a few minutes and try again."
                    )
                }, 429
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                if transcript_list.manually_created_transcripts:
                    transcript = transcript_list.manually_created_transcripts[0].fetch()
                elif transcript_list.generated_transcripts:
                    transcript = transcript_list.generated_transcripts[0].fetch()
                else:
                    raise Exception("No transcripts available")
                break
            except Exception as alt_err:
                last_error = str(alt_err)
                if attempt < max_retries - 1:
                    time.sleep(retry_delays[attempt])

    if transcript is None:
        return {"error": f"Could not retrieve transcript: {last_error[:100]}"}, 400

    full_text = " ".join(seg["text"] for seg in transcript)
    response_data = {
        "headline": title,
        "body": full_text,
        "publish_date": None,
        "summary": None,
        "topic": None,
        "image_url": None,
    }

    try:
        os.makedirs("data", exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(response_data, f, ensure_ascii=False, indent=2)
    except Exception as cache_err:
        logger.warning(f"Failed to cache transcript: {cache_err}")

    return response_data


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def health_check():
    return {"status": "ok"}

@app.get("/scraper/")
def health_check():
    return {"status": "ok", "version": "2.0-fastapi"}


@app.get("/scraper/get-latest-articles")
def get_latest_articles(num_articles: str | None = Query(default=None)):
    count = _get_article_count(num_articles, default=30)
    try:
        cna_urls = retrieve_cna_urls(count)
        straits_urls = retrieve_straits_urls(count)
        return {"cna": cna_urls, "straits_times": straits_urls}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/scraper/get-article")
def get_article(url: str = Query(...)):
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        return JSONResponse({"error": "Invalid URL"}, status_code=400)
    result = _check_which_site(url, skip_age_check=True)  # ← True for manual requests
    if result is None:
        return JSONResponse({"error": "Could not extract article content"}, status_code=404)
    if isinstance(result, tuple):
        data, status_code = result
        return JSONResponse(data, status_code=status_code)
    return result


@app.get("/scraper/get-transcript")
def get_transcript(url: str = Query(...)):
    if not url:
        return JSONResponse({"error": "No URL provided"}, status_code=400)
    try:
        if "youtube.com" in url:
            if "/shorts/" in url:
                video_id = url.split("/shorts/")[1]
            else:
                video_id = url.split("v=")[-1]
            if "&" in video_id:
                video_id = video_id.split("&")[0]
        elif "youtu.be" in url:
            video_id = url.split("/")[-1].split("?")[0]
        else:
            return JSONResponse({"error": "Invalid YouTube URL"}, status_code=400)

        res = requests.get(url)
        soup = bs(res.text, "html.parser")
        title = str(soup.title.text)
        title = "-".join(title.split("-")[:-1])

        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join(seg["text"] for seg in transcript)
        return {"headline": title, "body": full_text}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/scraper/scrape-all-sources")
def scrape_all_sources(
    num_articles: str | None = Query(default=None),
    sg_only: bool = Query(default=False),
    async_mode: bool = Query(default=True),
):
    try:
        count = _get_article_count(num_articles, default=100)

        if async_mode:
            job_id = create_scrape_job(count, sg_only)
            return {
                "success": True,
                "job_id": job_id,
                "status": "started",
                "message": f"Background job started. Check status at /scraper/job-status/{job_id}",
            }

        # Synchronous path
        job_id = create_scrape_job(count, sg_only)
        max_wait_time = 1800
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            status = get_job_status(job_id)
            if status.get("status") == "completed":
                return {
                    "success": True,
                    "log": {
                        "timestamp": status.get("started_at"),
                        "sources_scraped": status.get("sources_scraped", []),
                        "sources_failed": status.get("sources_failed", []),
                        "total_articles": status.get("saved_articles", 0),
                        "new_articles": status.get("saved_articles", 0),
                    },
                    "csv_file": CSVHandler.CSV_FILE,
                    "message": f"Scraping complete! {status.get('saved_articles', 0)} articles saved",
                }
            if status.get("status") == "failed":
                return JSONResponse(
                    {"success": False, "error": status.get("error", "Unknown error")},
                    status_code=500,
                )
            time.sleep(2)

        status = get_job_status(job_id)
        return JSONResponse(
            {
                "success": True,
                "status": "timeout",
                "message": f"Still running after {max_wait_time}s",
                "partial_results": {
                    "saved_articles": status.get("saved_articles", 0),
                    "completed_sources": status.get("completed_sources", 0),
                },
                "job_id": job_id,
            },
            status_code=202,
        )
    except Exception as e:
        logger.error(f"Failed to run scrape job: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/scraper/job-status/{job_id}")
def job_status(job_id: str):
    try:
        return get_job_status(job_id)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/scraper/upload-to-s3")
def upload_to_s3():
    try:
        from utils.s3_uploader import S3Uploader

        s3_uploader = S3Uploader()
        result = s3_uploader.upload_csv(CSVHandler.CSV_FILE, create_backup=True)
        if result.get("success"):
            return {
                "success": True,
                "message": "Upload successful",
                "main_url": result.get("main_url"),
                "backup_url": result.get("backup_url"),
            }
        return JSONResponse({"success": False, "message": result.get("message")}, status_code=500)
    except Exception as e:
        logger.error(f"S3 upload endpoint failed: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/scraper/view-scraped-articles")
def view_scraped_articles():
    try:
        if not os.path.exists(CSVHandler.CSV_FILE):
            return {"articles": [], "count": 0}
        articles = []
        with open(CSVHandler.CSV_FILE, "r", encoding="utf-8") as f:
            articles = list(csv.DictReader(f))
        return {"articles": articles, "count": len(articles)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/scraper/article-stats")
def article_stats():
    try:
        if not os.path.exists(CSVHandler.CSV_FILE):
            return JSONResponse({"error": "No data available"}, status_code=404)
        with open(CSVHandler.CSV_FILE, "r", encoding="utf-8") as f:
            articles = list(csv.DictReader(f))
        from collections import Counter
        return {
            "total_articles": len(articles),
            "by_topic": dict(Counter(a["topic"] for a in articles)),
            "by_source": dict(Counter(a["source"] for a in articles)),
            "by_country": dict(Counter(a["country"] for a in articles)),
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/scraper/get-article-screenscraper")
def get_article_screenscraper(url: str = Query(...)):
    """Screenshot + OCR via Selenium/Tesseract."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from PIL import Image
        import pytesseract

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
            try:
                os.remove(image_name)
            except Exception:
                pass
            return {"body": extracted_text}
        except Exception as e:
            return JSONResponse({"error": f"An error occurred: {str(e)}"}, status_code=500)
        finally:
            driver.quit()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8015, reload=False)