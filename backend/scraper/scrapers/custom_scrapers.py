"""
Custom scrapers for specific news sources (CNA, Straits Times, Fox News) with DATE FILTERING
"""
import re
import requests
import logging
from bs4 import BeautifulSoup as bs
from datetime import datetime, timedelta
from urllib.parse import urljoin
from utils.text_processing import clean_boilerplate, is_english_text, smart_truncate
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
        
        article_cards = soup.find_all("div", class_="card")
        for card in article_cards:
            if specified_length is not None and len(article_urls) >= specified_length:
                break
            a_tag = card.find("a", href=True)
            if a_tag:
                href = a_tag.get("href")
                if href and href.startswith("/"):
                    article_urls.append(f"{base_url}{href}")
        
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


def _unwrap_inline_tags(soup_fragment) -> None:
    """
    Remove ALL child tags inside <p> elements, keeping only their text.
    This prevents BeautifulSoup from inserting spaces mid-word when any
    inline element splits a word across tag boundaries.

    e.g. <p>Fears of <a href="...">at</a>tacks</p>
         → <p>Fears of attacks</p>

    Must be called BEFORE get_text() or _join_paragraphs().
    """
    # Unwrap every tag inside paragraphs — CNA uses many different inline tags
    for p in soup_fragment.find_all('p'):
        for tag in p.find_all(True):  # True = match any tag
            tag.unwrap()


def _join_paragraphs(paragraphs: list) -> str:
    """
    Join paragraph elements with double newline to preserve paragraph structure.
    Uses separator=' ' so BeautifulSoup inserts a space between inline tags
    instead of concatenating them — this prevents mid-word merges like
    'notedtheuptick' or 'tofight' caused by CNA hyperlinks mid-word.
    """
    result = []
    for p in paragraphs:
        # separator=' ' inserts space between any child tags
        text = p.get_text(separator=' ', strip=True)
        # Collapse multiple spaces created by adjacent tags
        text = re.sub(r' {2,}', ' ', text).strip()
        if text:
            result.append(text)
    return "\n\n".join(result)


def scrape_straits_times(url, skip_age_check=False):
    """Scrape Straits Times article with DATE FILTERING and paragraph preservation"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(url, headers=headers, timeout=10)
        soup = bs(res.content, "html.parser")
        
        # Extract headline
        headline_elem = (soup.find("h1", class_="headline") or soup.find("h1") or
                        soup.find("div", {"data-testid": "article-title"}))
        headline = headline_elem.text.strip() if headline_elem else "Headline not found"
        
        # Unwrap inline tags to prevent mid-word spaces in extracted text
        # e.g. <a href="...">at</a>tacks → attacks
        _unwrap_inline_tags(soup)

        # Extract body — preserve paragraph breaks with \n\n
        body = ""
        article_body = soup.find("div", class_="article-body")
        if article_body:
            body_paras = article_body.find_all("p")
            body = _join_paragraphs(body_paras)
        
        if not body or len(body) < 100:
            body_paras = soup.find_all("p", class_="paragraph-base")
            if body_paras:
                body = _join_paragraphs(body_paras)
        
        if not body or len(body) < 100:
            all_paras = soup.find_all("p")
            content_paras = [p for p in all_paras 
                           if not p.find_parent(["nav", "header", "footer"]) 
                           and len(p.get_text(strip=True)) > 20]
            body = _join_paragraphs(content_paras)
        
        body = clean_boilerplate(body, preserve_paragraphs=True)
        
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
                now_ref = datetime.now(date_obj.tzinfo) if date_obj.tzinfo else datetime.now()
                if date_obj.date() > now_ref.date():
                    logger.debug(f"Skipping future Straits Times article: {headline[:50]}")
                    return None

                publish_date = date_obj.strftime("%Y-%m-%d")
                
                article_age = datetime.now() - date_obj.replace(tzinfo=None)
                if not skip_age_check and article_age.days > MAX_ARTICLE_AGE_DAYS:
                    logger.debug(f"Skipping old Straits Times article ({article_age.days} days): {headline[:50]}")
                    return None
            except Exception as date_error:
                logger.debug(f"Date parsing error for Straits Times: {date_error}")
        else:
            logger.debug(f"No date found for Straits Times article: {headline[:50]} (using today's date)")
        
        topic = derive_topic_from_metadata(url, soup=soup, text=f"{headline} {body}")
        
        if not body or len(body) < 50:
            logger.warning(f"Insufficient content from {url}")
            return None
        
        return {
            "headline": headline.replace("\n", " "),
            "body": body,                           # paragraphs separated by \n\n
            "summary": smart_truncate(body.replace("\n", " "), 300),  # flat for CSV
            "publish_date": publish_date,
            "image_url": image_url,
            "topic": topic
        }
        
    except Exception as e:
        logger.error(f"Straits Times scraping error for {url}: {e}")
        return None


def scrape_cna(url, skip_age_check=False):
    """Scrape CNA article with DATE FILTERING and paragraph preservation"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(url, headers=headers, timeout=10)
        soup = bs(res.content, "html.parser")
        
        # Extract headline
        headline_elem = (soup.find("h1", class_="h1--page-title") or soup.find("h1") or
                        soup.find("div", class_="article__title"))
        headline = headline_elem.text.strip() if headline_elem else "Headline not found"

        # Unwrap inline tags to prevent mid-word spaces in extracted text
        _unwrap_inline_tags(soup)

        # CNA newsletter/boilerplate phrases to filter out at paragraph level
        CNA_BOILERPLATE = [
            "subscribe to cna",
            "morning brief",
            "automated curation",
            "top stories to start your day",
            "not intended for persons residing in the e.u",
            "by clicking subscribe",
            "promotional material from mediacorp",
            "loading",
        ]

        def _is_cna_boilerplate(text: str) -> bool:
            t = text.lower().strip()
            return any(phrase in t for phrase in CNA_BOILERPLATE)

        # Extract body — collect <p> tags from div.text-long divs that have content.
        # CNA's DOM contains many empty div.text-long elements (menus, blocks etc).
        # We only want divs that actually contain <p> tags with article text.
        # Deduplication: track seen paragraph texts to avoid mobile/desktop copies.
        text_long_divs = soup.find_all("div", class_="text-long")
        if text_long_divs:
            seen_texts = set()
            all_paras = []
            for div in text_long_divs:
                paras = div.find_all("p")
                if not paras:
                    continue
                # Check if this div's content is a duplicate of already-seen divs
                div_text = div.get_text(strip=True)[:100]
                if div_text in seen_texts:
                    break  # hit the duplicate (desktop copy) — stop here
                seen_texts.add(div_text)
                all_paras.extend(paras)
        else:
            all_paras = soup.find_all("p")

        # Filter boilerplate paragraphs before joining
        clean_paras = [p for p in all_paras if not _is_cna_boilerplate(p.get_text())]
        body = _join_paragraphs(clean_paras)

        body = clean_boilerplate(body, preserve_paragraphs=True)
        
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
                now_ref = datetime.now(date_obj.tzinfo) if date_obj.tzinfo else datetime.now()
                if date_obj.date() > now_ref.date():
                    logger.debug(f"Skipping future CNA article: {headline[:50]}")
                    return None

                publish_date = date_obj.strftime("%Y-%m-%d")
                
                article_age = datetime.now() - date_obj.replace(tzinfo=None)
                if not skip_age_check and article_age.days > MAX_ARTICLE_AGE_DAYS:
                    logger.debug(f"Skipping old CNA article ({article_age.days} days): {headline[:50]}")
                    return None
            except Exception as date_error:
                logger.debug(f"Date parsing error for CNA: {date_error}")
        else:
            logger.debug(f"No date found for CNA article: {headline[:50]} (using today's date)")
        
        topic = derive_topic_from_metadata(url, soup=soup, text=f"{headline} {body}")
        
        return {
            "headline": headline.replace("\n", " "),
            "body": body,                           # paragraphs separated by \n\n
            "summary": smart_truncate(body.replace("\n", " "), 300),  # flat for CSV
            "publish_date": publish_date,
            "image_url": image_url,
            "topic": topic
        }
        
    except Exception as e:
        logger.error(f"CNA scraping error for {url}: {e}")
        return None


def scrape_fox_news(url, skip_age_check=False):
    """Scrape Fox News article with DATE FILTERING and paragraph preservation"""
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        soup = bs(res.content, "html.parser")
        
        paywall = bool(soup.find("div", class_="paywall"))

        headline_elem = soup.find("h1", class_="headline") or soup.find("h1")
        headline = headline_elem.text.strip() if headline_elem else "Headline not found"
        
        publish_date = datetime.now().strftime("%Y-%m-%d")
        time_elem = soup.find("time")
        if time_elem and time_elem.get("datetime"):
            try:
                date_obj = datetime.fromisoformat(time_elem["datetime"].replace('Z', '+00:00'))
                now_ref = datetime.now(date_obj.tzinfo) if date_obj.tzinfo else datetime.now()
                if date_obj.date() > now_ref.date():
                    logger.debug(f"Skipping future Fox News article: {headline[:50]}")
                    return None

                publish_date = date_obj.strftime("%Y-%m-%d")
                
                article_age = datetime.now() - date_obj.replace(tzinfo=None)
                if not skip_age_check and article_age.days > MAX_ARTICLE_AGE_DAYS:
                    logger.debug(f"Skipping old Fox News article ({article_age.days} days): {headline[:50]}")
                    return None
            except Exception as date_error:
                logger.debug(f"Date parsing error for Fox News: {date_error}")
        else:
            logger.debug(f"No date found for Fox News article: {headline[:50]} (using today's date)")
        
        # Extract body — preserve paragraph breaks with \n\n
        body = ""
        article = soup.find("div", class_="paywall") if paywall else (
            soup.find("div", class_="article-body") or 
            soup.find("article") or 
            soup.find("div", class_="article-content")
        )
        
        if article:
            paragraphs = article.find_all("p")
            boilerplate_phrases = ["You can now listen to Fox News articles", "EW You can now",
                                  "Listen to this article", "Sign up", "Subscribe",
                                  "CLICK HERE TO DOWNLOAD", "contributed to this report",
                                  "is an associate editor", "is a senior editor", "is a staff reporter"]
            
            clean_paras = []
            for p in paragraphs:
                text = p.get_text(separator=' ', strip=True)
                text = re.sub(r' {2,}', ' ', text).strip()
                if text and len(text) > 20:
                    if not any(phrase in text for phrase in boilerplate_phrases):
                        clean_paras.append(text)
            
            # Join with \n\n to preserve paragraph structure
            body = "\n\n".join(clean_paras)
        
        body = clean_boilerplate(body.strip(), preserve_paragraphs=True)
        
        if len(body) < 100:
            logger.warning(f"Fox News insufficient content: {url}")
            return None
        
        if not is_english_text(body):
            logger.warning(f"Fox News non-English content: {url}")
            return None
        
        topic = derive_topic_from_metadata(url, soup=soup, text=f"{headline} {body}")
        
        return {
            "headline": headline.replace("\n", " "),
            "body": body,                           # paragraphs separated by \n\n
            "summary": smart_truncate(body.replace("\n", " "), 300),  # flat for CSV
            "topic": topic
        }
        
    except Exception as e:
        logger.error(f"Fox News scraping error for {url}: {e}")
        return None