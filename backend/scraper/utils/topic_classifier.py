"""
Topic classification with improved keyword matching and priority weighting
"""
import re
import json
import os
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# ENHANCED: Priority weights (specific topics override generic ones)
TOPIC_PRIORITY = {
    'Crime': 20,        # HIGHEST - very specific
    'Health': 18,       # VERY HIGH
    'Environment': 15,  # HIGH - needs boost
    'Politics': 12,     
    'Sports': 12,    
    'Technology': 10,
    'Entertainment': 10,
    'Business': 7,
    'General': 1        # LOWEST - catch-all
}

def load_topics_config():
    """Load topics from config file"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'topics.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            topics = config.get('topics', {})
            if isinstance(topics, dict) and topics:
                logger.info(f"Loaded {len(topics)} topics from config")
                return topics
    except Exception as e:
        logger.error(f"Failed to load topics config: {e}")
        raise

CONFIG_TOPICS = load_topics_config()


def assign_topic(title: str, summary: str) -> str:
    """
    IMPROVED: Context rules FIRST, then keyword matching
    """
    if not title and not summary:
        return 'General'
    
    text_full = f"{title} {summary}".lower()
    title_text = str(title).lower()
    
    # ============================================
    # PRIORITY CONTEXT RULES (CHECK FIRST!)
    # ============================================
    
    # Rule: Medical practice/GP = Health
    if any(k in text_full for k in ['gp', 'doctor', 'physician', 'general practitioner']):
        if any(k in text_full for k in ['patient', 'digital records', 'nehr', 'practice', 'clinic', 'medical']):
            logger.debug("✓ Priority: Medical practice → Health")
            return 'Health'
    
    # Rule: Gaming = Technology
    if any(k in text_full for k in ['pc cafe', 'pc cafes', 'lan shop', 'gaming cafe', 'esports']):
        logger.debug("✓ Priority: Gaming → Technology")
        return 'Technology'
    
    # Rule: Terminal illness/caregiving = Health
    if 'terminal' in text_full and any(k in text_full for k in ['illness', 'disease', 'cancer']):
        logger.debug("✓ Priority: Terminal illness → Health")
        return 'Health'
    
    if any(k in text_full for k in ['caregiver', 'caregiving', 'caring for']) and \
       any(k in text_full for k in ['mother', 'father', 'parent', 'illness']):
        logger.debug("✓ Priority: Caregiving → Health")
        return 'Health'
    
    # Rule: Football/sports team = Sports
    if any(k in text_full for k in ['lions', 'football', 'soccer', 'asian cup']):
        if any(k in text_full for k in ['team', 'player', 'qualification', 'tournament', 'match']):
            logger.debug("✓ Priority: Football → Sports")
            return 'Sports'
    
    # Rule: Volunteer/charity = General
    if any(k in text_full for k in ['volunteer', 'charity', 'hoarder', 'declutter']):
        if any(k in text_full for k in ['social', 'community', 'help', 'rescue']):
            logger.debug("✓ Priority: Volunteer → General")
            return 'General'
    
    # Rule: Hospital + accident = Crime
    if any(k in text_full for k in ['hospital', 'injured', 'hurt']) and \
       any(k in text_full for k in ['accident', 'crash', 'collision', 'lorry']):
        logger.debug("✓ Priority: Accident → Crime")
        return 'Crime'
    
    # Rule: Recreation/simulation of crime = Crime
    if any(k in text_full for k in ['recreat', 'simulat', 'roblox', 'gorebox']) and \
       any(k in text_full for k in ['isis', 'terror', 'attack', 'killing', 'execution']):
        logger.debug("✓ Priority: Crime simulation → Crime")
        return 'Crime'
    
    # Rule: Food recall = Health
    if any(k in text_full for k in ['recall', 'sfa', 'food agency', 'food safety']) and \
       any(k in text_full for k in ['food', 'biscuit', 'product', 'consumer']):
        logger.debug("✓ Priority: Food recall → Health")
        return 'Health'
    
    # Rule: Police advice = General
    if 'police' in title_text and any(k in title_text for k in ['advise', 'advice', 'warn', 'remind']):
        logger.debug("✓ Priority: Police advice → General")
        return 'General'
    
    # Rule: Animal shelter = General
    if any(k in text_full for k in ['animal shelter', 'animal rescue', 'pet adoption']) and \
       any(k in text_full for k in ['charity', 'commissioner', 'inquiry', 'adoption']):
        logger.debug("✓ Priority: Animal shelter → General")
        return 'General'
    
    # ============================================
    # NOW DO KEYWORD MATCHING (IF NO CONTEXT MATCH)
    # ============================================
    
    # PASS 1: Check title for HIGH-PRIORITY topics (Crime, Health, Environment)
    high_priority_topics = ['Crime', 'Health', 'Environment', 'Politics']
    title_matches = []
    
    for topic in high_priority_topics:
        if topic not in CONFIG_TOPICS:
            continue
        keywords = CONFIG_TOPICS[topic]
        priority = TOPIC_PRIORITY.get(topic, 5)
        
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, title_text):
                title_matches.append((topic, priority, len(keyword), keyword))
    
    # If high-priority title match found, return immediately
    if title_matches:
        title_matches.sort(key=lambda x: (x[1], x[2]), reverse=True)
        logger.debug(f"✓ High-priority title match: {title_matches[0][0]} (keyword: '{title_matches[0][3]}')")
        return title_matches[0][0]

    # PASS 2: Check title for ALL topics
    title_matches = []
    for topic, keywords in CONFIG_TOPICS.items():
        priority = TOPIC_PRIORITY.get(topic, 5)
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, title_text):
                title_matches.append((topic, priority, len(keyword), keyword))
    
    if title_matches:
        title_matches.sort(key=lambda x: (x[1], x[2]), reverse=True)
        logger.debug(f"✓ Title match: {title_matches[0][0]} (keyword: '{title_matches[0][3]}')")
        return title_matches[0][0]
    
    # PASS 3: Check full text for HIGH-PRIORITY topics
    full_matches = []
    for topic in high_priority_topics:
        if topic not in CONFIG_TOPICS:
            continue
        keywords = CONFIG_TOPICS[topic]
        priority = TOPIC_PRIORITY.get(topic, 5)
        
        match_count = 0
        matched_keywords = []
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text_full):
                match_count += 1
                matched_keywords.append(keyword)
        
        if match_count > 0:
            # Boost score for multiple keyword matches
            effective_priority = priority + (match_count - 1)
            full_matches.append((topic, effective_priority, match_count, matched_keywords[0]))
    
    if full_matches:
        full_matches.sort(key=lambda x: (x[1], x[2]), reverse=True)
        logger.debug(f"✓ High-priority full-text match: {full_matches[0][0]} ({full_matches[0][2]} keywords)")
        return full_matches[0][0]
    
    # PASS 4: Check full text for ALL topics
    full_matches = []
    for topic, keywords in CONFIG_TOPICS.items():
        priority = TOPIC_PRIORITY.get(topic, 5)
        
        match_count = 0
        matched_keywords = []
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text_full):
                match_count += 1
                matched_keywords.append(keyword)
        
        if match_count > 0:
            effective_priority = priority + (match_count - 1) * 0.5
            full_matches.append((topic, effective_priority, match_count, matched_keywords[0]))
    
    if full_matches:
        full_matches.sort(key=lambda x: (x[1], x[2]), reverse=True)
        logger.debug(f"✓ Full-text match: {full_matches[0][0]} ({full_matches[0][2]} keywords)")
        return full_matches[0][0]
    
    logger.debug(f"⚠ No topic match found, defaulting to General")
    return 'General'


def derive_topic_from_metadata(url: str, soup=None, keywords=None, text: str = "") -> str:
    """
    IMPROVED: Keyword matching takes absolute priority over metadata
    Only use metadata as last resort
    """
    # STEP 1: Try keyword matching FIRST (this is the most reliable)
    if text:
        text_parts = text.split(' ', 100)
        title_proxy = ' '.join(text_parts[:20])
        summary_proxy = ' '.join(text_parts[20:])
        keyword_topic = assign_topic(title_proxy, summary_proxy)
        
        if keyword_topic != 'General':
            return keyword_topic
    
    # STEP 2: Try keywords parameter
    if keywords:
        keywords_text = ' '.join(keywords) if isinstance(keywords, (list, tuple)) else str(keywords)
        keyword_topic = assign_topic(keywords_text, "")
        if keyword_topic != 'General':
            return keyword_topic
    
    # STEP 3: Only use metadata if everything else fails
    candidates = []
    SKIP_GENERIC_TOPICS = {'singapore', 'world', 'asia', 'news', 'latest', 'home', 'local', 'global'}
    
    def add_candidate(value):
        from utils.text_processing import normalize_topic
        topic = normalize_topic(value)
        if topic and topic.lower() not in SKIP_GENERIC_TOPICS and topic not in candidates:
            candidates.append(topic)
    
    if soup is not None and len(soup) > 0:
        meta_keys = ["article:section", "og:section", "section", "category", "type",
                    "article:tag", "news_keywords", "keywords"]
        for key in meta_keys:
            meta = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
            if meta and meta.get("content"):
                add_candidate(meta.get("content"))
        
        # Parse ld+json
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "{}")
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            for k in ['articleSection', 'keywords', 'genre']:
                                if k in item:
                                    add_candidate(item[k])
                else:
                    for k in ['articleSection', 'keywords', 'genre']:
                        if k in data:
                            add_candidate(data[k])
            except:
                continue
    
    # URL path hints
    parsed_url = urlparse(url)
    path_parts = [p for p in parsed_url.path.split("/") if p and not p.isdigit()]
    for part in path_parts:
        if part.lower() not in SKIP_GENERIC_TOPICS:
            add_candidate(part)
    
    # Map metadata to standard categories
    if candidates:
        metadata_topic = candidates[0].lower()
        TOPIC_MAPPING = {
            'sport': 'Sports', 'sports': 'Sports', 'athletics': 'Sports',
            'politics': 'Politics', 'political': 'Politics', 'government': 'Politics',
            'business': 'Business', 'economy': 'Business', 'finance': 'Business', 'markets': 'Business',
            'technology': 'Technology', 'tech': 'Technology', 'digital': 'Technology',
            'health': 'Health', 'medical': 'Health', 'healthcare': 'Health',
            'entertainment': 'Entertainment', 'lifestyle': 'Entertainment', 'culture': 'Entertainment',
            'environment': 'Environment', 'climate': 'Environment', 'sustainability': 'Environment',
            'crime': 'Crime', 'courts': 'Crime', 'law': 'Crime', 'justice': 'Crime'
        }
        
        mapped = TOPIC_MAPPING.get(metadata_topic)
        if mapped:
            logger.debug(f"✓ Metadata match: {mapped}")
            return mapped
    
    logger.debug(f"⚠ No reliable topic found, defaulting to General")
    return 'General'