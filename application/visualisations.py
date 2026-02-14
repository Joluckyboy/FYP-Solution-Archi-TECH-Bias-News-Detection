import os
import re
from typing import Any, Dict, List, Optional
from pathlib import Path
from collections import Counter, defaultdict

import pandas as pd

# =========================================================
# Paths
# =========================================================
SCRAPER_DATA_DIR = os.getenv("SCRAPER_DATA_DIR", "/backend/scraper/data")
SCRAPED_ARTICLES_PATH = Path(SCRAPER_DATA_DIR) / "scraped_articles.csv"

# =========================================================
# Stopwords
# =========================================================
_STOPWORDS = {
    # core
    "the","a","an","and","or","but","if","then","than","to","of","in","on","for","with","at","by","from","as",
    "it","its","this","that","these","those","into","over","after","before","about","against","between","during",
    "without","within","while","not","no","yes",

    # common verbs + news filler
    "says","said","say","speaks","speak","tells","told","warns","warned","urges","urged","calls","called",
    "announces","announced","reports","reported","adds","added","asks","asked",

    # time/filler
    "new","latest","update","updates","live","today","yesterday","tomorrow","year","years","month","months","week","weeks",

    # pronouns
    "he","she","they","them","their","his","her","hers","him","we","our","you","your","i","me","my","us",

    # helper verbs / modals
    "is","are","was","were","be","been","being","have","has","had","do","does","did",
    "will","would","can","could","may","might","must","should","shall",

    # titles that pollute keyword lists
    "president","pm","minister","mr","mrs","ms","dr","sir","madam","gen","general",

    # generic people nouns
    "man","woman","people",
}

# =========================================================
# Event-ish anchor words
# (Bias trending keywords toward “stories/events”, not just entities.)
# =========================================================
_EVENT_NOUNS = {
    "election","vote","campaign","ballot","primary","runoff",
    "trial","court","judge","lawsuit","ruling","appeal","verdict","indictment","charges",
    "murder","killing","shooting","attack","assault","robbery","theft","crime","arrest",
    "fire","blaze","outbreak","explosion","accident","crash","collision","pileup",
    "flood","storm","typhoon","hurricane","earthquake","landslide",
    "protest","strike","riot","clash",
    "budget","tariff","sanctions","deal","agreement","summit",
    "scandal","probe","investigation","resignation","ban",
}


def _slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9\s-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace(" ", "-")
    s = re.sub(r"-+", "-", s)
    return s or "general-news"


def _read_scraped_articles() -> pd.DataFrame:
    if not SCRAPED_ARTICLES_PATH.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(SCRAPED_ARTICLES_PATH)
    except Exception:
        return pd.DataFrame()

    if df.empty:
        return df

    for col in ["title", "summary", "source", "topic", "published_at", "country", "url", "image_url"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    if "topic" in df.columns:
        df["topic"] = df["topic"].replace("", "General News")

    if "published_at" in df.columns:
        df["published_at_dt"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)
    else:
        df["published_at_dt"] = pd.NaT

    return df


def _tokenize_text(text: str) -> List[str]:
    text = (text or "").lower()
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    toks = re.findall(r"[a-z]{3,}", text)
    return [t for t in toks if t not in _STOPWORDS]


def _looks_like_event_phrase(phrase: str) -> bool:
    parts = phrase.split()
    if len(parts) >= 2 and any(p in _EVENT_NOUNS for p in parts):
        return True
    if len(parts) >= 3:
        return True
    return False


def _extract_trending_keywords(df: pd.DataFrame, top_n: int = 8) -> List[str]:
    """
    Return a list[str] of trending story-like keyphrases.

    Fixes:
    - Avoid junk tokens like "his", "will"
    - Avoid duplicates like "Trump" vs "Donald Trump" by preferring longer phrases
    - Prefer event/story phrases (e.g., "fire outbreak", "car crash", "election campaign")
    """
    if df.empty:
        return []

    title_series = df["title"] if "title" in df.columns else pd.Series([""] * len(df))
    summary_series = df["summary"] if "summary" in df.columns else pd.Series([""] * len(df))

    tokenized_docs: List[List[str]] = []
    for t, s in zip(title_series.astype(str), summary_series.astype(str)):
        toks = _tokenize_text(f"{t} {s}")
        if toks:
            tokenized_docs.append(toks)

    if not tokenized_docs:
        return []

    uni = Counter()
    bi = Counter()
    tri = Counter()

    for toks in tokenized_docs:
        uni.update(toks)
        if len(toks) >= 2:
            bi.update([" ".join(toks[i : i + 2]) for i in range(len(toks) - 1)])
        if len(toks) >= 3:
            tri.update([" ".join(toks[i : i + 3]) for i in range(len(toks) - 2)])

    scored: List[tuple[str, float]] = []
    for k, v in tri.items():
        if v >= 2:
            scored.append((k, v * 3.2))
    for k, v in bi.items():
        if v >= 2:
            scored.append((k, v * 2.2))
    for k, v in uni.items():
        if v >= 3:
            scored.append((k, v * 1.0))

    if not scored:
        return []

    scored.sort(key=lambda x: x[1], reverse=True)

    # event/story phrases first
    scored_event_first = [s for s in scored if _looks_like_event_phrase(s[0])]
    scored_other = [s for s in scored if s not in scored_event_first]
    scored = scored_event_first + scored_other

    chosen: List[str] = []
    chosen_norm: List[str] = []

    def _norm(s: str) -> str:
        s = s.lower().strip()
        s = re.sub(r"\s+", " ", s)
        return s

    for term, _score in scored:
        term = (term or "").strip()
        if not term:
            continue

        parts = term.split()
        if any(p in _STOPWORDS for p in parts):
            continue

        n = _norm(term)

        if n in chosen_norm:
            continue

        # subset of existing longer phrase → skip
        if any(n in cn for cn in chosen_norm):
            continue

        # contains existing shorter phrase → replace with longer phrase
        replaced = False
        for i, cn in enumerate(list(chosen_norm)):
            if cn in n:
                chosen[i] = term
                chosen_norm[i] = n
                replaced = True
                break

        if not replaced:
            chosen.append(term)
            chosen_norm.append(n)

        if len(chosen) >= top_n:
            break

    return [c.title() for c in chosen[:top_n]]


def _detect_bias_column(df: pd.DataFrame) -> Optional[str]:
    if df.empty:
        return None
    candidates = ["bias", "bias_type", "bias_label", "biasCategory", "bias_category", "political_bias"]
    cols = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in cols:
            return cols[c.lower()]
    return None


def _normalize_bias_to_group(label: str) -> Optional[str]:
    s = (label or "").strip().lower()
    if not s:
        return None
    s = s.replace("_", "-")
    s = re.sub(r"\s+", "-", s)

    if s in {"left", "liberal"}:
        return "left"
    if s in {"lean-left", "leaning-left", "center-left", "centre-left", "left-leaning"}:
        return "leaning-left"
    if s in {"center", "centre", "neutral", "balanced"}:
        return "center"
    if s in {"lean-right", "leaning-right", "center-right", "centre-right", "right-leaning"}:
        return "leaning-right"
    if s in {"right", "conservative"}:
        return "right"
    return None


# =========================================================
# Main function called by /application/visualisations
# =========================================================
def load_visualisations_data() -> Dict[str, Any]:
    df = _read_scraped_articles()

    if df.empty:
        return {
            "trendingKeywords": [],
            "topicOutletDistribution": {},
            # MUST match frontend keys exactly:
            "outletBiasGroups": {
                "left": [],
                "leaning-left": [],
                "center": [],
                "leaning-right": [],
                "right": [],
            },
        }

    # Trending uses only recent articles
    if "published_at_dt" in df.columns:
        df_recent = df.sort_values("published_at_dt", ascending=False).head(150)
    else:
        df_recent = df.head(150)

    trending = _extract_trending_keywords(df_recent, top_n=8)

    # -----------------------------------------------------
    # Topic coverage: topic_slug -> { outlet -> count }
    # Frontend default value is "general-news".
    # -----------------------------------------------------
    topic_outlet: Dict[str, Dict[str, int]] = {}
    if "topic" in df.columns and "source" in df.columns:
        grouped = df.groupby(["topic", "source"]).size().reset_index(name="count")
        for _, row in grouped.iterrows():
            topic_raw = str(row.get("topic", "")).strip() or "General News"
            outlet = str(row.get("source", "")).strip() or "Unknown"
            count = int(row.get("count", 0))

            topic_slug = _slugify(topic_raw)
            if topic_slug in {"general", "generalnews", "general-news", "general-news-"}:
                topic_slug = "general-news"

            topic_outlet.setdefault(topic_slug, {})
            topic_outlet[topic_slug][outlet] = count

    # ensure default exists so UI loads with data instead of “No data”
    topic_outlet.setdefault("general-news", topic_outlet.get("general-news", {}))

    # put general-news first
    if "general-news" in topic_outlet:
        ordered = {"general-news": topic_outlet["general-news"]}
        for k, v in topic_outlet.items():
            if k != "general-news":
                ordered[k] = v
        topic_outlet = ordered

    # -----------------------------------------------------
    # Outlet bias groups: group_key -> [outlet names]
    # -----------------------------------------------------
    bias_groups: Dict[str, List[str]] = {
        "left": [],
        "leaning-left": [],
        "center": [],
        "leaning-right": [],
        "right": [],
    }

    bias_col = _detect_bias_column(df)
    if bias_col and "source" in df.columns:
        per_outlet_counts: Dict[str, Counter] = defaultdict(Counter)
        for _, row in df[["source", bias_col]].iterrows():
            outlet = str(row["source"] or "").strip() or "Unknown"
            group = _normalize_bias_to_group(str(row[bias_col]))
            if group:
                per_outlet_counts[outlet][group] += 1

        for outlet, counts in per_outlet_counts.items():
            if not counts:
                continue
            group = counts.most_common(1)[0][0]
            if group in bias_groups:
                bias_groups[group].append(outlet)

        for g in list(bias_groups.keys()):
            bias_groups[g].sort(key=lambda o: sum(per_outlet_counts[o].values()), reverse=True)

    return {
        "trendingKeywords": trending,
        "topicOutletDistribution": topic_outlet,
        "outletBiasGroups": bias_groups,
    }
