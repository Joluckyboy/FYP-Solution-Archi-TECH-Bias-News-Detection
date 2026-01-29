"""
Custom scrapers for specific news sources (CNA, Straits Times, Fox News) with DATE FILTERING
"""
import requests
import logging
from bs4 import BeautifulSoup as bs
from datetime import datetime, timedelta
from urllib.parse import urljoin
from utils.text_processing import clean_boilerplate, is_english_text
from utils.topic_classifier import derive_topic_from_metadata

logger = logging.getLogger(__name__)

# CRITICAL: Only scrape articles from last 7 days
MAX_ARTICLE_AGE_DAYS = 7


def retrieve_straits_urls(specified_length: int | None):
    """Retrieve Straits Times article URLs"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        base_url = "https://www.straitstimes.com"
        res = requests.get(f"{base_url}/singapore", headers=headers, timeout=15)
        res.raise_for_status()
        soup = bs(res.content, "html.parser")
        
        article_urls = []
        
        # Method 1: Article cards
        article_cards = soup.find_all("div", class_="card")
        for card in article_cards:
            if specified_length is not None and len(article_urls) >= specified_length:
                break
            a_tag = card.find("a", href=True)
            if a_tag:
                href = a_tag.get("href")
                if href and href.startswith("/"):
                    article_urls.append(f"{base_url}{href}")
        
        # Method 2: All /singapore/ links
        if specified_length is None or len(article_urls) < specified_length:
            all_links = soup.find_all("a", href=True)
            for a_tag in all_links:
                if specified_length is not None and len(article_urls) >= specified_length:
                    break
                href = a_tag.get("href", "")
                if "/singapore/" in href and href.startswith("/"):
                    full_url = f"{base_url}{href}"
                    if full_url not in article_urls:
                        article_urls.append(full_url)
        
        logger.info(f"Retrieved {len(article_urls)} Straits Times URLs")
        return article_urls
        
    except Exception as e:
        logger.error(f"Straits Times URL retrieval error: {e}")
        return []


def retrieve_cna_urls(specified_length: int | None):
    """Retrieve CNA article URLs"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        base_url = "https://www.channelnewsasia.com"
        res = requests.get(f"{base_url}/singapore", headers=headers, timeout=10)
        soup = bs(res.content, "html.parser")
        
        article_anchors = soup.find_all("a", class_="list-object__heading-link")
        
        article_urls = []
        for a_tag in article_anchors:
            if specified_length is not None and len(article_urls) >= specified_length:
                break
            if a_tag and a_tag.get("href"):
                relative_url = a_tag.get("href")
                absolute_url = urljoin(base_url, relative_url)
                article_urls.append(absolute_url)
        
        logger.info(f"Retrieved {len(article_urls)} CNA URLs")
        return article_urls
    except Exception as e:
        logger.error(f"CNA URL retrieval error: {e}")
        return []


def scrape_straits_times(url):
    """Scrape Straits Times article with DATE FILTERING"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(url, headers=headers, timeout=10)
        soup = bs(res.content, "html.parser")
        
        # Extract headline
        headline_elem = (soup.find("h1", class_="headline") or soup.find("h1") or
                        soup.find("div", {"data-testid": "article-title"}))
        headline = headline_elem.text.strip() if headline_elem else "Headline not found"
        
        # Extract body
        body = ""
        article_body = soup.find("div", class_="article-body")
        if article_body:
            body_paras = article_body.find_all("p")
            body = " ".join([p.get_text(strip=True) for p in body_paras])
        
        if not body or len(body) < 100:
            body_paras = soup.find_all("p", class_="paragraph-base")
            if body_paras:
                body = " ".join([p.get_text(strip=True) for p in body_paras])
        
        if not body or len(body) < 100:
            all_paras = soup.find_all("p")
            content_paras = [p for p in all_paras 
                           if not p.find_parent(["nav", "header", "footer"]) 
                           and len(p.get_text(strip=True)) > 20]
            body = " ".join([p.get_text(strip=True) for p in content_paras])
        
        body = clean_boilerplate(body)
        
        if not is_english_text(body):
            logger.warning(f"Non-English content: {url}")
            return None
        
        # Extract image
        image_url = ""
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            image_url = og_image["content"]
        else:
            for selector in [soup.find("img", class_="featured-image"),
                           soup.find("div", class_="article-image"),
                           soup.find("figure", class_="media")]:
                if selector:
                    img = selector.find("img") if selector.name != "img" else selector
                    if img and img.get("src"):
                        image_url = img["src"]
                        break
        
        # Extract date
        publish_date = datetime.now().strftime("%Y-%m-%d")
        date_elem = soup.find("time")
        if date_elem and date_elem.get("datetime"):
            try:
                date_obj = datetime.fromisoformat(date_elem["datetime"].replace('Z', '+00:00'))
                publish_date = date_obj.strftime("%Y-%m-%d")
                
                # NEW: DATE FILTERING
                article_age = datetime.now() - date_obj.replace(tzinfo=None)
                if article_age.days > MAX_ARTICLE_AGE_DAYS:
                    logger.debug(f"Skipping old Straits Times article ({article_age.days} days): {headline[:50]}")
                    return None
            except Exception as date_error:
                logger.debug(f"Date parsing error for Straits Times: {date_error}")
                # Use default date (today) if parsing fails
                pass
        else:
            # No date found: use current date (assume recent since scraped today)
            logger.debug(f"No date found for Straits Times article: {headline[:50]} (using today's date)")
            pass
        
        topic = derive_topic_from_metadata(url, soup=soup, text=f"{headline} {body}")
        
        if not body or len(body) < 50:
            logger.warning(f"Insufficient content from {url}")
            return None
        
        return {
            "headline": headline.replace("\n", " "),
            "body": body.replace("\n", " ")[:5000],
            "publish_date": publish_date,
            "image_url": image_url,
            "topic": topic
        }
        
    except Exception as e:
        logger.error(f"Straits Times scraping error for {url}: {e}")
        return None


def scrape_cna(url):
    """Scrape CNA article with DATE FILTERING"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(url, headers=headers, timeout=10)
        soup = bs(res.content, "html.parser")
        
        # Extract headline
        headline_elem = (soup.find("h1", class_="h1--page-title") or soup.find("h1") or
                        soup.find("div", class_="article__title"))
        headline = headline_elem.text.strip() if headline_elem else "Headline not found"
        
        # Extract body
        body_paras = soup.find_all("div", class_="text-long") or soup.find_all("p")
        body = " ".join([para.get_text(strip=True) for para in body_paras])
        
        # Extract image
        image_url = ""
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            image_url = og_image["content"]
        else:
            img = soup.find("img", class_="article__header-image")
            if img and img.get("src"):
                image_url = img["src"]
        
        # Extract date
        publish_date = datetime.now().strftime("%Y-%m-%d")
        time_elem = soup.find("time", class_="article__publish-date")
        if time_elem and time_elem.get("datetime"):
            try:
                date_obj = datetime.fromisoformat(time_elem["datetime"].replace('Z', '+00:00'))
                publish_date = date_obj.strftime("%Y-%m-%d")
                
                # NEW: DATE FILTERING
                article_age = datetime.now() - date_obj.replace(tzinfo=None)
                if article_age.days > MAX_ARTICLE_AGE_DAYS:
                    logger.debug(f"⏭️  Skipping old CNA article ({article_age.days} days): {headline[:50]}")
                    return None
            except Exception as date_error:
                logger.debug(f"Date parsing error for CNA: {date_error}")
                # Use default date (today) if parsing fails
                pass
        else:
            # No date found: use current date (assume recent since scraped today)
            logger.debug(f"No date found for CNA article: {headline[:50]} (using today's date)")
            pass
        
        topic = derive_topic_from_metadata(url, soup=soup, text=f"{headline} {body}")
        
        return {
            "headline": headline.replace("\n", " "),
            "body": body.replace("\n", " ")[:5000],
            "publish_date": publish_date,
            "image_url": image_url,
            "topic": topic
        }
        
    except Exception as e:
        logger.error(f"CNA scraping error for {url}: {e}")
        return None


def scrape_fox_news(url):
    """Scrape Fox News article with DATE FILTERING"""
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        soup = bs(res.content, "html.parser")
        
        # Check for paywall
        paywall = bool(soup.find("div", class_="paywall"))
        
        # Extract headline
        headline_elem = soup.find("h1", class_="headline") or soup.find("h1")
        headline = headline_elem.text.strip() if headline_elem else "Headline not found"
        
        # Extract date (BEFORE body to skip old articles early)
        publish_date = datetime.now().strftime("%Y-%m-%d")
        time_elem = soup.find("time")
        if time_elem and time_elem.get("datetime"):
            try:
                date_obj = datetime.fromisoformat(time_elem["datetime"].replace('Z', '+00:00'))
                publish_date = date_obj.strftime("%Y-%m-%d")
                
                # NEW: DATE FILTERING
                article_age = datetime.now() - date_obj.replace(tzinfo=None)
                if article_age.days > MAX_ARTICLE_AGE_DAYS:
                    logger.debug(f"⏭️  Skipping old Fox News article ({article_age.days} days): {headline[:50]}")
                    return None
            except Exception as date_error:
                logger.debug(f"Date parsing error for Fox News: {date_error}")
                # Use default date (today) if parsing fails
                pass
        else:
            # No date found: use current date (assume recent since scraped today)
            logger.debug(f"No date found for Fox News article: {headline[:50]} (using today's date)")
            pass
        
        # Extract body
        body = ""
        article = soup.find("div", class_="paywall") if paywall else (
            soup.find("div", class_="article-body") or 
            soup.find("article") or 
            soup.find("div", class_="article-content")
        )
        
        if article:
            paragraphs = article.find_all("p")
            boilerplate_phrases = ["You can now listen to Fox News articles", "EW You can now",
                                  "Listen to this article", "Sign up", "Subscribe"]
            
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    if not any(phrase in text for phrase in boilerplate_phrases):
                        body += text + " "
        
        body = clean_boilerplate(body.strip())
        
        if len(body) < 100:
            logger.warning(f"Fox News insufficient content: {url}")
            return None
        
        if not is_english_text(body):
            logger.warning(f"Fox News non-English content: {url}")
            return None
        
        topic = derive_topic_from_metadata(url, soup=soup, text=f"{headline} {body}")
        
        return {
            "headline": headline,
            "body": body.strip(),
            "topic": topic
        }
        
    except Exception as e:
        logger.error(f"Fox News scraping error for {url}: {e}")
        return None