"""
ASYNC Background task handler for long-running scraping jobs
Use this instead of synchronous endpoint to avoid gunicorn timeouts
"""
import threading
import logging
from datetime import datetime
from config.sources import SINGAPORE_SOURCES, US_SOURCES
from utils.csv_handler import CSVHandler
from utils.bias_classifier import classify_political_bias
from scrapers.custom_scrapers import retrieve_cna_urls, retrieve_straits_urls, scrape_cna, scrape_straits_times
from scrapers.generic_scraper import scrape_generic_source

logger = logging.getLogger(__name__)

# Global job tracking
active_jobs = {}
job_counter = 0


def create_scrape_job(num_articles=100, sg_only=False):
    """Create and start a background scraping job"""
    # Check if another job is already running
    for job_id, job in active_jobs.items():
        if job.get('status') == 'running':
            logger.warning(f"Job already running: {job_id}")
            return job_id  # Return existing job ID
    
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
        # ADDED: Track detailed scraping log (like original app_old.py)
        'sources_scraped': [],
        'sources_failed': []
    }
    
    active_jobs[job_id] = job_info
    
    # Start background thread
    thread = threading.Thread(
        target=_run_scrape_job,
        args=(job_id, num_articles, sg_only),
        daemon=True
    )
    thread.start()
    
    return job_id


def get_job_status(job_id):
    """Get status of a scraping job"""
    return active_jobs.get(job_id, {'status': 'not_found'})


def _run_scrape_job(job_id, num_articles, sg_only):
    """Background worker function"""
    try:
        job = active_jobs[job_id]
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
                                    'summary': result.get('body', '')[:300],
                                    'image_url': result.get('image_url', ''),
                                    'country': source['country'],
                                    'topic': result.get('topic', 'General')
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
                                    'summary': result.get('body', '')[:300],
                                    'image_url': result.get('image_url', ''),
                                    'country': source['country'],
                                    'topic': result.get('topic', 'General')
                                })
                    
                    else:  # foxnews
                        source_articles = scrape_generic_source(source['url'], source['name'], 
                                                       source['country'], num_articles)
                
                else:  # generic source
                    source_articles = scrape_generic_source(source['url'], source['name'], 
                                                   source['country'], num_articles)
                
                # Save after each source completes
                if source_articles:
                    classified_articles = []
                    for article in source_articles:
                        bias_label = classify_political_bias(article)
                        if not bias_label:
                            logger.warning(f"[{job_id}] Skipping article without bias label: {article.get('title', '')[:80]}")
                            continue
                        article['political_bias'] = bias_label
                        classified_articles.append(article)

                    cleaned = CSVHandler.validate_and_clean_batch(classified_articles)
                    saved_count = CSVHandler.append_articles(cleaned)
                    job['saved_articles'] = job.get('saved_articles', 0) + saved_count
                    logger.info(f"[{job_id}] ✓ {source['name']}: {saved_count} articles saved to CSV")
                    
                    # ADDED: Track detailed source info (like original app_old.py)
                    job['sources_scraped'].append({
                        'name': source['name'],
                        'articles': saved_count
                    })
                else:
                    logger.warning(f"[{job_id}] ⚠ {source['name']}: No articles scraped")
                    job['sources_scraped'].append({
                        'name': source['name'],
                        'articles': 0
                    })
                
                job['completed_sources'] = idx
                job['progress'] = int((idx / len(sources)) * 100)
            
            except Exception as e:
                logger.error(f"[{job_id}] Error scraping {source['name']}: {e}")
                # ADDED: Track failed sources (like original app_old.py)
                job['sources_failed'].append({
                    'name': source.get('name', key),
                    'error': str(e)
                })
                continue
        
        job['status'] = 'completed'
        job['completed_at'] = datetime.now().isoformat()
        job['progress'] = 100
        
        logger.info(f"[{job_id}] Job complete: {job['saved_articles']} total articles saved")
    
    except Exception as e:
        logger.error(f"[{job_id}] Job failed: {e}")
        job = active_jobs.get(job_id, {})
        job['status'] = 'failed'
        job['error'] = str(e)
        job['completed_at'] = datetime.now().isoformat()
