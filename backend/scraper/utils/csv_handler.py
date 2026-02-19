"""
CSV handler with duplicate detection by title + source.
- Comprehensive text cleaning for title AND summary
- Enhanced duplicate detection (URL + title+source)
- Topic validation and auto-correction
- political_bias field is always saved as-is (empty string = not yet classified)
"""
import csv
import os
import logging
import re
from datetime import datetime
from utils.topic_classifier import assign_topic, CONFIG_TOPICS
from utils.text_processing import clean_text_comprehensive

logger = logging.getLogger(__name__)


class CSVHandler:
    """Handles CSV operations with ENHANCED deduplication and comprehensive text cleaning"""
    
    CSV_FILE = 'data/scraped_articles.csv'
    CSV_HEADERS = [
        'title', 'source', 'url', 'published_at',
        'summary', 'image_url', 'country', 'topic', 'political_bias'
    ]
    VALID_BIAS_LABELS = {'left', 'leaning-left', 'center', 'leaning-right', 'right'}

    @classmethod
    def initialize_csv(cls):
        """Create CSV file with headers if it doesn't exist"""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(cls.CSV_FILE):
            with open(cls.CSV_FILE, 'w', newline='', encoding='utf-8') as f:
                csv.DictWriter(f, fieldnames=cls.CSV_HEADERS).writeheader()
            return
        cls._ensure_csv_schema()

    @classmethod
    def _ensure_csv_schema(cls):
        """Ensure existing CSV has all required headers, add defaults if missing."""
        if not os.path.exists(cls.CSV_FILE):
            return
        with open(cls.CSV_FILE, 'r', encoding='utf-8') as f:
            existing_headers = csv.DictReader(f).fieldnames or []
        if existing_headers == cls.CSV_HEADERS:
            return

        import tempfile
        data_dir = os.path.dirname(cls.CSV_FILE) or '.'
        os.makedirs(data_dir, exist_ok=True)
        with open(cls.CSV_FILE, 'r', encoding='utf-8') as src, \
             tempfile.NamedTemporaryFile('w', newline='', encoding='utf-8',
                                        delete=False, dir=data_dir) as tmp:
            reader = csv.DictReader(src)
            writer = csv.DictWriter(tmp, fieldnames=cls.CSV_HEADERS)
            writer.writeheader()
            for row in reader:
                if row:
                    writer.writerow({k: row.get(k, '') for k in cls.CSV_HEADERS})
        os.replace(tmp.name, cls.CSV_FILE)

    @classmethod
    def _normalize_bias_label(cls, value) -> str:
        """Returns valid label string, or empty string if invalid/missing."""
        if not value:
            return ''
        label = str(value).strip().lower().replace('_', '-').replace(' ', '-')
        return label if label in cls.VALID_BIAS_LABELS else ''

    @classmethod
    def get_existing_urls(cls) -> set:
        """Get all existing URLs with normalization"""
        if not os.path.exists(cls.CSV_FILE):
            return set()
        urls = set()
        with open(cls.CSV_FILE, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                if row and row.get('url'):
                    urls.add(row['url'].strip().rstrip('/'))
        return urls

    @classmethod
    def get_existing_title_source_pairs(cls) -> set:
        """
        ENHANCED: Get all existing (title, source) pairs to prevent duplicates
        This fixes the issue where same article appears multiple times from same source
        """
        if not os.path.exists(cls.CSV_FILE):
            return set()
        pairs = set()
        with open(cls.CSV_FILE, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                if row and row.get('title') and row.get('source'):
                    pairs.add((row['title'].strip().lower(), row['source'].strip()))
        return pairs

    @classmethod
    def append_articles(cls, articles: list) -> int:
        """
        ENHANCED: Append new articles to CSV, skip duplicates by BOTH URL and title+source
        """
        cls.initialize_csv()
        existing_urls  = cls.get_existing_urls()
        existing_pairs = cls.get_existing_title_source_pairs()
        new_articles, skipped = [], 0

        for a in articles:
            url = a.get('url', '').strip().rstrip('/')
            if url in existing_urls:
                skipped += 1
                continue
            pair = (a.get('title', '').strip().lower(), a.get('source', '').strip())
            if pair in existing_pairs:
                skipped += 1
                continue
            a['url'] = url
            new_articles.append(a)
            existing_urls.add(url)
            existing_pairs.add(pair)

        if new_articles:
            with open(cls.CSV_FILE, 'a', newline='', encoding='utf-8') as f:
                csv.DictWriter(f, fieldnames=cls.CSV_HEADERS).writerows(new_articles)
            logger.info(f"✓ Saved {len(new_articles)} articles (skipped {skipped} duplicates)")
        elif skipped:
            logger.info(f"🔄 No new articles (skipped {skipped} duplicates)")

        return len(new_articles)

    @classmethod
    def validate_article(cls, article: dict) -> tuple:
        """Validate and auto-correct article fields. Returns (is_valid, reason)."""
        if not article.get('title') or len(str(article.get('title', '')).strip()) < 5:
            return False, "Title too short or missing"

        url = article.get('url', '').strip()
        if not url or not url.startswith('http'):
            return False, "Invalid URL"
        article['url'] = url.rstrip('/')

        summary = str(article.get('summary', '')).strip()
        if not summary or len(summary) < 20:
            return False, "Summary too short"

        # Auto-correct topic
        topic = str(article.get('topic', 'General')).strip().title()
        valid_topics = [t.title() for t in (CONFIG_TOPICS.keys()
                        if isinstance(CONFIG_TOPICS, dict) else CONFIG_TOPICS)]
        valid_topics.append('General')
        if topic not in valid_topics:
            reassigned = assign_topic(article.get('title', ''), article.get('summary', ''))
            article['topic'] = reassigned.title() if reassigned != 'General' else 'General'
        else:
            article['topic'] = topic

        # Validate date
        pub_date = article.get('published_at', '')
        if pub_date:
            try:
                date_obj = datetime.strptime(pub_date, "%Y-%m-%d")
                if date_obj.year < 2000 or date_obj.year > datetime.now().year + 1:
                    article['published_at'] = datetime.now().strftime("%Y-%m-%d")
            except ValueError:
                article['published_at'] = datetime.now().strftime("%Y-%m-%d")

        if not article.get('image_url'):
            article['image_url'] = ""

        # political_bias: always store as-is (empty = not yet classified by ECS task)
        article['political_bias'] = cls._normalize_bias_label(article.get('political_bias'))

        return True, ""

    @classmethod
    def validate_summary_quality(cls, summary: str) -> tuple:
        """
        Validate summary doesn't have mid-sentence cutoffs
        
        Returns:
            (is_valid, error_message)
        """
        if not summary:
            return False, "Empty summary"
        bad_endings = [
            ' of.', ' the.', ' a.', ' an.', ' to.', ' in.', ' at.',
            ' for.', ' with.', ' by.', ' from.', ' and.', ' or.',
        ]
        summary_lower = summary.lower()
        for ending in bad_endings:
            if summary_lower.endswith(ending):
                return False, f"Incomplete ending: {ending}"
        if re.search(r'[a-z][A-Z]', summary):
            return False, "Contains word merge"
        return True, ""

    @classmethod
    def validate_and_clean_batch(cls, articles: list) -> list:
        """
        COMPREHENSIVE FIXED: Validate and clean batch with:
        - Comprehensive text cleaning (encoding, prefixes, boilerplate) for BOTH title AND summary
        - Deduplication by title+source
        - Summary quality validation
        FIXED: Properly handles SKIP_BIAS_CLASSIFICATION
        """
        """Validate, deduplicate and clean a batch of articles."""
        cleaned, seen_urls, seen_pairs, skipped = [], set(), set(), 0

        for article in articles:
            url = article.get('url', '').strip().rstrip('/')
            if url in seen_urls:
                skipped += 1
                continue

            pair = (article.get('title', '').strip().lower(), article.get('source', '').strip())
            if pair in seen_pairs:
                skipped += 1
                continue

            article['url'] = url
            is_valid, reason = cls.validate_article(article)
            if not is_valid:
                logger.debug(f"Invalid article: {reason} - {article.get('title', '')[:50]}")
                skipped += 1
                continue

            article['title']   = clean_text_comprehensive(str(article.get('title', '')).strip())
            article['summary'] = clean_text_comprehensive(str(article.get('summary', '')).strip())

            # Fix summary quality issues
            is_valid_summary, issue = cls.validate_summary_quality(article['summary'])
            if not is_valid_summary:
                summary = article['summary']
                for ending in [' of.', ' the.', ' a.', ' an.', ' to.', ' in.',
                               ' at.', ' for.', ' with.', ' by.', ' from.', ' and.', ' or.']:
                    if summary.lower().endswith(ending):
                        article['summary'] = summary[:-len(ending)].strip() + '...'
                        break

            if len(article['title']) < 5 or len(article['summary']) < 20:
                skipped += 1
                continue

            cleaned.append(article)
            seen_urls.add(url)
            seen_pairs.add(pair)

        if skipped:
            logger.info(f"🧹 Cleaned: {skipped} invalid/duplicate, {len(cleaned)} valid articles")
        return cleaned