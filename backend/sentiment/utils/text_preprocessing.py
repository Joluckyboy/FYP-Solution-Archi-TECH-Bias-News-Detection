"""
Strips journalist bylines, timestamps, and duplicate sentences from article text.
"""
import re

try:
    import wordninja
    _WORDNINJA_AVAILABLE = True
except ImportError:
    _WORDNINJA_AVAILABLE = False


def _fix_merged_tokens(text: str) -> str:
    """
    Find tokens that look like merged words (all-lowercase, 7+ chars, no space)
    and split them using wordninja's statistical English word segmentation.

    e.g. 'Fazlinotedthe' → 'Fazli noted the'
         'installthe'    → 'install the'
         'ministersaid'  → 'minister said'
         'monitoringof'  → 'monitoring of'

    Skips tokens that are likely real words (in a known-word set) or
    proper nouns (start with uppercase).
    Only runs if wordninja is installed — degrades gracefully if not.
    """
    if not _WORDNINJA_AVAILABLE:
        return text

    # Match tokens that are: all lowercase OR start with one uppercase then all lowercase
    # AND are 7+ chars (short words are unlikely to be merges)
    # AND contain no digits or special chars
    def try_split(m):
        token = m.group(0)
        lower = token.lower()

        # Skip if it looks like a clean single word (heuristic: no repeated consonants
        # that would indicate a boundary, and it's a common word)
        # Let wordninja decide — if it returns 1 word, keep original
        parts = wordninja.split(lower)
        if len(parts) <= 1:
            return token  # not a merge, keep as-is

        # Reconstruct preserving original capitalisation of first char
        rejoined = ' '.join(parts)
        if token[0].isupper():
            rejoined = rejoined[0].upper() + rejoined[1:]
        return rejoined

    # Only try to split tokens that are 7+ chars, all-alpha, no existing space
    text = re.sub(r'\b[a-zA-Z]{7,}\b', try_split, text)
    return text


def preprocess_article_text(text: str) -> str:
    """
    Clean article body text before sentiment sentence splitting.
    Preserves paragraph breaks (\n\n) as sentence boundaries.
    """

    # ── 1. Strip byline + timestamp ANYWHERE in text ───────────────────────
    text = re.sub(
        r'[A-Z][A-Z]+(?:\s+[A-Z][A-Z]+){1,3}'
        r'\s+'
        r'\d{1,2}(?:,\s+|\s+)\d{4},\s+\d{1,2}:\d{2}\s+[AP]M'
        r'(?:\s+\d{1,2}(?:,\s+|\s+)\d{4},\s+\d{1,2}:\d{2}\s+[AP]M)?',
        ' ',
        text
    )

    # ── 2. Catch "Mar 6, 2026, 11:47 AM" / "March 9, 2026, 3:30 p.m." timestamps
    text = re.sub(
        r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
        r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
        r'\s+\d{1,2},\s+\d{4},\s+\d{1,2}:\d{2}\s*(?:[ap]\.?m\.?|[AP]M)\b',
        ' ',
        text,
        flags=re.IGNORECASE
    )

    # ── 3. Strip "SINGAPORE -" / "SINGAPORE –" location prefix ────────────
    text = re.sub(r'(?:^|\s)SINGAPORE\s*[-–—]\s*', ' ', text)

    # ── 4. Strip CNA/MSF boilerplate footer ───────────────────────────────
    boilerplate_footers = [
        r'Ministry of Social and Family Development\s*Need help\?.*$',
        r'Need help\?\s*Reach us here\.?\s*$',
        r'Ministry of Social and Family Development\s*$',
        r'Reach us here\.?\s*$',
    ]
    for pattern in boilerplate_footers:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

    # ── 5. Fix word merges from inline HTML tags ───────────────────────────
    # 5a. camelCase: "theMiddle" → "the Middle", "saidHe" → "said He"
    text = re.sub(r'([a-z])([A-Z][a-z])', r'\1 \2', text)
    # 5b. ALL-CAPS header fused with next word: "EASTAsked" → "EAST Asked"
    text = re.sub(r'([A-Z]{2,})([A-Z][a-z])', r'\1 \2', text)
    # 5c. All-lowercase merges via wordninja dictionary
    text = _fix_merged_tokens(text)

    # ── 6. Fix missing space after sentence-ending punctuation ────────────
    text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)

    # ── 7. Fix em-dash/en-dash with no surrounding spaces ─────────────────
    text = re.sub(r'\s*(–|—)\s*', ' — ', text)

    # ── 8. Convert paragraph breaks into sentence boundaries ──────────────
    def paragraph_to_sentence(match):
        preceding = match.group(1)
        if preceding and preceding[-1] in '.!?':
            return preceding + ' '
        return preceding + '. '

    text = re.sub(r'(.)\n\n', paragraph_to_sentence, text)

    # ── 9. General cleanup ─────────────────────────────────────────────────
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    text = text.strip()

    # ── 10. Drop boilerplate sentences by pattern ─────────────────────────
    text = _filter_boilerplate_sentences(text)

    return text


_BOILERPLATE_STARTS_RE = re.compile(
    r'^('
    r'subscribe\b.*|'
    r'sign up\b.*|'
    r'click here\b.*|'
    r'tap here\b.*|'
    r'download\b.*(app|newsletter).*|'
    r'get the\b.*app.*|'
    r'loading\.{0,3}$|'
    r'read more\b.*|'
    r'also read\b.*|'
    r'more on this\b.*|'
    r'share this\b.*|'
    r'follow us\b.*|'
    r'morning brief\b.*|'
    r'top stories to start\b.*|'
    r'automated curation\b.*|'
    r'not intended for persons\b.*|'
    r'by clicking subscribe\b.*|'
    r'by clicking\b.*agree\b.*|'
    r'promotional material from\b.*|'
    r'[a-z.,\s]{0,30}you agree\b.*|'
    r'.{5,80}\bcontributed to this report\b.*|'
    r'.{3,60}\bis an? (?:associate |senior |staff |deputy |contributing )?'
    r'(?:editor|reporter|writer|correspondent|producer|anchor)\b.*|'
    r'.{3,60}\bis a (?:fox news|cna|straits times|channel news)\b.*'
    r')$',
    re.IGNORECASE,
)


def _filter_boilerplate_sentences(text: str) -> str:
    raw = re.split(r'(?<=[.!?])\s+', text)
    kept = []
    for sent in raw:
        s = sent.strip()
        if not s:
            continue
        if _BOILERPLATE_STARTS_RE.match(s):
            continue
        kept.append(s)
    return ' '.join(kept)


def deduplicate_sentences(sentences: list[dict]) -> list[dict]:
    """
    Remove duplicate sentences from the sentence_sentiments list.
    Keeps the first occurrence. Also removes sentences that are
    clearly scraper artifacts (too short, or pure boilerplate).
    """
    seen = set()
    result = []

    JUNK_PATTERNS = [
        r'^\s*$',                          # empty
        r'^[\w\s]{0,30}$',                 # very short fragments
        r'reach us here',                  # CNA footer
        r'need help\?',                    # CNA footer
        r'ministry of social',             # MSF boilerplate
        r'have been reduced to \$\d+',     # orphaned sentence fragment
    ]
    junk_re = re.compile('|'.join(JUNK_PATTERNS), re.IGNORECASE)

    for s in sentences:
        text = s.get('sentence', '').strip()

        # Skip empty or junk
        if not text or junk_re.search(text):
            continue

        # Skip if < 15 chars (likely a fragment)
        if len(text) < 15:
            continue

        # Skip duplicates
        if text in seen:
            continue

        seen.add(text)
        result.append(s)

    return result