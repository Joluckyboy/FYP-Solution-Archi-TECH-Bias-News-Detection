"""
Strips journalist bylines, timestamps, and duplicate sentences from article text.
"""
import re


def preprocess_article_text(text: str) -> str:
    """
    Clean article body text before sentiment sentence splitting.
    """

    # ── 1. Strip byline + timestamp ANYWHERE in text ───────────────────────
    # Catches patterns like:
    # "CHONG JUN LIANG 06, 2026, 11:47 AM 06, 2026, 01:52 PM"
    # "JOHN SMITH Mar 6, 2026, 10:30 AM"
    # Works whether at start or mid-text (e.g. after first sentence)
    text = re.sub(
        r'[A-Z][A-Z]+(?:\s+[A-Z][A-Z]+){1,3}'   # ALL-CAPS name (2–4 words)
        r'\s+'
        r'\d{1,2}(?:,\s+|\s+)\d{4},\s+\d{1,2}:\d{2}\s+[AP]M'  # date+time
        r'(?:\s+\d{1,2}(?:,\s+|\s+)\d{4},\s+\d{1,2}:\d{2}\s+[AP]M)?',  # optional second timestamp
        ' ',
        text
    )

    # ── 2. Also catch "Mar 6, 2026, 11:47 AM" style timestamps ────────────
    text = re.sub(
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4},\s+\d{1,2}:\d{2}\s+[AP]M\b',
        ' ',
        text
    )

    # ── 3. Strip "SINGAPORE -" / "SINGAPORE –" location prefix ────────────
    # Works at start of text OR after the cleaned byline
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

    # ── 5. Fix word merges from scraper (e.g. "reducedby", "SCFAperiod") ──
    # Insert space before a capital letter that follows a lowercase letter
    # Only when it looks like a merge, not acronyms
    text = re.sub(r'([a-z])([A-Z][a-z])', r'\1 \2', text)

    # ── 6. General cleanup ─────────────────────────────────────────────────
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r'\s{2,}', ' ', text)
    text = text.strip()

    return text


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