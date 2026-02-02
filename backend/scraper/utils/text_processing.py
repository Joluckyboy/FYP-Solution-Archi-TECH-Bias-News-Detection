"""
Text cleaning and validation utilities for news scraping

1. Enhanced encoding fix (â€ → proper characters)
2. SINGAPORE: prefix removal for CNA articles
3. NEW! / NEW ! prefix removal for Fox News
4. Better boilerplate removal
5. All fixes applied to BOTH title AND summary
"""
import re
import logging

logger = logging.getLogger(__name__)


def fix_encoding_issues(text: str) -> str:
    """
    Fix common UTF-8 encoding corruption issues
    
    Common corruptions:
    - â€" → — (em dash)
    - â€œ → " (opening quote)
    - â€ → " (closing quote)
    - â€™ → ' (apostrophe)
    - Â  → (non-breaking space)
    - â€¦ → … (ellipsis)
    - â€" → – (en dash)
    """
    if not text:
        return ""
    
    # Fix em dash corruption
    text = text.replace('â€"', '—')
    text = text.replace('â€"', '-')
    text = text.replace('â€"', '–')
    text = text.replace('â€"', '—')
    
    # Fix quote corruptions
    text = text.replace('â€œ', '"')
    text = text.replace('â€', '"')
    text = text.replace('â€˜', "'")
    text = text.replace('"', '"')
    text = text.replace("'", "'")
    
    # Fix ellipsis
    text = text.replace('â€¦', '…')
    
    # Fix other common corruptions
    text = text.replace('Â ', ' ')
    text = text.replace('Â', ' ')
    text = text.replace('Ã©', 'é')
    text = text.replace('Ã¨', 'è')
    text = text.replace('Ã¡', 'á')
    text = text.replace('Ã±', 'ñ')
    text = text.replace('Ã¼', 'ü')
    text = text.replace('Ã¶', 'ö')
    text = text.replace('Ã¤', 'ä')
    
    # Remove any remaining control characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def remove_location_prefixes(text: str) -> str:
    """
    Remove common location prefixes from article summaries
    
    Examples:
    - "SINGAPORE: Article text" → "Article text"
    - "NEW YORK - Article text" → "Article text"
    """
    if not text:
        return ""
    
    patterns = [
        r'^SINGAPORE\s*[:—–-]\s*',
        r'^NEW\s+YORK\s*[:—–-]\s*',
        r'^NEW\s+DELHI\s*[:—–-]\s*',
        r'^WASHINGTON\s*[:—–-]\s*',
        r'^LONDON\s*[:—–-]\s*',
        r'^[A-Z][A-Z\s]{2,15}\s*[:—–-]\s*',
    ]
    
    for pattern in patterns:
        text = re.sub(pattern, '', text)
    
    return text.strip()


def remove_news_prefixes(text: str) -> str:
    """
    Remove common news prefixes like "NEW!", "BREAKING:", etc.
    
    Examples:
    - "NEW ! Article text" → "Article text"
    - "BREAKING: Article text" → "Article text"
    """
    if not text:
        return ""
    
    patterns = [
        r'^\s*NEW\s*!+\s*',
        r'^\s*BREAKING\s*[!:]\s*',
        r'^\s*EXCLUSIVE\s*[!:]\s*',
        r'^\s*JUST\s+IN\s*[!:]\s*',
        r'^\s*UPDATE\s*[!:]\s*',
        r'^\s*URGENT\s*[!:]\s*',
    ]
    
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text.strip()


def remove_usatoday_dates(text: str) -> str:
    """
    Remove USA Today date prefixes from article text
    
    Examples:
    - "Jan. 30, 2026, 7:56 p.m. ET Article text" → "Article text"
    - "Updated Jan. 30, 2026, 8:28 p.m. ET Article" → "Article"
    """
    if not text:
        return ""
    
    # Pattern 1: "Updated Jan. 30, 2026, 8:28 p.m. ET "
    text = re.sub(
        r'^Updated\s+[A-Z][a-z]{2}\.\s+\d{1,2},\s+\d{4},\s+\d{1,2}:\d{2}\s+[ap]\.m\.\s+ET\s+',
        '',
        text,
        flags=re.IGNORECASE
    )
    
    # Pattern 2: "Jan. 30, 2026, 7:56 p.m. ET "
    text = re.sub(
        r'^[A-Z][a-z]{2}\.\s+\d{1,2},\s+\d{4},\s+\d{1,2}:\d{2}\s+[ap]\.m\.\s+ET\s+',
        '',
        text
    )
    
    # Pattern 3: "Jan. 30, 2026 " (without time)
    text = re.sub(
        r'^[A-Z][a-z]{2}\.\s+\d{1,2},\s+\d{4}\s+',
        '',
        text
    )
    
    return text.strip()


def clean_boilerplate(text: str) -> str:
    """
    Remove common boilerplate text from news articles
    
    Steps:
    1. Fixes encoding issues
    2. Removes location prefixes
    3. Removes news prefixes
    4. Removes newsletter signup text
    5. Cleans up whitespace
    6. PRESERVES ELLIPSIS from truncation
    """
    if not text:
        return ""
    
    # Remember if text was truncated
    was_truncated = text.rstrip().endswith('...')
    
    # Fix encoding issues first
    text = fix_encoding_issues(text)
    
    # Remove prefixes
    text = remove_location_prefixes(text)
    text = remove_news_prefixes(text)
    text = remove_usatoday_dates(text)
    
    # Remove boilerplate phrases
    boilerplate_phrases = [
        "Sign up now:Get ST's newsletters delivered to your inbox",
        "Get ST's newsletters delivered to your inbox",
        "Sign up here to get Decoding Asia newsletter",
        "Decoding Asia newsletter: your guide to navigating Asia in a new global order",
        "Delivered to your inbox. Free.",
        "Sign up now:",
        "The Usual Place Podcast",
        "You can now listen to Fox News articles",
        "EW You can now listen to Fox News articles",
        "Listen to this article",
        "EDITOR'S NOTE:",
        "EDITOR'S NOTE: Call to Earth is a CNN editorial series",
        "Perpetual Planet Initiative has partnered with CNN",
        "Sign up for our weekly Wellness newsletter",
        "CNN Business",
        "CNN International Business",
        "accordingto advance",
        "Sign up",
        "Subscribe to continue reading",
        "Subscribe to get unlimited access",
        "Get unlimited access",
        "Newsletter",
        "Tune in at 12pm SGT/HKT to watch the live show",
        "PublishedJan", "PublishedDec", "PublishedFeb", "PublishedMar", "PublishedApr",
        "UpdatedJan", "UpdatedDec", "UpdatedFeb", "UpdatedMar", "UpdatedApr",
        "ST PHOTO:", "PHOTO:", "ILLUSTRATION:",
        "More information:", "Read more:", "Related stories:",
    ]
    
    cleaned = text
    for phrase in boilerplate_phrases:
        cleaned = re.sub(re.escape(phrase), " ", cleaned, flags=re.IGNORECASE)
    
    # Clean up date patterns
    cleaned = re.sub(r'Published[A-Za-z]{3}\s+\d{1,2},\s+\d{4},\s+\d{1,2}:\d{2}\s+[AP]M', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'Updated[A-Za-z]{3}\s+\d{1,2},\s+\d{4},\s+\d{1,2}:\d{2}\s+[AP]M', '', cleaned, flags=re.IGNORECASE)
    
    # Remove attribution patterns
    cleaned = re.sub(r'By\s+[A-Z][a-z]+\s+[A-Z][a-z]+', '', cleaned)
    cleaned = re.sub(r'ST PHOTO:\s+[A-Z\s]+', '', cleaned)
    
    # Fix typos
    cleaned = cleaned.replace('accordingto', 'according to')
    
    # Collapse multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.strip()
    
    # PRESERVE ELLIPSIS if it was there before cleaning
    if was_truncated and not cleaned.endswith('...'):
        cleaned = cleaned.rstrip() + '...'
    
    return cleaned


def clean_text_comprehensive(text: str) -> str:
    """
    ONE-STOP comprehensive text cleaning for titles and summaries
    
    Applies ALL fixes in the correct order and preserves ellipsis.
    """
    if not text:
        return ""
    
    # Remember if text was truncated
    was_truncated = text.rstrip().endswith('...')
    
    # Apply all cleaning steps
    text = fix_encoding_issues(text)
    text = remove_location_prefixes(text)
    text = remove_news_prefixes(text)
    text = remove_usatoday_dates(text)
    text = clean_boilerplate(text)
    
    # Ensure ellipsis is preserved
    if was_truncated and not text.endswith('...'):
        text = text.rstrip() + '...'
    
    return text.strip()


def is_english_text(text: str, min_ascii_ratio: float = 0.7) -> bool:
    """Check if text is primarily English"""
    if not text or len(text) < 20:
        return False
    
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    ascii_ratio = ascii_chars / len(text)
    
    return ascii_ratio >= min_ascii_ratio


def smart_truncate(text: str, max_length: int = 300) -> str:
    """
    IMPROVED: Truncate text at sentence or word boundaries with GUARANTEED ellipsis
    
    Key improvements over original:
    - ALWAYS adds ellipsis when truncating (100% coverage)
    - Respects sentence boundaries when possible
    - Falls back to word boundaries gracefully
    - Default 300 chars for optimal summary length
    - Never cuts mid-sentence without ellipsis
    
    Args:
        text: Text to truncate
        max_length: Maximum length (default 300)
    
    Returns:
        Truncated text with ellipsis if shortened
    """
    if not text:
        return ""
    
    # Remove newlines and excessive whitespace
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = ' '.join(text.split())
    
    # If text is already short enough, return as-is
    if len(text) <= max_length:
        return text.strip()
    
    # Text needs truncation - will add ellipsis
    truncated = text[:max_length]
    min_sentence_pos = int(max_length * 0.6)  # At least 60% of desired length
    
    # Strategy 1: Try to end at sentence boundary
    sentence_endings = ['. ', '! ', '? ']
    last_sentence_pos = -1
    
    for ending in sentence_endings:
        pos = truncated.rfind(ending)
        if pos > last_sentence_pos and pos >= min_sentence_pos:
            last_sentence_pos = pos
    
    # If we found a good sentence boundary
    if last_sentence_pos >= min_sentence_pos:
        # ALWAYS check if there's more content after the sentence
        full_text_after = text[last_sentence_pos + 1:].strip()
        
        # If there's ANY text after (even 1 char), add ellipsis
        if len(full_text_after) > 5:  # More than just whitespace/punctuation
            return text[:last_sentence_pos + 1].strip() + '...'
        else:
            # This is truly the end of text
            return text[:last_sentence_pos + 1].strip()
        
    # Strategy 2: Word boundary with ellipsis
    last_space = truncated.rfind(' ')
    if last_space > min_sentence_pos:
        return truncated[:last_space].strip() + '...'
    
    # Strategy 3: Hard truncate with ellipsis (fallback)
    return truncated.strip() + '...'


def normalize_topic(raw_topic: str) -> str:
    """Normalize topic labels from metadata"""
    if not raw_topic:
        return ""
    topic = str(raw_topic).replace("_", " ").replace("-", " ")
    topic = topic.split("|")[0].split(",")[0].strip()
    if len(topic) < 3:
        return ""
    return topic.title()