"""
Text cleaning and validation utilities for news scraping - ENHANCED VERSION
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
    """
    if not text:
        return ""
    
    # Fix em dash corruption
    text = text.replace('â€"', '—')
    text = text.replace('â€"', '-')
    text = text.replace('â€"', '–')
    
    # Fix quote corruptions
    text = text.replace('â€œ', '"')
    text = text.replace('â€', '"')
    text = text.replace('â€˜', ''')
    text = text.replace('â€™', ''')
    
    # Fix other common corruptions
    text = text.replace('Â ', ' ')  # Non-breaking space
    text = text.replace('Ã©', 'é')
    text = text.replace('Ã¨', 'è')
    text = text.replace('Ã¡', 'á')
    text = text.replace('Ã±', 'ñ')
    
    # Remove any remaining control characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    return text


def remove_location_prefixes(text: str) -> str:
    """
    Remove common location prefixes from article summaries
    
    Examples:
    - "SINGAPORE — Article text" → "Article text"
    - "SINGAPORE: Article text" → "Article text"  
    - "NEW YORK - Article text" → "Article text"
    """
    if not text:
        return ""
    
    # Pattern: CITY_NAME followed by em dash, colon, or hyphen at START only
    patterns = [
        r'^SINGAPORE\s*[—:–-]\s*',
        r'^NEW\s+[A-Z]+\s*[—:–-]\s*',  # NEW YORK, NEW DELHI, etc.
        r'^[A-Z][A-Z\s]{2,15}\s*[—:–-]\s*',  # Any all-caps location
    ]
    
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text.strip()


def clean_boilerplate(text: str) -> str:
    """Remove common boilerplate text from news articles - ENHANCED VERSION"""
    if not text:
        return ""
    
    # STEP 1: Fix encoding issues FIRST
    text = fix_encoding_issues(text)
    
    # STEP 2: Remove location prefixes  
    text = remove_location_prefixes(text)
    
    # STEP 3: Remove "NEW !", "NEW!", and similar breaking news prefixes at START only
    text = re.sub(r'^\s*NEW\s*!+\s*', '', text, flags=re.IGNORECASE)
    
    # STEP 4: Remove boilerplate phrases
    boilerplate_phrases = [
        # Straits Times & Business Times
        "Sign up now:Get ST's newsletters delivered to your inbox",
        "Get ST's newsletters delivered to your inbox",
        "Sign up here to get Decoding Asia newsletter",
        "Decoding Asia newsletter: your guide to navigating Asia in a new global order",
        "Delivered to your inbox. Free.",
        "Sign up now:",
        "The Usual Place Podcast",
        # Fox News
        "You can now listen to Fox News articles",
        "EW You can now listen to Fox News articles",
        "Listen to this article",
        # CNN
        "EDITOR'S NOTE:",
        "EDITOR'S NOTE: Call to Earth is a CNN editorial series",
        "Perpetual Planet Initiative has partnered with CNN",
        "Sign up for our weekly Wellness newsletter",
        "CNN Business",
        "CNN International Business",
        # Today Online
        "SINGAPORE â€",
        # Generic
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
    
    # Collapse multiple spaces
    cleaned = ' '.join(cleaned.split())
    
    return cleaned.strip()


def is_english_text(text: str, min_ascii_ratio: float = 0.7) -> bool:
    """Check if text is primarily English"""
    if not text or len(text) < 20:
        return False
    
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    ascii_ratio = ascii_chars / len(text)
    
    return ascii_ratio >= min_ascii_ratio


def smart_truncate(text: str, max_length: int = 300) -> str:
    """Truncate text at sentence or word boundaries"""
    if not text:
        return ""
    
    # Remove newlines and excessive whitespace
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = ' '.join(text.split())
    
    if len(text) <= max_length:
        return text.strip()
    
    truncated = text[:max_length]
    min_sentence_pos = int(max_length * 0.6)
    
    # Try to end at sentence boundary
    for delimiter in ['. ', '! ', '? ']:
        last_sentence = truncated.rfind(delimiter, min_sentence_pos)
        if last_sentence > 0:
            return truncated[:last_sentence + 1].strip()
    
    # Try word boundary
    last_space = truncated.rfind(' ')
    if last_space > min_sentence_pos:
        return truncated[:last_space].strip() + '...'
    
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