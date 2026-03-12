"""
helpers/data_helpers.py
~~~~~~~~~~~~~~~~~~~~~~~~
Data-loading, caching, and topic-building helpers for the analyzer.
"""

import hashlib
import os
import re
import time as _time
import traceback
from collections import Counter
from typing import Any

import pandas as pd

from ..core import s3_sync
from ..core.services import get_topic_service

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRAPER_DATA_DIR = os.getenv("SCRAPER_DATA_DIR", "/app/data")
SCRAPED_DATA_PATH = os.path.join(SCRAPER_DATA_DIR, "scraped_articles.csv")

DEFAULT_BIAS_DISTRIBUTION: dict[str, int] = {
    "left": 0,
    "leaning_left": 0,
    "center": 0,
    "leaning_right": 0,
    "right": 0,
}

# ---------------------------------------------------------------------------
# Topics cache
# ---------------------------------------------------------------------------

_topics_cache: list | None = None
_topics_cache_time: float = 0.0
_topics_cache_csv_mtime: float = 0.0
_TOPICS_CACHE_TTL = 600  # seconds


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------


def _safe_read_csv(path: str) -> pd.DataFrame | None:
    if not os.path.exists(path):
        return None
    try:
        return pd.read_csv(path)
    except Exception as e:
        print(f"Error reading CSV {path}: {e}")
        return None


def _parse_published_at(df: pd.DataFrame) -> pd.DataFrame:
    if "published_at" in df.columns:
        df["published_at_dt"] = pd.to_datetime(
            df["published_at"], errors="coerce", utc=True
        )
        df["published_at_dt"] = df["published_at_dt"].fillna(
            pd.Timestamp.min.tz_localize("UTC")
        )
    else:
        df["published_at_dt"] = pd.Timestamp.min.tz_localize("UTC")
    return df


def _topic_id(topic_name: str) -> int:
    return int(hashlib.md5(topic_name.encode("utf-8")).hexdigest()[:8], 16)


# ---------------------------------------------------------------------------
# Fallback topic builder (CSV topic column)
# ---------------------------------------------------------------------------


def _build_topics_from_scraped_csv(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Groups by df['topic'] and returns topic objects the frontend expects."""
    required_cols = {
        "title",
        "source",
        "url",
        "published_at",
        "summary",
        "image_url",
        "topic",
    }
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"scraped_articles.csv missing columns: {missing}")

    df = df.fillna("")
    df = _parse_published_at(df)
    df["topic"] = df["topic"].replace("", "General")

    topics_out = []
    for _, (topic_name, g) in enumerate(df.groupby("topic", dropna=False)):
        g = g.copy().sort_values("published_at_dt", ascending=False, na_position="last")
        latest_row = g.iloc[0]

        non_empty_imgs = g[g["image_url"].astype(str).str.strip() != ""]
        valid_imgs = non_empty_imgs[non_empty_imgs["image_url"].str.startswith("http")]
        valid_imgs = valid_imgs[~valid_imgs["image_url"].str.contains("usatoday.com", case=False, na=False)]
        all_images = valid_imgs["image_url"].tolist()[:5] if not valid_imgs.empty else []
        image_url = all_images[0] if all_images else "https://placehold.co/600x400?text=No+Image"

        source_count = int(g["source"].nunique())

        latest_date = ""
        if (
            pd.notna(latest_row.get("published_at_dt"))
            and str(latest_row.get("published_at_dt")) != "NaT"
        ):
            latest_date = latest_row["published_at_dt"].isoformat()

        top_summaries = [s for s in g["summary"].astype(str).str.strip().tolist() if s][
            :5
        ]
        contextual_insight = (
            "Event Summary:\n" + "\n\n".join(top_summaries)
            if top_summaries
            else "Summary not available yet."
        )

        articles = [
            {
                "title": r["title"],
                "source": r["source"],
                "url": r["url"],
                "published_at": r["published_at"],
                "summary": r["summary"],
                "image_url": r["image_url"],
                "political_bias": r["political_bias"],
            }
            for _, r in g.iterrows()
        ]

        topics_out.append(
            {
                "id": _topic_id(str(topic_name)),
                "topic_name": str(topic_name),
                "title": str(latest_row["title"]),
                "image": str(image_url),
                "all_images": all_images,
                "source_count": source_count,
                "bias_distribution": dict(DEFAULT_BIAS_DISTRIBUTION),
                "latest_date": latest_date,
                "contextual_insight": contextual_insight,
                "articles": articles,
            }
        )

    topics_out.sort(key=lambda t: t.get("latest_date", ""), reverse=True)
    return topics_out


# ---------------------------------------------------------------------------
# Main topic fetch (with TTL cache)
# ---------------------------------------------------------------------------


def fetch_topics_data() -> tuple[list | None, str | None]:
    """
    Returns (topics, error_string).
    Priority: semantic clustering → CSV topic-column fallback.
    """
    s3_sync.ensure_scraped_csv()
    df = _safe_read_csv(SCRAPED_DATA_PATH)

    if df is None or len(df) == 0:
        return None, f"scraped_articles.csv not found/invalid at {SCRAPED_DATA_PATH}."

    global _topics_cache, _topics_cache_time, _topics_cache_csv_mtime

    now = _time.time()
    try:
        csv_mtime = os.path.getmtime(SCRAPED_DATA_PATH)
    except OSError:
        csv_mtime = 0.0

    cache_fresh = (
        _topics_cache is not None
        and (now - _topics_cache_time) < _TOPICS_CACHE_TTL
        and csv_mtime == _topics_cache_csv_mtime
    )
    if cache_fresh:
        print("Returning cached topics.")
        return _topics_cache, None

    if "cluster_id" in df.columns and df["cluster_id"].notna().any():
        print(f"Building topics from cluster_id ({len(df)} rows)...")
        try:
            topics = _build_topics_from_cluster_id(df)  # ← new function (Change 2)
            _topics_cache = topics
            _topics_cache_time = now
            _topics_cache_csv_mtime = csv_mtime
            return topics, None
        except Exception as e:
            print(f"cluster_id grouping failed: {e}")
            traceback.print_exc()

    print(f"Running TopicClusteredService on {len(df)} rows...")
    try:
        topics = get_topic_service().cluster_articles(df)
        _topics_cache = topics
        _topics_cache_time = now
        _topics_cache_csv_mtime = csv_mtime
        return topics, None
    except Exception as e:
        print(f"TopicClusteredService failed: {e}")
        traceback.print_exc()

    if "topic" in df.columns:
        print(
            f"Falling back to CSV topic grouping: {SCRAPED_DATA_PATH} ({len(df)} rows)"
        )
        fallback = _build_topics_from_scraped_csv(df)
        _topics_cache = fallback
        _topics_cache_time = now
        _topics_cache_csv_mtime = csv_mtime
        return fallback, None

    return None, (
        f"scraped_articles.csv not found/invalid at {SCRAPED_DATA_PATH}. "
        "Ensure the scraper writes scraped_articles.csv and the analyzer volume mount is correct."
    )

# ---------------------------------------------------------------------------
# Primary builder — groups by precomputed cluster_id  (no ML at request time)
# ---------------------------------------------------------------------------

def _build_topics_from_cluster_id(df: pd.DataFrame) -> list[dict[str, Any]]:
    required = {"title", "source", "url", "published_at", "cluster_id"}
    missing  = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {missing}")

    df = df.copy().fillna("")
    df = _parse_published_at(df)
    df["cluster_id"] = (
        df["cluster_id"].astype(str).str.strip().replace("", "unclustered")
    )

    topics_out: list[dict[str, Any]] = []

    for cluster_id, group in df.groupby("cluster_id", dropna=False):
        group      = group.sort_values(
            "published_at_dt", ascending=False, na_position="last"
        )
        latest_row = group.iloc[0]

        # Representative image — first article with a real http URL
        image_url = "https://placehold.co/600x400?text=No+Image"
        all_images = []
        if "image_url" in group.columns:
            valid = group["image_url"].astype(str).str.strip()
            valid = valid[valid.str.startswith("http")]
            valid = valid[~valid.str.contains("usatoday.com", case=False, na=False)]
            if not valid.empty:
                image_url = valid.iloc[0]
                all_images = valid.tolist()[:5]

        # Latest date as ISO string
        latest_date = ""
        pub_dt = latest_row.get("published_at_dt")
        if pd.notna(pub_dt) and str(pub_dt) != "NaT":
            latest_date = pub_dt.isoformat()

        # Most common CSV topic category (drives filter pills on frontend)
        topic_name = ""
        if "topic" in group.columns:
            mode_vals = group["topic"].dropna().mode()
            if not mode_vals.empty:
                topic_name = str(mode_vals.iloc[0])

        # Contextual insight from top summaries
        top_summaries: list[str] = []
        if "summary" in group.columns:
            top_summaries = [
                s for s in group["summary"].astype(str).str.strip() if s
            ][:5]
        contextual_insight = (
            "Event Summary:\n" + "\n\n".join(top_summaries)
            if top_summaries else "Summary not available yet."
        )

        keep_cols = [
            c for c in [
                "title", "source", "url", "published_at",
                "summary", "image_url", "political_bias",
            ] if c in group.columns
        ]

        topics_out.append({
            "id":                  _stable_id(str(cluster_id)),
            "cluster_id":          str(cluster_id),
            "topic_name":          topic_name,
            "title":               str(latest_row["title"]),
            "image":               image_url,
            "all_images":          all_images,
            "source_count":        int(len(group)),
            "bias_distribution":   _bias_distribution(group),
            "latest_date":         latest_date,
            "contextual_insight":  contextual_insight,
            # Analysis fields populated lazily via /dashboard/topic_enrichment
            "silent_outlets":      {},
            "lead_articles":       {},
            "framing_differences": {},
            "linguistic_framing":  {},
            "articles":            group[keep_cols].to_dict(orient="records"),
        })

    # Hottest first (most sources), most recent as tiebreaker
    topics_out.sort(
        key=lambda t: (t["source_count"], t.get("latest_date", "")),
        reverse=True,
    )
    return topics_out

def _stable_id(value: str) -> int:
    """Same as _topic_id but accepts any string."""
    return int(hashlib.md5(str(value).encode("utf-8")).hexdigest()[:8], 16)


def _bias_distribution(group: pd.DataFrame) -> dict:
    counts = {
        "left": 0, "leaning_left": 0, "center": 0,
        "leaning_right": 0, "right": 0,
    }
    col = group.get("political_bias", pd.Series(dtype=str)).fillna("").str.lower()
    for b in col:
        if   b == "left":   counts["left"]          += 1
        elif b == "right":  counts["right"]         += 1
        elif b == "center": counts["center"]        += 1
        elif "left"  in b:  counts["leaning_left"]  += 1
        elif "right" in b:  counts["leaning_right"] += 1
        else:               counts["center"]        += 1
    total = max(sum(counts.values()), 1)
    return {k: round(v / total * 100, 1) for k, v in counts.items()}

# ---------------------------------------------------------------------------
# Keyword extraction
# ---------------------------------------------------------------------------

_STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "if",
    "then",
    "than",
    "to",
    "of",
    "in",
    "on",
    "for",
    "with",
    "at",
    "by",
    "from",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "as",
    "it",
    "its",
    "this",
    "that",
    "these",
    "those",
    "into",
    "over",
    "after",
    "before",
    "about",
    "against",
    "between",
    "during",
    "without",
    "within",
    "while",
    "not",
    "no",
    "yes",
    "says",
    "said",
    "new",
    "latest",
    "update",
    "updates",
    "live",
    "gen",
}


def extract_keywords(df: pd.DataFrame, top_k: int = 10) -> list[str]:
    text_parts = []
    if "title" in df.columns:
        text_parts.append(df["title"].astype(str))
    if "summary" in df.columns:
        text_parts.append(df["summary"].astype(str))
    if not text_parts:
        return []
    text = (" ".join(pd.concat(text_parts, axis=0).tolist())).lower()
    tokens = [t for t in re.findall(r"[a-z]{3,}", text) if t not in _STOPWORDS]
    return [w for w, _ in Counter(tokens).most_common(top_k)]
