"""
ECS Task: Orchestrates scraping + political bias classification.

Calls your TWO existing services running as sidecars in the same ECS task:
  - scraper        → localhost:8015  (your scraper Flask app)
  - political-bias → localhost:9000  (your BERT bias classifier)

Flow:
  1. Wait for both sidecars to be ready
  2. Trigger scraper via POST /scraper/scrape-all-sources (async)
  3. Poll until scrape job completes (scraper uploads CSV to S3 when done)
  4. Download CSV from S3
  5. Classify any articles missing political_bias label via political-bias API
  6. Remove articles older than 7 days
  7. Re-upload final CSV to S3
  8. Container exits → ECS task stops automatically
"""

import boto3
import csv
import os
import logging
import requests
import time
from datetime import datetime, timedelta
from io import StringIO

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
BUCKET              = os.environ["S3_BUCKET"]
CSV_KEY             = "scraped_articles/scraped_articles.csv"
AWS_REGION          = os.environ.get("AWS_REGION", "ap-southeast-1")
SCRAPER_URL         = "http://localhost:8015"
BIAS_URL            = "http://localhost:9000"
MAX_AGE_DAYS        = 7


CSV_HEADERS = [
    "title", "source", "url", "published_at",
    "summary", "image_url", "country", "topic", "political_bias"
]
VALID_BIAS = {"left", "leaning-left", "center", "leaning-right", "right"}


# ── Step 1: Wait for both services ───────────────────────────────────────────
def wait_for_service(name: str, url: str, max_retries: int = 40) -> None:
    logger.info(f"Waiting for {name} at {url} ...")
    for i in range(max_retries):
        try:
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                logger.info(f"{name} is ready.")
                return
        except Exception:
            pass
        logger.info(f"  {name} not ready yet... ({i+1}/{max_retries})")
        time.sleep(10)
    raise RuntimeError(f"{name} never became ready after {max_retries * 10}s.")


def wait_for_all_services():
    # political-bias takes longer (downloads BERT model from S3)
    # scraper starts faster
    wait_for_service("scraper",        f"{SCRAPER_URL}/scraper/",          max_retries=20)
    wait_for_service("political-bias", f"{BIAS_URL}/biasengine/hello",     max_retries=60)


# ── Step 2 & 3: Trigger scraper and poll until done ──────────────────────────
def run_scrape_job() -> None:
    """
    POST /scraper/scrape-all-sources with async_mode=true.
    Poll /scraper/job-status/<job_id> until completed.
    Scraper handles its own S3 upload when done.
    """
    logger.info("Triggering scrape job on scraper service...")

    r = requests.post(
        f"{SCRAPER_URL}/scraper/scrape-all-sources",
        params={"async_mode": "true"},
        timeout=30,
    )
    r.raise_for_status()
    job_id = r.json()["job_id"]
    logger.info(f"Scrape job started: {job_id}")

    # Poll until done — max 35 minutes (70 × 30s)
    for i in range(70):
        time.sleep(30)
        try:
            status_r = requests.get(
                f"{SCRAPER_URL}/scraper/job-status/{job_id}", timeout=10
            )
            s = status_r.json()
        except Exception as e:
            logger.warning(f"Status poll error: {e}")
            continue

        status   = s.get("status")
        progress = s.get("progress", 0)
        articles = s.get("saved_articles", 0)
        elapsed  = (i + 1) * 30
        logger.info(f"[{elapsed}s] {progress}% | {articles} articles | status={status}")

        if status == "completed":
            logger.info(f"Scrape job done. {articles} articles saved to CSV.")
            return

        if status == "failed":
            raise RuntimeError(f"Scrape job failed: {s.get('error')}")

    raise RuntimeError("Scrape job timed out after 35 minutes.")


# ── Step 4: Download CSV from S3 ─────────────────────────────────────────────
def download_csv(s3) -> list[dict]:
    logger.info(f"Downloading CSV from s3://{BUCKET}/{CSV_KEY}")
    obj = s3.get_object(Bucket=BUCKET, Key=CSV_KEY)
    content = obj["Body"].read().decode("utf-8")
    articles = list(csv.DictReader(StringIO(content)))
    logger.info(f"Downloaded {len(articles)} articles.")
    return articles


# ── Step 5: Classify articles missing political_bias ─────────────────────────
def classify_article(article: dict) -> str:
    """Call political-bias sidecar. Returns valid label or empty string."""
    try:
        r = requests.get(
            f"{BIAS_URL}/biasengine/rate_bias_no_perplexity",
            params={
                "site":      article.get("source", ""),
                "title":     article.get("title", ""),
                "page_text": article.get("summary", ""),
            },
            timeout=15,
        )
        if r.status_code == 200:
            label = r.json().get("rating", "").strip().lower().replace("_", "-")
            if label in VALID_BIAS:
                return label
    except Exception as e:
        logger.debug(f"Classify error: {e}")
    return ""


def classify_all(articles: list[dict]) -> list[dict]:
    need_label = [a for a in articles if not a.get("political_bias")]
    already    = len(articles) - len(need_label)
    logger.info(f"Classifying {len(need_label)} articles ({already} already labeled).")

    labeled = 0
    for i, a in enumerate(need_label, 1):
        label = classify_article(a)
        a["political_bias"] = label
        if label:
            labeled += 1
        if i % 20 == 0:
            logger.info(f"  {i}/{len(need_label)} classified ({labeled} labeled so far)")

    logger.info(f"Classification done: {labeled}/{len(need_label)} got labels.")
    return articles


# ── Step 6: Remove articles older than 7 days ────────────────────────────────
def remove_old_articles(articles: list[dict]) -> list[dict]:
    cutoff = (datetime.now() - timedelta(days=MAX_AGE_DAYS)).date()
    kept, removed = [], 0
    for a in articles:
        pub = a.get("published_at", "")
        if not pub:
            kept.append(a)
            continue
        try:
            if datetime.strptime(pub[:10], "%Y-%m-%d").date() >= cutoff:
                kept.append(a)
            else:
                removed += 1
        except Exception:
            kept.append(a)
    logger.info(f"Cleanup: removed {removed} old articles, kept {len(kept)}.")
    return kept


# ── Step 7: Upload final CSV to S3 ───────────────────────────────────────────
def upload_csv(s3, articles: list[dict]) -> None:
    out = StringIO()
    writer = csv.DictWriter(out, fieldnames=CSV_HEADERS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(articles)
    s3.put_object(
        Bucket=BUCKET,
        Key=CSV_KEY,
        Body=out.getvalue().encode("utf-8"),
        ContentType="text/csv",
    )
    logger.info(f"Uploaded {len(articles)} articles → s3://{BUCKET}/{CSV_KEY}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    logger.info("=" * 60)
    logger.info("ECS DAILY SCRAPE + CLASSIFY TASK")
    logger.info(f"  Scraper:   {SCRAPER_URL}")
    logger.info(f"  Bias API:  {BIAS_URL}")
    logger.info(f"  S3 bucket: {BUCKET}")
    logger.info("=" * 60)

    # 1. Wait for both sidecars to be ready
    wait_for_all_services()

    s3 = boto3.client("s3", region_name=AWS_REGION)

    # 2 & 3. Trigger scraper job, wait until scraper uploads CSV to S3
    run_scrape_job()

    # 4. Download the freshly scraped CSV from S3
    articles = download_csv(s3)

    # 5. Classify articles missing political_bias
    articles = classify_all(articles)

    # 6. Remove articles older than 7 days
    articles = remove_old_articles(articles)

    # 7. Upload final classified + cleaned CSV back to S3
    upload_csv(s3, articles)

    logger.info("=" * 60)
    logger.info("Task complete. Container will now exit.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()