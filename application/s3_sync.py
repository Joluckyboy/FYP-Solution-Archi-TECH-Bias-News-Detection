"""
S3 sync utility - downloads scraped_articles.csv from S3 every 12 hours.

Caching strategy: re-download only if local file is missing OR older than 12 hours.
This syncs with the daily ECS Fargate scraping schedule:
    - ECS runs at 12am → uploads cleaned CSV to S3
    - Within 12h → re-downloads fresh CSV automatically
"""
import os
import time
import logging

logger = logging.getLogger(__name__)

# Environment variables
S3_BUCKET = os.getenv("S3_BUCKET")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
S3_DOWNLOAD_ENABLED = os.getenv("SCRAPER_S3_SYNC", "true").lower() == "true"
SCRAPER_DATA_DIR = os.getenv("SCRAPER_DATA_DIR", "/app/data")
SCRAPED_CSV_PATH = os.path.join(SCRAPER_DATA_DIR, "scraped_articles.csv")

# S3 key for the scraped articles CSV
S3_KEY = os.getenv("SCRAPER_S3_KEY", "scraped_articles/scraped_articles.csv")

# Re-download every 12 hours — catches the 12am ECS upload by 3am
CACHE_TTL_HOURS = 12


def ensure_scraped_csv():
    """
    Downloads scraped_articles.csv from S3 if:
      1. File does not exist locally, OR
      2. File is older than 12 hours (CACHE_TTL_HOURS)

    This syncs with the daily ECS Fargate scraping schedule:
      - ECS runs at 12am → uploads cleaned CSV to S3
      - Within 12h → re-downloads fresh CSV automatically
      - 2 S3 GETs per day
    """
    os.makedirs(SCRAPER_DATA_DIR, exist_ok=True)

    # If S3 sync is disabled, fall back to local file
    if not S3_DOWNLOAD_ENABLED:
        if os.path.exists(SCRAPED_CSV_PATH):
            file_size = os.path.getsize(SCRAPED_CSV_PATH)
            logger.warning(
                f"SCRAPER_S3_SYNC=false, using existing local file "
                f"({file_size:,} bytes): {SCRAPED_CSV_PATH}"
            )
        else:
            logger.warning(
                f"SCRAPER_S3_SYNC=false and no local file at {SCRAPED_CSV_PATH}"
            )
        return

    # Check if S3 bucket is configured
    if not S3_BUCKET:
        logger.warning("S3_BUCKET not set — cannot download scraped CSV.")
        if os.path.exists(SCRAPED_CSV_PATH):
            logger.warning("Falling back to existing local file.")
        return

    # Check if local file exists and is fresh enough (within 12 hours)
    if os.path.exists(SCRAPED_CSV_PATH):
        file_age_seconds = time.time() - os.path.getmtime(SCRAPED_CSV_PATH)
        file_age_hours = file_age_seconds / 3600

        if file_age_hours < CACHE_TTL_HOURS:
            file_size = os.path.getsize(SCRAPED_CSV_PATH)
            logger.info(
                f"CSV is {file_age_hours:.1f}h old (< {CACHE_TTL_HOURS}h), "
                f"using local cache ({file_size:,} bytes). Skipping S3 download."
            )
            return
        else:
            logger.info(
                f"CSV is {file_age_hours:.1f}h old (>= {CACHE_TTL_HOURS}h). "
                f"Re-downloading from S3..."
            )

    # Import boto3
    try:
        import boto3
    except ImportError:
        logger.error("boto3 not installed — cannot download from S3.")
        return

    # Download fresh copy from S3
    try:
        logger.info(f"Downloading latest CSV from S3...")
        logger.info(f"  Bucket : {S3_BUCKET}")
        logger.info(f"  Key    : {S3_KEY}")
        logger.info(f"  Local  : {SCRAPED_CSV_PATH}")

        s3_client = boto3.client("s3", region_name=AWS_REGION)
        s3_client.download_file(S3_BUCKET, S3_KEY, SCRAPED_CSV_PATH)

        file_size = os.path.getsize(SCRAPED_CSV_PATH)
        logger.info(
            f"✓ Downloaded fresh CSV from S3 "
            f"({file_size:,} bytes) → {SCRAPED_CSV_PATH}"
        )

    except Exception as e:
        # Check for NoSuchKey specifically
        error_code = ""
        if hasattr(e, "response") and isinstance(e.response, dict):
            error_code = e.response.get("Error", {}).get("Code", "")

        if error_code == "NoSuchKey":
            logger.warning(
                f"Scraped CSV not found in S3: s3://{S3_BUCKET}/{S3_KEY}. "
                "The ECS scraper task may not have run yet."
            )
        else:
            logger.error(f"Failed to download scraped CSV from S3: {e}")

        # Fall back to existing local file if available
        if os.path.exists(SCRAPED_CSV_PATH):
            file_size = os.path.getsize(SCRAPED_CSV_PATH)
            logger.warning(
                f"Using existing local file as fallback "
                f"({file_size:,} bytes): {SCRAPED_CSV_PATH}"
            )
        else:
            logger.error(
                "No local fallback available. Dashboard will return empty data."
            )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ensure_scraped_csv()