"""
ASYNC Background task handler for long-running scraping jobs.
NOTE: Political bias classification is NOT done here.
      It is handled separately by bias-classifier ECS container
      after scraping completes and CSV is uploaded to S3.
"""
import threading
import logging
from datetime import datetime
from config.sources import SINGAPORE_SOURCES, US_SOURCES
from utils.csv_handler import CSVHandler
from scrapers.custom_scrapers import retrieve_cna_urls, retrieve_straits_urls, scrape_cna, scrape_straits_times
from scrapers.generic_scraper import scrape_generic_source
from utils.s3_uploader import S3Uploader
import os

logger = logging.getLogger(__name__)

active_jobs = {}
job_counter = 0


def create_scrape_job(num_articles=100, sg_only=False):
    for job_id, job in active_jobs.items():
        if job.get('status') == 'running':
            logger.warning(f"Job already running: {job_id}")
            return job_id

    global job_counter
    job_counter += 1
    job_id = f"job_{job_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    job_info = {
        'id': job_id,
        'status': 'running',
        'started_at': datetime.now().isoformat(),
        'progress': 0,
        'total_sources': 0,
        'completed_sources': 0,
        'total_articles': 0,
        'saved_articles': 0,
        'error': None,
        'sources_scraped': [],
        'sources_failed': []
    }

    active_jobs[job_id] = job_info

    thread = threading.Thread(
        target=_run_scrape_job,
        args=(job_id, num_articles, sg_only),
        daemon=True
    )
    thread.start()
    return job_id


def get_job_status(job_id):
    return active_jobs.get(job_id, {'status': 'not_found'})


def _run_scrape_job(job_id, num_articles, sg_only):
    """Scrape all sources, save to CSV, upload to S3."""
    try:
        job = active_jobs[job_id]

        # Restore CSV from S3 before scraping
        _restore_csv_from_s3()

        sources = SINGAPORE_SOURCES if sg_only else {**SINGAPORE_SOURCES, **US_SOURCES}

        job['total_sources'] = len(sources)
        logger.info(f"[{job_id}] Starting scrape: {len(sources)} sources, {num_articles or 'ALL'} articles each")

        for idx, (key, source) in enumerate(sources.items(), 1):
            try:
                logger.info(f"[{job_id}] Scraping {source['name']} ({idx}/{len(sources)})")
                source_articles = []

                if source['type'] == 'custom':
                    if key == 'cna':
                        urls = retrieve_cna_urls(num_articles)
                        for url in urls:
                            result = scrape_cna(url)
                            if result:
                                source_articles.append({
                                    'title': result['headline'],
                                    'source': source['name'],
                                    'url': url,
                                    'published_at': result.get('publish_date', ''),
                                    # FIX: use pre-built summary field (flat 300-char string)
                                    # instead of raw body[:300] which truncates mid-paragraph
                                    'summary': result.get('summary', ''),
                                    'image_url': result.get('image_url', ''),
                                    'country': source['country'],
                                    'topic': result.get('topic', 'General'),
                                    'political_bias': ''
                                })
                    elif key == 'straits':
                        urls = retrieve_straits_urls(num_articles)
                        for url in urls:
                            result = scrape_straits_times(url)
                            if result:
                                source_articles.append({
                                    'title': result['headline'],
                                    'source': source['name'],
                                    'url': url,
                                    'published_at': result.get('publish_date', ''),
                                    # FIX: use pre-built summary field (flat 300-char string)
                                    'summary': result.get('summary', ''),
                                    'image_url': result.get('image_url', ''),
                                    'country': source['country'],
                                    'topic': result.get('topic', 'General'),
                                    'political_bias': ''
                                })
                    else:
                        source_articles = scrape_generic_source(
                            source['url'], source['name'], source['country'], num_articles
                        )
                        for a in source_articles:
                            a['political_bias'] = ''
                else:
                    source_articles = scrape_generic_source(
                        source['url'], source['name'], source['country'], num_articles
                    )
                    for a in source_articles:
                        a['political_bias'] = ''

                if source_articles:
                    cleaned = CSVHandler.validate_and_clean_batch(source_articles)
                    saved_count = CSVHandler.append_articles(cleaned)
                    job['saved_articles'] = job.get('saved_articles', 0) + saved_count
                    logger.info(f"[{job_id}] ✓ {source['name']}: {saved_count} articles saved")
                    job['sources_scraped'].append({'name': source['name'], 'articles': saved_count})
                else:
                    logger.warning(f"[{job_id}] ⚠ {source['name']}: No articles scraped")
                    job['sources_scraped'].append({'name': source['name'], 'articles': 0})

                job['completed_sources'] = idx
                job['progress'] = int((idx / len(sources)) * 100)

            except Exception as e:
                logger.error(f"[{job_id}] Error scraping {source['name']}: {e}")
                job['sources_failed'].append({'name': source.get('name', key), 'error': str(e)})
                continue

        job['status'] = 'completed'
        job['completed_at'] = datetime.now().isoformat()
        job['progress'] = 100
        logger.info(f"[{job_id}] Scraping complete: {job['saved_articles']} articles saved")

        # Always upload to S3
        try:
            s3_uploader = S3Uploader()
            upload_result = s3_uploader.upload_csv(CSVHandler.CSV_FILE, create_backup=False)
            if upload_result.get('success'):
                job['s3_upload'] = {'status': 'success', 'main_url': upload_result.get('main_url')}
                logger.info(f"[{job_id}] ✓ S3 upload successful: {upload_result.get('main_url')}")
            else:
                job['s3_upload'] = {'status': 'failed', 'message': upload_result.get('message')}
                logger.warning(f"[{job_id}] S3 upload failed: {upload_result.get('message')}")
        except Exception as e:
            logger.error(f"[{job_id}] S3 upload error: {e}")
            job['s3_upload'] = {'status': 'failed', 'message': str(e)}

    except Exception as e:
        logger.error(f"[{job_id}] Job failed: {e}")
        job = active_jobs.get(job_id, {})
        job['status'] = 'failed'
        job['error'] = str(e)
        job['completed_at'] = datetime.now().isoformat()


def _restore_csv_from_s3():
    """Download existing CSV from S3 into local file before scraping."""
    try:
        s3_uploader = S3Uploader()
        s3_key = 'scraped_articles/scraped_articles.csv'
        os.makedirs('data', exist_ok=True)
        success = s3_uploader.download_csv(s3_key, CSVHandler.CSV_FILE)
        if success:
            with open(CSVHandler.CSV_FILE, 'r', encoding='utf-8') as f:
                count = sum(1 for _ in f) - 1  # minus header
            logger.info(f"Restored {count} existing articles from S3.")
        else:
            logger.info("No existing CSV in S3, starting fresh.")
            CSVHandler.initialize_csv()
    except Exception as e:
        logger.warning(f"Could not restore CSV from S3: {e}. Starting fresh.")
        CSVHandler.initialize_csv()