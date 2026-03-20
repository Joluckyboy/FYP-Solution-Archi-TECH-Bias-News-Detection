"""
Generic scraper using newspaper3k with timeout protection and DATE FILTERING
"""
import newspaper
import logging
from datetime import datetime, timedelta
from newspaper import Article, Config
from utils.text_processing import clean_boilerplate, is_english_text, smart_truncate
from utils.topic_classifier import derive_topic_from_metadata
from utils.timeout_handler import download_and_parse_article

logger = logging.getLogger(__name__)

# CRITICAL: Only scrape articles from last 7 days
MAX_ARTICLE_AGE_DAYS = 7


def scrape_generic_source(source_url: str, source_name: str, country: str, 
                         num_articles: int | None = None) -> list:
    """Scrape articles from generic sources using newspaper3k with timeout protection and DATE FILTERING"""
    articles = []
    
    try:
        config = Config()
        config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        config.request_timeout = 10
        config.number_threads = 1
        config.fetch_images = True
        
        logger.info(f"Building newspaper for {source_name}...")
        
        try:
            paper = newspaper.build(source_url, config=config, memoize_articles=False)
        except Exception as build_error:
            logger.error(f"Failed to build newspaper for {source_name}: {build_error}")
            return articles
        
        total_available = len(paper.articles)
        logger.info(f"Found {total_available} articles for {source_name}")
        
        article_count = 0
        timeout_count = 0
        consecutive_timeouts = 0
        max_consecutive_timeouts = 20  # INCREASED from 5 to allow more articles despite timeouts
        seen_summaries = set()
        failed_count = 0
        max_total_failures = 20
        old_articles_skipped = 0  # NEW: Track old articles
        
        # Determine article stream
        if num_articles is None:
            article_stream = paper.articles
            logger.info(f"Scraping ALL {total_available} articles from {source_name}")
        else:
            article_stream = paper.articles[:num_articles * 2]
            logger.info(f"Attempting to scrape {num_articles} articles from {source_name}")
        
        for article_obj in article_stream:
            if num_articles and article_count >= num_articles:
                break
            
            if consecutive_timeouts >= max_consecutive_timeouts:
                logger.warning(f"⚠️  Stopping {source_name}: {max_consecutive_timeouts} consecutive timeouts")
                break
            
            try:
                result = download_and_parse_article(article_obj, config, timeout_seconds=10)
                
                if result is None:
                    timeout_count += 1
                    consecutive_timeouts += 1
                    continue
                
                consecutive_timeouts = 0
                
                # Skip insufficient content
                if not result.title or not result.text or len(result.text) < 100:
                    failed_count += 1
                    continue
                
                # NEW: DATE FILTERING - Skip old articles
                if result.publish_date:
                    try:
                        now_ref = datetime.now(result.publish_date.tzinfo) if result.publish_date.tzinfo else datetime.now()
                        if result.publish_date.date() > now_ref.date():
                            logger.debug(f"Skipping future-dated article: {result.title[:50]}")
                            continue

                        article_age = datetime.now() - result.publish_date
                        if article_age.days > MAX_ARTICLE_AGE_DAYS:
                            old_articles_skipped += 1
                            logger.debug(f"Skipping old article ({article_age.days} days): {result.title[:50]}")
                            continue
                    except Exception as date_error:
                        logger.debug(f"Date parsing error: {date_error}")
                        # Skip articles with unparseable dates (can't verify they're recent)
                        failed_count += 1
                        continue
                else:
                    # No date found: assume recent (scraped today, so likely recent)
                    # Better to include borderline articles than exclude all undated ones
                    logger.debug(f"No date found for article: {result.title[:50]} (assuming recent)")
                    pass
                
                # Skip non-English
                if not is_english_text(result.text):
                    failed_count += 1
                    continue
                
                # Skip paywall/error content
                text_lower = result.text.lower().strip()
                failure_indicators = ['subscribe', 'sign in', 'log in', '403', '404', 
                                    'access denied', 'continue reading', 'read more',
                                    'enable javascript', 'cookies', 'please disable', 'ad blocker']
                if (len(result.text.split()) < 20 or 
                    (len(result.text.split()) < 50 and 
                     any(indicator in text_lower for indicator in failure_indicators))):
                    failed_count += 1
                    continue
                
                # Skip non-ASCII titles for NYT
                if 'nytimes' in source_url and not result.title.isascii():
                    failed_count += 1
                    continue
                
                title = result.title.strip()
                cleaned_text = clean_boilerplate(result.text, preserve_paragraphs=True)
                summary = smart_truncate(cleaned_text, 300)
                
                # Skip duplicate summaries
                if summary in seen_summaries:
                    failed_count += 1
                    continue
                seen_summaries.add(summary)
                
                image_url = result.top_image or ""
                
                published_at = datetime.now().strftime("%Y-%m-%d")
                if result.publish_date:
                    try:
                        published_at = result.publish_date.strftime("%Y-%m-%d")
                    except:
                        pass
                
                topic = derive_topic_from_metadata(url=article_obj.url, 
                                                  soup=result.top_node,
                                                  keywords=result.keywords,
                                                  text=f"{title} {summary}")
                
                articles.append({
                    'title': title,
                    'source': source_name,
                    'url': article_obj.url,
                    'published_at': published_at,
                    'summary': summary,
                    'image_url': image_url,
                    'country': country,
                    'topic': topic
                })
                
                article_count += 1
                
            except Exception as e:
                logger.debug(f"Error processing article: {str(e)[:50]}")
                continue
        
        success_msg = f"{source_name}: {article_count} recent articles scraped"
        if timeout_count > 0:
            success_msg += f" ({timeout_count} timeouts)"
        if old_articles_skipped > 0:
            success_msg += f" ({old_articles_skipped} old articles skipped)"
        logger.info(success_msg)
                
    except Exception as e:
        logger.error(f"Error with {source_name}: {str(e)[:100]}")
    
    return articles


def scrape_generic_article(url, skip_age_check=False):
    """Scrape a single article using newspaper3k with DATE FILTERING"""
    try:
        article = Article(url)
        article.download()
        article.parse()
        
        # NEW: DATE FILTERING
        if article.publish_date:
            try:
                now_ref = datetime.now(article.publish_date.tzinfo) if article.publish_date.tzinfo else datetime.now()
                if article.publish_date.date() > now_ref.date():
                    logger.warning(f"Future-dated article skipped: {url}")
                    return None

                if not skip_age_check and article.publish_date:
                    article_age = datetime.now() - article.publish_date.replace(tzinfo=None)
                    if article_age.days > MAX_ARTICLE_AGE_DAYS:
                        logger.warning(f"Article too old ({article_age.days} days): {url}")
                        return None
            except Exception as date_error:
                logger.debug(f"Date parsing error: {date_error}")
                # Continue if date parsing fails
        
        publish_date = article.publish_date.strftime("%Y-%m-%d") if article.publish_date else None
        body = article.text
        headline = article.title
        
        if not body or len(body.strip()) < 100:
            logger.warning(f"newspaper3k insufficient content: {url}")
            return None
        
        body = clean_boilerplate(body, preserve_paragraphs=True)
        
        if not is_english_text(body):
            logger.warning(f"Non-English content: {url}")
            return None
        
        # Check for paywall/error
        body_lower = body.lower().strip()
        failure_indicators = ['subscribe', 'sign in', 'log in', '403', '404', 
                            'access denied', 'continue reading', 'read more', 'enable javascript']
        if (len(body_lower.split()) < 20 or 
            any(indicator in body_lower for indicator in failure_indicators)):
            logger.warning(f"Paywall/error detected: {body_lower[:80]}")
            return None
        
        topic = derive_topic_from_metadata(url, soup=article.top_node, 
                                          text=f"{headline} {body}", 
                                          keywords=article.keywords)
        
        return {
            "headline": headline.strip().replace("\n", " "),
            "body": body.strip().replace("\n", " "),
            "publish_date": publish_date,
            "topic": topic
        }
    except Exception as e:
        logger.error(f"Generic scraping error for {url}: {e}")
        return None