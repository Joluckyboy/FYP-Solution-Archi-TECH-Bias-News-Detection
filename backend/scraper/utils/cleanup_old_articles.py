"""
Automatic cleanup of articles older than 7 days from CSV dataset
"""
import csv
import os
import logging
from datetime import datetime, timedelta
from utils.csv_handler import CSVHandler

logger = logging.getLogger(__name__)

MAX_ARTICLE_AGE_DAYS = 7


def cleanup_old_articles():
    """
    Remove articles older than 7 days from CSV dataset
    
    Returns:
        dict: Statistics about cleanup operation
    """
    if not os.path.exists(CSVHandler.CSV_FILE):
        logger.info("No CSV file found - nothing to clean up")
        return {'removed': 0, 'kept': 0}
    
    cutoff_date = (datetime.now() - timedelta(days=MAX_ARTICLE_AGE_DAYS)).date()
    logger.info(f"Removing articles published before {cutoff_date}")
    
    # Read all articles
    articles = []
    with open(CSVHandler.CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        articles = list(reader)
    
    # Filter out old articles
    kept_articles = []
    removed_count = 0
    
    for article in articles:
        pub_date_str = article.get('published_at', '')
        
        # Keep articles without dates (assume recent)
        if not pub_date_str:
            kept_articles.append(article)
            continue
        
        try:
            pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d").date()
            
            if pub_date >= cutoff_date:
                kept_articles.append(article)
            else:
                removed_count += 1
                logger.debug(f"Removing old article: {article.get('title', '')[:50]} ({pub_date})")
        except ValueError:
            # Keep articles with invalid dates
            kept_articles.append(article)
            logger.warning(f"Invalid date format: {pub_date_str}")
    
    # Rewrite CSV with only recent articles
    if removed_count > 0:
        with open(CSVHandler.CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSVHandler.CSV_HEADERS)
            writer.writeheader()
            writer.writerows(kept_articles)
        
        logger.info(f"🧹 Cleanup complete: Removed {removed_count} old articles, kept {len(kept_articles)}")
    else:
        logger.info(f"✓ No old articles to remove ({len(kept_articles)} articles within 7 days)")
    
    return {
        'removed': removed_count,
        'kept': len(kept_articles),
        'cutoff_date': str(cutoff_date)
    }


if __name__ == '__main__':
    # Test cleanup
    logging.basicConfig(level=logging.INFO)
    stats = cleanup_old_articles()
    print(f"Cleanup stats: {stats}")