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


def _is_lxml_compat_error(e: Exception) -> bool:
    """
    Detect the newspaper3k/lxml 5.x incompatibility error.

    lxml 5.x removed the `attrs` keyword argument from find().
    This error can surface in multiple ways:
      - TypeError: find() got an unexpected keyword argument 'attrs'
      - The error message may contain a Unicode word-joiner (U+2060) before 'find()'
        which prevents naive string matching on 'unexpected keyword argument' alone.

    We therefore check for both the keyword and the function name.
    """
    msg = str(e)
    return "unexpected keyword argument" in msg or (
        "find()" in msg and "keyword argument" in msg
    )


def scrape_generic_article(url, skip_age_check=False):
    """Scrape a single article using newspaper3k with DATE FILTERING"""
    try:
        article = Article(url)
        article.download()
        article.parse()

    except Exception as e:
        if _is_lxml_compat_error(e):
            logger.warning(f"newspaper3k lxml compat error (parse stage) for {url}, trying BS4 fallback")
            return _scrape_with_bs4_fallback(url, skip_age_check)
        logger.error(f"Generic scraping error for {url}: {e}")
        return None

    try:
        # DATE FILTERING
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
        
        is_video_page = '/video/' in url or '/videos/' in url
        min_length = 30 if is_video_page else 100

        if not body or len(body.strip()) < min_length:
            # For video pages, try to extract description from BeautifulSoup as fallback
            if is_video_page:
                try:
                    import requests as _requests
                    from bs4 import BeautifulSoup as bs
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    res = _requests.get(url, headers=headers, timeout=10)
                    soup = bs(res.content, "html.parser")

                    # Try og:description first (most reliable for video pages)
                    og_desc = soup.find("meta", property="og:description")
                    if og_desc and og_desc.get("content"):
                        body = og_desc["content"].strip()

                    # Then try all <p> tags
                    if not body or len(body) < 30:
                        paras = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 20]
                        body = " ".join(paras)

                    # Try the page title + description as last resort
                    if not body or len(body) < 30:
                        og_title = soup.find("meta", property="og:title")
                        if og_title and og_title.get("content"):
                            body = og_title["content"].strip()

                    if not body or len(body) < 10:
                        logger.warning(f"Video page: could not extract any content from {url}")
                        return None

                    logger.info(f"Video page fallback extraction: {len(body)} chars from {url}")

                    # Re-extract headline for video pages if newspaper3k missed it
                    if not headline or headline == url:
                        og_title = soup.find("meta", property="og:title")
                        headline = og_title["content"].strip() if og_title and og_title.get("content") else headline

                except Exception as e:
                    logger.warning(f"Video page fallback failed for {url}: {e}")
                    return None
            else:
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
        
        # FIXED: wrap top_node access in its own try/except so lxml errors here
        # also route to the BS4 fallback instead of returning None silently.
        try:
            topic = derive_topic_from_metadata(url, soup=article.top_node, 
                                              text=f"{headline} {body}", 
                                              keywords=article.keywords)
        except Exception as e:
            if _is_lxml_compat_error(e):
                logger.warning(f"newspaper3k lxml compat error (top_node) for {url}, using text-only topic")
            # Fall back to text-only topic derivation (no soup)
            topic = derive_topic_from_metadata(url, soup=None,
                                              text=f"{headline} {body}",
                                              keywords=article.keywords)
        
        return {
            "headline": headline.strip().replace("\n", " "),
            "body": body.strip().replace("\n", " "),
            "publish_date": publish_date,
            "topic": topic
        }

    except Exception as e:
        if _is_lxml_compat_error(e):
            logger.warning(f"newspaper3k lxml compat error (post-parse) for {url}, trying BS4 fallback")
            return _scrape_with_bs4_fallback(url, skip_age_check)
        logger.error(f"Generic scraping error for {url}: {e}")
        return None

    
def _scrape_with_bs4_fallback(url: str, skip_age_check: bool = False) -> dict | None:
    """
    Direct BeautifulSoup scraper used when newspaper3k fails.
    Handles CNN, NPR, Yahoo Finance, and most standard news layouts.
    """
    try:
        import requests as _requests
        from bs4 import BeautifulSoup as bs

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        res = _requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200:
            logger.warning(f"BS4 fallback: HTTP {res.status_code} for {url}")
            return None

        soup = bs(res.content, "html.parser")

        # ── Headline ──────────────────────────────────────────────────
        headline = ""
        for selector in [
            soup.find("h1"),
            soup.find("meta", property="og:title"),
        ]:
            if selector:
                headline = selector.get("content", "") or selector.get_text(strip=True)
                if headline:
                    break
        if not headline:
            return None

        # ── Publish date ──────────────────────────────────────────────
        publish_date = None
        # Try <time> tag
        time_elem = soup.find("time")
        if time_elem and time_elem.get("datetime"):
            try:
                date_obj = datetime.fromisoformat(
                    time_elem["datetime"].replace('Z', '+00:00')
                )
                now_ref = datetime.now(date_obj.tzinfo) if date_obj.tzinfo else datetime.now()
                if date_obj.date() > now_ref.date():
                    logger.debug(f"BS4 fallback: future article skipped: {url}")
                    return None
                article_age = (datetime.now() - date_obj.replace(tzinfo=None)).days
                if not skip_age_check and article_age > MAX_ARTICLE_AGE_DAYS:
                    logger.debug(f"BS4 fallback: old article ({article_age}d) skipped: {url}")
                    return None
                publish_date = date_obj.strftime("%Y-%m-%d")
            except Exception:
                pass

        # Try og:article:published_time meta
        if not publish_date:
            pub_meta = soup.find("meta", property="article:published_time")
            if pub_meta and pub_meta.get("content"):
                try:
                    date_obj = datetime.fromisoformat(
                        pub_meta["content"].replace('Z', '+00:00')
                    )
                    publish_date = date_obj.strftime("%Y-%m-%d")
                except Exception:
                    pass

        # ── Body text ─────────────────────────────────────────────────
        body = ""

        # Strategy 1: known article body containers
        for container_attrs in [
            {"class": "article__content"},           # CNN
            {"class": "storytext"},                  # NPR
            {"class": "caas-body"},                  # Yahoo Finance/News
            {"class": "article-body"},
            {"class": "post-content"},
            {"id": "article-body"},
            {"role": "article"},
        ]:
            container = soup.find(True, container_attrs)
            if container:
                paras = container.find_all("p")
                if paras:
                    body = "\n\n".join(
                        p.get_text(separator=" ", strip=True)
                        for p in paras
                        if len(p.get_text(strip=True)) > 20
                    )
                    if len(body) > 200:
                        break

        # Strategy 2: all <p> tags outside nav/header/footer
        if len(body) < 200:
            all_paras = soup.find_all("p")
            content_paras = [
                p for p in all_paras
                if not p.find_parent(["nav", "header", "footer", "aside"])
                and len(p.get_text(strip=True)) > 30
            ]
            body = "\n\n".join(
                p.get_text(separator=" ", strip=True) for p in content_paras
            )

        # Strategy 3: og:description as last resort
        if len(body) < 100:
            og_desc = soup.find("meta", property="og:description")
            if og_desc and og_desc.get("content"):
                body = og_desc["content"].strip()

        if not body or len(body) < 50:
            logger.warning(f"BS4 fallback: insufficient content from {url}")
            return None

        body = clean_boilerplate(body, preserve_paragraphs=True)

        if not is_english_text(body):
            logger.warning(f"BS4 fallback: non-English content: {url}")
            return None

        # ── Image ─────────────────────────────────────────────────────
        image_url = ""
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            image_url = og_image["content"]

        topic = derive_topic_from_metadata(
            url=url, soup=soup, text=f"{headline} {body}"
        )

        logger.info(f"BS4 fallback succeeded: '{headline[:60]}' ({len(body)} chars)")

        return {
            "headline": headline.strip().replace("\n", " "),
            "body": body.strip(),
            "publish_date": publish_date,
            "image_url": image_url,
            "topic": topic,
        }

    except Exception as e:
        logger.error(f"BS4 fallback failed for {url}: {e}")
        return None