"""
CSV handler with duplicate detection by title + source
1. Clean BOTH title AND summary using comprehensive text cleaning
2. Enhanced duplicate detection (title + source)
3. Topic validation and auto-correction
4. All text cleaning applied consistently
"""
import csv
import os
import logging
import re  # ← ADDED: Required for validate_summary_quality()
from datetime import datetime
from utils.topic_classifier import assign_topic, CONFIG_TOPICS
from utils.text_processing import clean_text_comprehensive
from collections import defaultdict

logger = logging.getLogger(__name__)


class CSVHandler:
    """Handles CSV operations with ENHANCED deduplication and comprehensive text cleaning"""
    
    CSV_FILE = 'data/scraped_articles.csv'
    CSV_HEADERS = ['title', 'source', 'url', 'published_at', 'summary', 
                   'image_url', 'country', 'topic', 'political_bias']
    VALID_BIAS_LABELS = {'left', 'leaning-left', 'center', 'leaning-right', 'right'}
    
    @classmethod
    def initialize_csv(cls):
        """Create CSV file with headers if it doesn't exist"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(cls.CSV_FILE):
            with open(cls.CSV_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=cls.CSV_HEADERS)
                writer.writeheader()
            return

        cls._ensure_csv_schema()

    @classmethod
    def _ensure_csv_schema(cls):
        """Ensure existing CSV has all required headers, add defaults if missing."""
        if not os.path.exists(cls.CSV_FILE):
            return

        with open(cls.CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            existing_headers = reader.fieldnames or []

        if existing_headers == cls.CSV_HEADERS:
            return

        import tempfile

        data_dir = os.path.dirname(cls.CSV_FILE) or '.'
        os.makedirs(data_dir, exist_ok=True)

        with open(cls.CSV_FILE, 'r', encoding='utf-8') as src, \
            tempfile.NamedTemporaryFile('w', newline='', encoding='utf-8', delete=False, dir=data_dir) as tmp:
            reader = csv.DictReader(src)
            writer = csv.DictWriter(tmp, fieldnames=cls.CSV_HEADERS)
            writer.writeheader()

            for row in reader:
                if not row:
                    continue

                migrated = {key: row.get(key, '') for key in cls.CSV_HEADERS}
                writer.writerow(migrated)

        os.replace(tmp.name, cls.CSV_FILE)

    @classmethod
    def _normalize_bias_label(cls, value: str | None) -> str | None:
        if value is None:
            return None
        label = str(value).strip().lower().replace('_', '-').replace(' ', '-')
        return label if label in cls.VALID_BIAS_LABELS else None
    
    @classmethod
    def get_existing_urls(cls) -> set:
        """Get all existing URLs with normalization"""
        if not os.path.exists(cls.CSV_FILE):
            return set()
        
        urls = set()
        with open(cls.CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row and row.get('url'):
                    normalized = row['url'].strip().rstrip('/')
                    urls.add(normalized)
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
            reader = csv.DictReader(f)
            for row in reader:
                if row and row.get('title') and row.get('source'):
                    # Normalize title for comparison
                    title = row['title'].strip().lower()
                    source = row['source'].strip()
                    pairs.add((title, source))
        return pairs
    
    @classmethod
    def append_articles(cls, articles: list) -> int:
        """
        ENHANCED: Append new articles to CSV, skip duplicates by BOTH URL and title+source
        """
        cls.initialize_csv()
        existing_urls = cls.get_existing_urls()
        existing_pairs = cls.get_existing_title_source_pairs()
        
        new_articles = []
        duplicates_skipped = 0
        
        for a in articles:
            # Check URL duplicate
            normalized_url = a.get('url', '').strip().rstrip('/')
            if normalized_url in existing_urls:
                duplicates_skipped += 1
                continue
            
            # ENHANCED: Check title+source duplicate
            title_normalized = a.get('title', '').strip().lower()
            source = a.get('source', '').strip()
            pair = (title_normalized, source)
            
            if pair in existing_pairs:
                logger.debug(f"🚫 Duplicate (same title+source): {a.get('title', '')[:50]} from {source}")
                duplicates_skipped += 1
                continue
            
            # Add to new articles
            a['url'] = normalized_url
            new_articles.append(a)
            existing_urls.add(normalized_url)
            existing_pairs.add(pair)
        
        if new_articles:
            with open(cls.CSV_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=cls.CSV_HEADERS)
                writer.writerows(new_articles)
            logger.info(f"✓ Saved {len(new_articles)} articles (skipped {duplicates_skipped} duplicates)")
        elif duplicates_skipped > 0:
            logger.info(f"🔄 No new articles (skipped {duplicates_skipped} duplicates)")
        
        return len(new_articles)

    @classmethod
    def validate_article(cls, article: dict) -> tuple:
        """Validate article data quality with auto-correction"""
        # Check required fields
        if not article.get('title') or len(str(article.get('title', '')).strip()) < 5:
            return False, "Title too short or missing"
        
        # Normalize URL
        url = article.get('url', '').strip()
        if not url or not url.startswith('http'):
            return False, "Invalid URL"
        article['url'] = url.rstrip('/')
        
        # Check summary
        summary = str(article.get('summary', '')).strip()
        if not summary or len(summary) < 20:
            return False, "Summary too short"
        
        # Detect truncated summaries
        suspicious_endings = ['...', ' and ', ' or ', ' the ', ' a ', ' is ', ' in ']
        if any(summary.endswith(end) for end in suspicious_endings):
            last_sentence = summary.split('.')[-1].strip()
            if last_sentence and len(last_sentence) > 5:
                article['summary'] = summary.rsplit('.', 1)[0] + '.'
        
        # Validate and auto-correct topic
        topic = str(article.get('topic', 'General')).strip().title()
        valid_topics = list(CONFIG_TOPICS.keys()) if isinstance(CONFIG_TOPICS, dict) else CONFIG_TOPICS
        valid_topics = [t.title() for t in valid_topics]
        valid_topics.append('General')
        
        if topic not in valid_topics:
            logger.warning(f"⚠️  Invalid topic '{topic}' for: {article.get('title', '')[:50]}")
            if article.get('summary'):
                reassigned = assign_topic(article.get('title', ''), article.get('summary', ''))
                if reassigned != 'General':
                    logger.info(f"   → Auto-reassigned to: {reassigned}")
                    article['topic'] = reassigned.title()
                else:
                    article['topic'] = 'General'
            else:
                article['topic'] = 'General'
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
        
        # Fill missing fields
        if not article.get('image_url'):
            article['image_url'] = ""

        # Check if we're allowing empty bias labels
        skip_bias = os.getenv('SKIP_BIAS_CLASSIFICATION', 'false').lower() == 'true'
        
        bias_label = cls._normalize_bias_label(article.get('political_bias'))
        
        if not bias_label and not skip_bias:
            return False, "Invalid political bias label"
        
        article['political_bias'] = bias_label or ''  # Empty string if no label

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
        
        # Check for incomplete endings
        bad_endings = [
            ' of.', ' the.', ' a.', ' an.', ' to.', ' in.', ' at.',
            ' for.', ' with.', ' by.', ' from.', ' and.', ' or.',
            'adefault', 'accordingto'  # Word merges
        ]
        
        summary_lower = summary.lower()
        for ending in bad_endings:
            if summary_lower.endswith(ending):
                return False, f"Incomplete ending: {ending}"
        
        # Check for word merges (lowercase letter followed by uppercase)
        if re.search(r'[a-z][A-Z]', summary):
            return False, "Contains word merge (e.g., 'aDefault')"
        
        return True, ""

    @classmethod
    def validate_and_clean_batch(cls, articles: list) -> list:
        """
        COMPREHENSIVE FIXED: Validate and clean batch with:
        - Comprehensive text cleaning (encoding, prefixes, boilerplate) for BOTH title AND summary
        - Deduplication by title+source
        - Summary quality validation
        """
        cleaned = []
        seen_urls = set()
        seen_pairs = set()  # Track (title, source) pairs
        skipped = 0
        
        for article in articles:
            # Check URL duplicate
            normalized_url = article.get('url', '').strip().rstrip('/')
            if normalized_url in seen_urls:
                skipped += 1
                continue
            
            # ENHANCED: Check title+source duplicate
            title_normalized = article.get('title', '').strip().lower()
            source = article.get('source', '').strip()
            pair = (title_normalized, source)
            
            if pair in seen_pairs:
                logger.debug(f"🚫 Batch duplicate: {article.get('title', '')[:50]} from {source}")
                skipped += 1
                continue
            
            article['url'] = normalized_url
            
            is_valid, reason = cls.validate_article(article)
            if not is_valid:
                logger.debug(f"Invalid article: {reason} - {article.get('title', '')[:50]}")
                skipped += 1
                continue
            
            # CRITICAL FIX: Apply comprehensive text cleaning to BOTH title AND summary
            article['title'] = clean_text_comprehensive(str(article.get('title', '')).strip())
            article['summary'] = clean_text_comprehensive(str(article.get('summary', '')).strip())

            bias_label = cls._normalize_bias_label(article.get('political_bias'))
            if not bias_label:
                logger.debug(f"Invalid political bias label: {article.get('political_bias')}")
                skipped += 1
                continue
            article['political_bias'] = bias_label
            
            # NEW: Validate summary quality (check for mid-sentence cutoffs)
            is_valid_summary, summary_issue = cls.validate_summary_quality(article['summary'])
            if not is_valid_summary:
                logger.warning(f"⚠️  Summary quality issue: {summary_issue} - {article.get('title', '')[:50]}")
                # Try to fix incomplete endings
                summary = article['summary']
                bad_endings = [' of.', ' the.', ' a.', ' an.', ' to.', ' in.', ' at.',
                              ' for.', ' with.', ' by.', ' from.', ' and.', ' or.']
                for ending in bad_endings:
                    if summary.lower().endswith(ending):
                        summary = summary[:-len(ending)].strip() + '...'
                        logger.info(f"   → Fixed incomplete ending: {ending}")
                        article['summary'] = summary
                        break
            
            # Final validation after cleaning AND quality check
            if len(article['title']) < 5 or len(article['summary']) < 20:
                logger.debug(f"Article too short after cleaning: {article.get('title', '')[:50]}")
                skipped += 1
                continue
            
            # Standardize other fields
            article['url'] = str(article.get('url', '')).strip()
            
            cleaned.append(article)
            seen_urls.add(normalized_url)
            seen_pairs.add(pair)
        
        if skipped > 0:
            logger.info(f"🧹 Cleaned: {skipped} invalid/duplicate, {len(cleaned)} valid articles")
        
        return cleaned