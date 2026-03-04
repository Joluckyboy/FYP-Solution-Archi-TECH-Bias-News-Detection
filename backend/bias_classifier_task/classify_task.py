"""
ECS Task: Orchestrates scraping + political bias classification + clustering.

Sidecars in the same ECS task (all on localhost):
  - scraper        → localhost:8015
  - political-bias → localhost:9000
  - analyzer       → localhost:8017

Flow:
  1. Wait for all 3 sidecars to be ready
  2. Trigger scraper via POST /scraper/scrape-all-sources (async)
  3. Poll until scrape job completes
  4. Download CSV from S3
  5. Classify articles missing political_bias label
  6. Remove articles older than 7 days
  7. Upload cleaned CSV to S3
  8. POST localhost:8017/dashboard/cluster
     → analyzer downloads fresh CSV from S3, clusters articles,
       writes cluster_id to every row, re-uploads enriched CSV to S3
  9. bias-classifier exits → ECS stops all sidecars automatically
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
BUCKET       = os.environ["S3_BUCKET"]
CSV_KEY      = "scraped_articles/scraped_articles.csv"
AWS_REGION   = os.environ.get("AWS_REGION", "ap-southeast-1")
SCRAPER_URL  = "http://localhost:8015"
BIAS_URL     = "http://localhost:9000"
ANALYZER_URL = "http://localhost:8017"
MAX_AGE_DAYS = 7

CSV_HEADERS = [
    "title", "source", "url", "published_at",
    "summary", "image_url", "country", "topic", "political_bias",
]
VALID_BIAS = {"left", "leaning-left", "center", "leaning-right", "right"}


# ── Step 1: Wait for all sidecars ─────────────────────────────────────────────
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


def wait_for_all_services() -> None:
    wait_for_service("scraper",        f"{SCRAPER_URL}/scraper/",      max_retries=20)
    wait_for_service("political-bias", f"{BIAS_URL}/biasengine/hello", max_retries=60)
    # Analyzer takes longer — loads sentence-transformers model on startup
    wait_for_service("analyzer",       f"{ANALYZER_URL}/health",       max_retries=40)


# ── Step 2 & 3: Trigger scraper, poll until done ──────────────────────────────
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

    for i in range(70):  # max 35 min
        time.sleep(30)
        try:
            s = requests.get(
                f"{SCRAPER_URL}/scraper/job-status/{job_id}", timeout=10
            ).json()
        except Exception as e:
            logger.warning(f"Status poll error: {e}")
            continue

        status   = s.get("status")
        progress = s.get("progress", 0)
        articles = s.get("saved_articles", 0)
        logger.info(
            f"[{(i+1)*30}s] {progress}% | {articles} articles | status={status}"
        )

        if status == "completed":
            logger.info(f"Scrape job done. {articles} articles saved to CSV.")
            return

        if status == "failed":
            raise RuntimeError(f"Scrape job failed: {s.get('error')}")

    raise RuntimeError("Scrape job timed out after 35 minutes.")


# ── Step 4: Download CSV from S3 ──────────────────────────────────────────────
def download_csv(s3) -> list[dict]:
    logger.info(f"Downloading CSV from s3://{BUCKET}/{CSV_KEY}")
    obj = s3.get_object(Bucket=BUCKET, Key=CSV_KEY)
    articles = list(csv.DictReader(StringIO(obj["Body"].read().decode("utf-8"))))
    logger.info(f"Downloaded {len(articles)} articles.")
    return articles


# ── Step 5: Classify missing political_bias ───────────────────────────────────
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
    logger.info(
        f"Classifying {len(need_label)} articles ({already} already labeled)."
    )
    labeled = 0
    for i, a in enumerate(need_label, 1):
        label = classify_article(a)
        a["political_bias"] = label
        if label:
            labeled += 1
        if i % 20 == 0:
            logger.info(
                f"  {i}/{len(need_label)} classified ({labeled} labeled so far)"
            )
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
            # Try multiple date formats
            pub_date = None
            for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y"]:
                try:
                    pub_date = datetime.strptime(pub.strip(), fmt).date()
                    break
                except ValueError:
                    continue
            if pub_date is None:
                # Unable to parse date, keep article
                kept.append(a)
                logger.debug(f"Unable to parse date '{pub}', keeping article")
            elif pub_date >= cutoff:
                kept.append(a)
            else:
                removed += 1
        except Exception as e:
            kept.append(a)
            logger.warning(f"Error processing date '{pub}': {e}")
    logger.info(f"Cleanup: removed {removed} old articles, kept {len(kept)}.")
    return kept


# ── Step 7: Upload cleaned CSV to S3 ─────────────────────────────────────────
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


# ── Step 8: Tell analyzer sidecar to cluster and re-upload CSV ───────────────
def trigger_clustering() -> None:
    logger.info("Triggering clustering on analyzer sidecar...")
    r = requests.post(
        f"{ANALYZER_URL}/dashboard/cluster",
        timeout=600,  # clustering large CSVs can take a few minutes
    )
    r.raise_for_status()
    result = r.json()
    logger.info(
        f"Clustering done: {result.get('clusters')} clusters "
        f"from {result.get('articles')} articles."
    )


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    logger.info("=" * 60)
    logger.info("ECS TASK: SCRAPE + CLASSIFY + CLUSTER")
    logger.info(f"  Scraper:      {SCRAPER_URL}")
    logger.info(f"  Bias API:     {BIAS_URL}")
    logger.info(f"  Analyzer:     {ANALYZER_URL}")
    logger.info(f"  S3 bucket:    {BUCKET}")
    logger.info("=" * 60)

    # 1. Wait for all 3 sidecars to be ready
    wait_for_all_services()

    s3 = boto3.client("s3", region_name=AWS_REGION)

    # 2 & 3. Scrape
    run_scrape_job()

    # 4. Download fresh CSV
    articles = download_csv(s3)

    # 5. Classify political bias
    articles = classify_all(articles)

    # 6. Remove old articles
    articles = remove_old_articles(articles)

    # 7. Upload cleaned CSV to S3
    upload_csv(s3, articles)

    # 8. Analyzer clusters + re-uploads CSV with cluster_id
    trigger_clustering()

    logger.info("=" * 60)
    logger.info("Task complete. Container will now exit.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()