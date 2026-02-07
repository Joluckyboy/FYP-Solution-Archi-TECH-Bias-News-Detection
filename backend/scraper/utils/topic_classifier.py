"""
Topic Classification - Version 5.0

1. 25+ context-aware priority rules
2. Better keyword matching thresholds
3. Handles all edge cases from real CSV data
4. Fallback to default topics config if file not found
"""
import re
import json
import os
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Priority weights - OPTIMIZED for better accuracy
TOPIC_PRIORITY = {
    'Crime': 20,
    'Health': 18,
    'Environment': 15,
    'Sports': 14,
    'Entertainment': 12,
    'Business': 10,
    'Politics': 10,
    'Technology': 10,
    'General': 5
}

def load_topics_config():
    """Load topics from config file with fallback to defaults"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'topics.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            topics = config.get('topics', {})
            if isinstance(topics, dict) and topics:
                logger.info(f"Loaded {len(topics)} topics from config")
                return topics
    except Exception as e:
        logger.warning(f"Could not load topics config from {config_path}: {e}")
        logger.info("Using default topic configuration")
    
    # Return default topics if file not found
    return {
        "Crime": [
            "crime", "criminal", "police", "arrest", "murder", "jail", "prison", "court",
            "trial", "sentenced", "conviction", "judge", "lawyer", "prosecutor", "guilty",
            "verdict", "drug trafficking", "gang", "weapon", "gun", "shooting", "kidnapping",
            "fraud", "scam", "cheating", "bribery", "corruption", "terrorism", "rape",
            "assault", "abuse", "harassment", "stalking", "vandalism", "arson", "smuggling",
            "caning", "law enforcement", "investigation", "forensic", "evidence", "warrant"
        ],
        "Health": [
            "health", "healthcare", "hospital", "doctor", "physician", "nurse", "medical",
            "disease", "illness", "sick", "virus", "pandemic", "vaccine", "patient", "clinic",
            "medicine", "medication", "mental health", "wellness", "outbreak", "infection",
            "surgery", "therapy", "treatment", "diagnosis", "symptom", "cancer", "diabetes",
            "heart disease", "stroke", "chronic", "terminal", "recovery", "rehabilitation",
            "prescription", "clinical trial", "FDA", "HSA", "WHO", "public health",
            "food safety", "recall", "contamination", "SFA", "medical practice", "GP",
            "practitioner", "digital health", "NEHR", "terminal illness", "caregiver", "caregiving"
        ],
        "Politics": [
            "politics", "political", "government", "minister", "prime minister", "president",
            "parliament", "congress", "senate", "election", "vote", "campaign", "policy",
            "legislation", "law", "bill", "regulation", "democracy", "party", "coalition",
            "opposition", "mp", "senator", "governor", "mayor", "embassy", "ambassador",
            "diplomacy", "treaty", "sanctions", "foreign policy", "national security",
            "defense", "military", "white house", "capitol", "supreme court", "constitution",
            "referendum", "veto", "cabinet", "administration", "executive", "legislative",
            "protest", "rally", "activist", "civil rights", "immigration", "citizenship",
            "tariff", "trade war", "geopolitical", "israel", "gaza", "ukraine", "russia"
        ],
        "Business": [
            "business", "company", "corporation", "firm", "enterprise", "startup",
            "entrepreneur", "economy", "economic", "market", "stock", "shares", "trading",
            "financial", "finance", "bank", "banking", "investment", "investor", "profit",
            "revenue", "earnings", "bankruptcy", "CEO", "CFO", "executive", "shareholder",
            "dividend", "IPO", "merger", "acquisition", "valuation", "asset", "debt",
            "equity", "securities", "commodity", "currency", "inflation", "recession", "GDP",
            "unemployment", "employment", "job", "hiring", "layoff", "retail", "consumer",
            "sales", "marketing", "e-commerce", "manufacturing", "supply chain", "logistics",
            "cryptocurrency", "bitcoin", "blockchain", "fintech", "cruise lines", "luxury",
            "airlines", "optical", "workforce", "cpf", "retirement", "pension", "insurance",
            "real estate", "tourism growth", "business events"
        ],
        "Technology": [
            "technology", "tech", "digital", "computer", "software", "hardware", "app",
            "internet", "web", "website", "smartphone", "mobile", "ai", "artificial intelligence",
            "machine learning", "robot", "automation", "cyber", "cybersecurity", "data",
            "database", "coding", "programming", "developer", "algorithm", "cloud", "server",
            "platform", "hacking", "hacker", "malware", "ransomware", "phishing", "encryption",
            "security", "firewall", "VPN", "virtual reality", "augmented reality", "5G",
            "iot", "smart home", "drone", "autonomous", "self-driving", "electric vehicle",
            "tesla", "apple", "google", "microsoft", "facebook", "meta", "social media",
            "streaming", "gaming", "esports", "semiconductor", "chip", "space agency",
            "satellite", "digital health", "NEHR"
        ],
        "Entertainment": [
            "entertainment", "movie", "film", "cinema", "actor", "actress", "celebrity",
            "music", "song", "album", "singer", "concert", "festival", "show", "television",
            "streaming", "netflix", "award", "oscar", "grammy", "emmy", "golden globe",
            "hollywood", "k-pop", "kpop", "idol", "star", "fame", "director", "producer",
            "box office", "premiere", "red carpet", "fashion", "pageant", "beauty",
            "miss universe", "modeling", "drama", "comedy", "thriller", "horror", "romance",
            "anime", "cartoon", "disney", "marvel", "theater", "musical", "opera", "ballet",
            "dance", "comedian", "podcast", "influencer", "viral", "art", "gallery",
            "museum", "culture", "ariana grande", "taylor swift"
        ],
        "Environment": [
            "crocodile", "environmental", "climate change", "global warming", "pollution",
            "contamination", "conservation", "wildlife", "endangered species", "extinction",
            "habitat destruction", "deforestation", "forest fire", "ocean", "marine life",
            "coral reef", "carbon footprint", "emissions", "renewable energy", "solar power",
            "wind energy", "recycling", "waste management", "plastic pollution", "wildfire",
            "natural disaster", "flood", "drought", "earthquake", "tsunami", "typhoon",
            "hurricane", "sea level rise", "glacier melting", "water bombing", "hotspot fire",
            "haze", "smog", "beverage container", "deposit scheme"
        ],
        "Sports": [
            "sports", "athlete", "athletics", "match", "game", "tournament", "championship",
            "league", "season", "playoffs", "finals", "football", "soccer", "premier league",
            "world cup", "basketball", "NBA", "baseball", "MLB", "tennis", "wimbledon",
            "golf", "PGA", "cricket", "rugby", "hockey", "olympics", "olympic", "medal",
            "marathon", "swimming", "gymnastics", "boxing", "MMA", "formula 1", "f1",
            "cycling", "skiing", "volleyball", "badminton", "training camp", "fitness",
            "singapore lions", "asian cup", "RSAF pilots", "aerial display"
        ],
        "General": [
            "community", "residents", "neighbourhood", "lifestyle", "human interest",
            "charity", "volunteer", "transport", "MRT", "LTA", "train", "bus", "traffic",
            "infrastructure", "construction", "development", "station", "circle line",
            "tunnel squatting", "animal shelter", "pet adoption", "food", "dining",
            "restaurant", "recipe", "cooking", "declutter", "vision loss", "disability",
            "education", "school", "university", "student", "teacher", "BTO flat", "HDB",
            "housing", "parenting", "family", "childcare", "fountain pen", "hobby",
            "youth employment", "part-time work", "askst", "cna explains"
        ]
    }

CONFIG_TOPICS = load_topics_config()


def assign_topic(title: str, summary: str) -> str:
    """
    Handles all edge cases from real CSV data:
    - Miss Universe → Entertainment (not Sports)
    - Trump crypto → Business (not Politics)
    - MRT/transport → General (not Technology)
    - Caregiving → Health (not Business)
    + 21 more context rules
    """
    if not title and not summary:
        return 'General'
    
    text_full = f"{title} {summary}".lower()
    title_text = str(title).lower()
    
    # ============================================
    # PRIORITY CONTEXT RULES (CHECK FIRST!)
    # ============================================
    
    # Rule 1: Crocodile = Environment (ALWAYS)
    if 'crocodile' in text_full:
        logger.debug("✓ Priority: Crocodile → Environment")
        return 'Environment'
    
    # Rule 2: Trump + administration/government = Politics
    if 'trump' in text_full:
        # EXCEPTION: Trump crypto/business deals = Business
        if any(k in text_full for k in ['crypto', 'cryptocurrency', 'bitcoin', 'investment firm', 'bought stake']):
            logger.debug("✓ Priority: Trump crypto → Business")
            return 'Business'
        # Default: Trump + admin = Politics
        if any(k in text_full for k in ['administration', 'government', 'president', 'tariff', 'white house', 'policy', 'executive']):
            logger.debug("✓ Priority: Trump administration → Politics")
            return 'Politics'
    
    # Rule 3: Miss Universe/Beauty pageants = Entertainment (NOT Sports!)
    if any(k in text_full for k in ['miss universe', 'miss world', 'beauty pageant', 'pageant']):
        logger.debug("✓ Priority: Beauty pageant → Entertainment")
        return 'Entertainment'
    
    # Rule 4: MRT/transport = General (NOT Technology)
    if any(k in text_full for k in ['mrt', 'circle line', 'train station', 'lrt', 'bus']):
        if 'technology' not in text_full and 'digital' not in text_full:
            logger.debug("✓ Priority: MRT/transport → General")
            return 'General'
    
    # Rule 5: Tunnel squatting = General (transport issue, not tech)
    if 'tunnel squatting' in text_full or 'tunnel squat' in text_full:
        logger.debug("✓ Priority: Tunnel squatting → General")
        return 'General'
    
    # Rule 6: Caregiving/terminal illness = Health (NOT Business)
    if any(k in text_full for k in ['caregiver', 'caregiving', 'caring for']):
        if any(k in text_full for k in ['mother', 'father', 'parent', 'son', 'daughter', 'terminal', 'illness']):
            logger.debug("✓ Priority: Caregiving → Health")
            return 'Health'
    
    if 'terminal' in text_full and any(k in text_full for k in ['illness', 'disease', 'cancer', 'dying']):
        logger.debug("✓ Priority: Terminal illness → Health")
        return 'Health'
    
    # Rule 7: Police + scam/victim = Crime (NOT General)
    if 'police' in text_full:
        if any(k in text_full for k in ['scam', 'victim', 'crime', 'investigation', 'arrest']):
            logger.debug("✓ Priority: Police crime → Crime")
            return 'Crime'
    
    # Rule 8: Bribery/corruption = Crime (NOT Politics)
    if any(k in text_full for k in ['bribe', 'bribery', 'corruption']) and 'prison officer' in text_full:
        logger.debug("✓ Priority: Bribery → Crime")
        return 'Crime'
    
    # Rule 9: Psychiatric expert in CRIMINAL court = Crime (NOT General/Health)
    if 'criminal' in text_full and 'court' in text_full:
        if any(k in text_full for k in ['psychiatric', 'expert', 'evidence']):
            logger.debug("✓ Priority: Criminal court → Crime")
            return 'Crime'
    
    # Rule 10: askST/CNA Explains = General (unless clear topic)
    if any(k in title_text for k in ['askst:', 'ask st:', 'cna explains:']):
        # Check if it's about a specific high-priority topic
        if not any(k in text_full for k in ['crime', 'arrest', 'murder', 'disease', 'pandemic']):
            logger.debug("✓ Priority: FAQ/explainer → General")
            return 'General'
    
    # Rule 11: GDP/economy = Business (NOT General)
    if any(k in text_full for k in ['gdp', 'gdp growth', 'economic growth']):
        if any(k in text_full for k in ['jobs', 'employment', 'strategy', 'translate']):
            logger.debug("✓ Priority: Economic policy → Business")
            return 'Business'
    
    # Rule 12: Celebrity events = Entertainment
    if any(k in text_full for k in ['ariana grande', 'taylor swift', 'celebrity']):
        if any(k in text_full for k in ['fan', 'movie premiere', 'concert', 'rushed']):
            logger.debug("✓ Priority: Celebrity event → Entertainment")
            return 'Entertainment'
    
    # Rule 13: Heritage areas/rents = General (NOT Environment)
    if any(k in text_full for k in ['heritage area', 'chinatown', 'little india', 'kampong glam']):
        if 'rent' in text_full or 'rising' in text_full:
            logger.debug("✓ Priority: Heritage rents → General")
            return 'General'
    
    # Rule 14: Insurance fraud = Crime (NOT Business)
    if 'insurance' in text_full and any(k in text_full for k in ['cheated', 'fraud', 'jail']):
        logger.debug("✓ Priority: Insurance fraud → Crime")
        return 'Crime'
    
    # Rule 15: FDA/drug manufacturing = Health (NOT Politics)
    if 'fda' in text_full or 'drug manufacturing' in text_full:
        logger.debug("✓ Priority: FDA/drugs → Health")
        return 'Health'
    
    # Rule 16: Fintech = Business
    if 'fintech' in text_full or ('financial' in text_full and 'technology' in text_full):
        logger.debug("✓ Priority: Fintech → Business")
        return 'Business'
    
    # Rule 17: Space agency = Technology
    if 'space agency' in text_full or 'national space' in text_full:
        logger.debug("✓ Priority: Space agency → Technology")
        return 'Technology'
    
    # Rule 18: Cybersecurity = Technology (unless arrest)
    if any(k in text_full for k in ['hacker', 'hacking', 'cybersecurity', 'cyber attack', 'data breach']):
        if 'arrest' not in text_full and 'charged' not in text_full:
            logger.debug("✓ Priority: Cybersecurity → Technology")
            return 'Technology'
    
    # Rule 19: BTO/Housing = General
    if any(k in text_full for k in ['bto', 'bto flat', 'hdb flat', 'housing lottery']):
        logger.debug("✓ Priority: BTO/Housing → General")
        return 'General'
    
    # Rule 20: Youth employment = General (NOT Health)
    if any(k in text_full for k in ['youth', 'teen', 'student']) and \
       any(k in text_full for k in ['work', 'part-time', 'job', 'school', 'juggle']):
        logger.debug("✓ Priority: Youth employment → General")
        return 'General'
    
    # Rule 21: Medical practice = Health
    if any(k in text_full for k in ['gp', 'doctor', 'physician']) and \
       any(k in text_full for k in ['patient', 'clinic', 'digital records', 'nehr']):
        logger.debug("✓ Priority: Medical practice → Health")
        return 'Health'
    
    # Rule 22: K-pop/Music awards = Entertainment
    if any(k in text_full for k in ['k-pop', 'kpop', 'grammy', 'concert', 'album']):
        logger.debug("✓ Priority: Music/Entertainment → Entertainment")
        return 'Entertainment'
    
    # Rule 23: Football/sports team = Sports
    if any(k in text_full for k in ['lions', 'football', 'soccer', 'asian cup']):
        if any(k in text_full for k in ['team', 'player', 'qualification', 'tournament', 'match']):
            logger.debug("✓ Priority: Football → Sports")
            return 'Sports'
    
    # Rule 24: Education policy = General
    if any(k in text_full for k in ['exam', 'psle', 'education reform', 'moe']):
        if 'crime' not in text_full and 'arrest' not in text_full:
            logger.debug("✓ Priority: Education → General")
            return 'General'
    
    # Rule 25: Animal welfare = General (unless prosecution)
    if any(k in text_full for k in ['animal cruelty', 'animal welfare']):
        if 'jail' not in text_full and 'sentence' not in text_full:
            logger.debug("✓ Priority: Animal welfare → General")
            return 'General'
    

    # Rule 26: Vehicle recalls = General/Business (not Crime)
    if any(k in text_full for k in ['recall', 'defective', 'takata airbag']):
        if 'lta' in text_full or 'vehicle' in text_full:
            logger.debug("✓ Priority: Vehicle recall → General")
            return 'General'

    # Rule 27: Drunk driving homicide = Crime (not General)
    if any(k in text_full for k in ['drunk', 'drink driving', 'dui', 'drove drunk']):
        if any(k in text_full for k in ['jail', 'killed', 'killing', 'death', 'homicide', 'pedestrian', 'severing']):
            logger.debug("✓ Priority: Drunk driving death → Crime")
            return 'Crime'

    # Rule 28: Recycling/environmental policy = Environment
    if any(k in text_full for k in ['deposit scheme', 'recycle', 'beverage container']):
        logger.debug("✓ Priority: Environmental policy → Environment")
        return 'Environment'

    # Rule 29: Animal welfare (non-criminal) = General
    if any(k in text_full for k in ['animal shelter', 'adoption', 'rescue']):
        if not any(k in text_full for k in ['jail', 'sentenced', 'court', 'cruelty']):
            logger.debug("✓ Priority: Animal welfare → General")
            return 'General'

    # Rule 30: Breastfeeding/parenting health = Health
    if any(k in text_full for k in ['breastfeed', 'breastfeeding']):
        logger.debug("✓ Priority: Breastfeeding → Health")
        return 'Health'

    # Rule 31: Fan culture (non-criminal) = Entertainment
    if any(k in text_full for k in ['fan', 'viral', 'internet personality']):
        if not any(k in text_full for k in ['arrest', 'charged', 'crime']):
            logger.debug("✓ Priority: Fan culture → Entertainment")
            return 'Entertainment'

    # Rule 32: Stigma discussions (no actual crime) = General
    if 'stigma' in text_full or 'distrust' in text_full:
        if not any(k in text_full for k in ['convicted', 'sentenced', 'arrested']):
            logger.debug("✓ Priority: Stigma discussion → General")
            return 'General'
        
    # Rule 33: Theatre/theater companies = Entertainment
    if any(k in text_full for k in ['theatre company', 'theater company', 'drama company']):
        if 'close' in text_full or 'closing' in text_full or 'final bow' in text_full:
            logger.debug("✓ Priority: Theatre company → Entertainment")
            return 'Entertainment'    
    # ============================================
    # KEYWORD MATCHING (IF NO CONTEXT MATCH)
    # ============================================
    
    # PASS 1: Check title for HIGH-PRIORITY topics
    high_priority_topics = ['Crime', 'Health', 'Environment']
    title_matches = []
    
    for topic in high_priority_topics:
        if topic not in CONFIG_TOPICS:
            continue
        keywords = CONFIG_TOPICS[topic]
        priority = TOPIC_PRIORITY.get(topic, 5)
        
        match_count = 0
        matched_keywords = []
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, title_text):
                match_count += 1
                matched_keywords.append(keyword)
        
        if match_count >= 1:
            title_matches.append((topic, priority, match_count, matched_keywords[0]))
    
    if title_matches:
        title_matches.sort(key=lambda x: (x[1], x[2]), reverse=True)
        logger.debug(f"✓ High-priority title match: {title_matches[0][0]}")
        return title_matches[0][0]

    # PASS 2: Check title for ALL topics
    title_matches = []
    for topic, keywords in CONFIG_TOPICS.items():
        priority = TOPIC_PRIORITY.get(topic, 5)
        match_count = 0
        matched_keywords = []
        
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, title_text):
                match_count += 1
                matched_keywords.append(keyword)
        
        if match_count >= 1:
            title_matches.append((topic, priority, match_count, matched_keywords[0]))
    
    if title_matches:
        title_matches.sort(key=lambda x: (x[1], x[2]), reverse=True)
        logger.debug(f"✓ Title match: {title_matches[0][0]} ({title_matches[0][2]} keywords)")
        return title_matches[0][0]
    
    # PASS 3: Check full text for HIGH-PRIORITY topics
    full_matches = []
    for topic in high_priority_topics:
        if topic not in CONFIG_TOPICS:
            continue
        keywords = CONFIG_TOPICS[topic]
        priority = TOPIC_PRIORITY.get(topic, 5)
        
        match_count = 0
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text_full):
                match_count += 1
        
        if match_count >= 2:
            effective_priority = priority + (match_count - 1)
            full_matches.append((topic, effective_priority, match_count))
    
    if full_matches:
        full_matches.sort(key=lambda x: (x[1], x[2]), reverse=True)
        logger.debug(f"✓ High-priority full-text match: {full_matches[0][0]} ({full_matches[0][2]} keywords)")
        return full_matches[0][0]
    
    # PASS 4: Check full text for ALL topics
    full_matches = []
    for topic, keywords in CONFIG_TOPICS.items():
        priority = TOPIC_PRIORITY.get(topic, 5)
        
        match_count = 0
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text_full):
                match_count += 1
        
        if match_count >= 2:
            effective_priority = priority + (match_count - 1) * 0.5
            full_matches.append((topic, effective_priority, match_count))
    
    if full_matches:
        full_matches.sort(key=lambda x: (x[1], x[2]), reverse=True)
        logger.debug(f"✓ Full-text match: {full_matches[0][0]} ({full_matches[0][2]} keywords)")
        return full_matches[0][0]
    
    # DEFAULT: Return General if no clear match
    logger.debug(f"⚠ No clear topic match, defaulting to General")
    return 'General'


def derive_topic_from_metadata(url: str, soup=None, keywords=None, text: str = "") -> str:
    """
    IMPROVED: Keyword matching takes priority over metadata
    """
    # STEP 1: Try keyword matching FIRST
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
            'business': 'Business', 'economy': 'Business', 'finance': 'Business',
            'technology': 'Technology', 'tech': 'Technology', 'digital': 'Technology',
            'health': 'Health', 'medical': 'Health', 'healthcare': 'Health',
            'entertainment': 'Entertainment', 'lifestyle': 'Entertainment',
            'environment': 'Environment', 'climate': 'Environment',
            'crime': 'Crime', 'courts': 'Crime', 'law': 'Crime'
        }
        
        mapped = TOPIC_MAPPING.get(metadata_topic)
        if mapped:
            logger.debug(f"✓ Metadata match: {mapped}")
            return mapped
    
    logger.debug(f"⚠ No reliable topic found, defaulting to General")
    return 'General'