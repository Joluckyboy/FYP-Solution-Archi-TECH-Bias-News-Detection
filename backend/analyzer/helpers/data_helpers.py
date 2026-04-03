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
from ..core.redis_cache import get_cached, set_cached, delete_cached

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRAPER_DATA_DIR = os.getenv("SCRAPER_DATA_DIR", "/app/data")
SCRAPED_DATA_PATH = os.path.join(SCRAPER_DATA_DIR, "scraped_articles.csv")

DEFAULT_BIAS_DISTRIBUTION: dict[str, int] = {
    "left": 0,
    "lean-left": 0,
    "center": 0,
    "lean-right": 0,
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
        valid_imgs = non_empty_imgs[
            non_empty_imgs["image_url"].str.startswith("http")
        ]
        
        # Filter out domains that block BOTH the browser AND the wsrv proxy
        dead_domains = ["usatoday.com", "gannett-cdn.com", "s.yimg.com", "npr.brightspotcdn.com"]
        for domain in dead_domains:
            valid_imgs = valid_imgs[~valid_imgs["image_url"].str.contains(domain, case=False, na=False)]
        all_images = (
            valid_imgs["image_url"].tolist()[:5] if not valid_imgs.empty else []
        )
        image_url = (
            all_images[0]
            if all_images
            else "https://placehold.co/600x400?text=No+Image"
        )

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
                "framing_differences": get_topic_service()._compute_framing_differences(
                    g
                )
                if get_topic_service()
                else {},
                "linguistic_framing": get_topic_service()._analyze_linguistic_framing(g)
                if get_topic_service()
                else {},
                "articles": articles,
            }
        )

    topics_out.sort(key=lambda t: t.get("latest_date", ""), reverse=True)
    return topics_out


# ---------------------------------------------------------------------------
# Main topic fetch (with TTL cache)
# ---------------------------------------------------------------------------


_REDIS_TOPICS_KEY = "analyzer:topics"
_REDIS_TOPICS_TTL = 21600  # 6 hours — covers EC2 uptime window (12pm-6pm)


def fetch_topics_data() -> tuple[list | None, str | None]:
    """
    Returns (topics, error_string).
    Cache priority: in-memory → Redis → rebuild from CSV.
    """
    global _topics_cache, _topics_cache_time, _topics_cache_csv_mtime

    now = _time.time()

    # ── 1. In-memory cache (fastest) ──────────────────────────────────────
    try:
        csv_mtime = os.path.getmtime(SCRAPED_DATA_PATH) if os.path.exists(SCRAPED_DATA_PATH) else 0.0
    except OSError:
        csv_mtime = 0.0

    mem_fresh = (
        _topics_cache is not None
        and (now - _topics_cache_time) < _TOPICS_CACHE_TTL
        and csv_mtime == _topics_cache_csv_mtime
    )
    if mem_fresh:
        print("Returning in-memory cached topics.")
        return _topics_cache, None

    # ── 2. Redis cache (survives restarts) ────────────────────────────────
    redis_data = get_cached(_REDIS_TOPICS_KEY)
    if redis_data is not None:
        # New cache format includes csv_mtime so we can reject stale Redis data.
        if isinstance(redis_data, dict) and "topics" in redis_data:
            cached_mtime = float(redis_data.get("csv_mtime", -1.0))
            cached_topics = redis_data.get("topics")
            if cached_mtime == csv_mtime:
                print("Returning Redis cached topics.")
                _topics_cache = cached_topics
                _topics_cache_time = now
                _topics_cache_csv_mtime = csv_mtime
                return cached_topics, None
            print("Redis topics cache stale (csv mtime changed); rebuilding.")
        else:
            # Legacy format had only topics list and could become stale after CSV updates.
            print("Ignoring legacy Redis topics cache format; rebuilding.")

    # ── 3. Rebuild from CSV ───────────────────────────────────────────────
    s3_sync.ensure_scraped_csv()
    df = _safe_read_csv(SCRAPED_DATA_PATH)

    if df is None or len(df) == 0:
        return None, f"scraped_articles.csv not found/invalid at {SCRAPED_DATA_PATH}."

    # Refresh mtime after potential S3 download
    try:
        csv_mtime = os.path.getmtime(SCRAPED_DATA_PATH)
    except OSError:
        csv_mtime = 0.0

    topics = None

    if "cluster_id" in df.columns and df["cluster_id"].notna().any():
        print(f"Building topics from cluster_id ({len(df)} rows)...")
        try:
            topics = _build_topics_from_cluster_id(df)
        except Exception as e:
            print(f"cluster_id grouping failed: {e}")
            traceback.print_exc()

    if topics is None:
        print(f"Running TopicClusteredService on {len(df)} rows...")
        try:
            topics = get_topic_service().cluster_articles(df)
            # Write cluster_id back to local CSV so future rebuilds use the fast path
            _backfill_cluster_ids(df, topics)
        except Exception as e:
            print(f"TopicClusteredService failed: {e}")
            traceback.print_exc()

    if topics is None and "topic" in df.columns:
        print(f"Falling back to CSV topic grouping: {SCRAPED_DATA_PATH} ({len(df)} rows)")
        topics = _build_topics_from_scraped_csv(df)

    if topics is None:
        return None, (
            f"scraped_articles.csv not found/invalid at {SCRAPED_DATA_PATH}. "
            "Ensure the scraper writes scraped_articles.csv and the analyzer volume mount is correct."
        )

    # Populate both caches
    _topics_cache = topics
    _topics_cache_time = now
    _topics_cache_csv_mtime = csv_mtime
    set_cached(
        _REDIS_TOPICS_KEY,
        {"csv_mtime": csv_mtime, "topics": topics},
        ttl=_REDIS_TOPICS_TTL,
    )

    return topics, None


def bust_topics_cache():
    """Clear both in-memory and Redis topic caches (called after /dashboard/cluster)."""
    global _topics_cache, _topics_cache_time
    _topics_cache = None
    _topics_cache_time = 0.0
    delete_cached(_REDIS_TOPICS_KEY)
    print("Topics cache busted (memory + Redis).")


# ---------------------------------------------------------------------------
# Primary builder — groups by precomputed cluster_id  (no ML at request time)
# ---------------------------------------------------------------------------


def _build_topics_from_cluster_id(df: pd.DataFrame) -> list[dict[str, Any]]:
    required = {"title", "source", "url", "published_at", "cluster_id"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {missing}")

    df = df.copy().fillna("")
    df = _parse_published_at(df)
    df["cluster_id"] = (
        df["cluster_id"].astype(str).str.strip().replace("", "unclustered")
    )

    topics_out: list[dict[str, Any]] = []

    for cluster_id, group in df.groupby("cluster_id", dropna=False):
        group = group.sort_values(
            "published_at_dt", ascending=False, na_position="last"
        )
        latest_row = group.iloc[0]

        # Representative image — first article with a real http URL
        image_url = "https://placehold.co/600x400?text=No+Image"
        all_images = []
        if "image_url" in group.columns:
            non_empty_imgs = group[group["image_url"].astype(str).str.strip() != ""]
            valid_imgs = non_empty_imgs[
                non_empty_imgs["image_url"].str.startswith("http")
            ]

            # Filter out domains that block BOTH the browser AND the wsrv proxy
            dead_domains = ["usatoday.com", "gannett-cdn.com", "s.yimg.com", "npr.brightspotcdn.com"]
            for domain in dead_domains:
                valid_imgs = valid_imgs[~valid_imgs["image_url"].str.contains(domain, case=False, na=False)]

            all_images = (
                valid_imgs["image_url"].tolist()[:10] if not valid_imgs.empty else []
            )
            image_url = (
                all_images[0]
                if all_images
                else "https://placehold.co/600x400?text=No+Image"
            )

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
            top_summaries = [s for s in group["summary"].astype(str).str.strip() if s][
                :5
            ]
        contextual_insight = (
            "Event Summary:\n" + "\n\n".join(top_summaries)
            if top_summaries
            else "Summary not available yet."
        )

        keep_cols = [
            c
            for c in [
                "title",
                "source",
                "url",
                "published_at",
                "summary",
                "image_url",
                "political_bias",
            ]
            if c in group.columns
        ]

        topics_out.append(
            {
                "id": _stable_id(str(cluster_id)),
                "cluster_id": str(cluster_id),
                "topic_name": topic_name,
                "title": str(latest_row["title"]),
                "image": image_url,
                "all_images": all_images,
                "source_count": int(len(group)),
                "bias_distribution": _bias_distribution(group),
                "latest_date": latest_date,
                "contextual_insight": contextual_insight,
                # Analysis fields
                "silent_outlets": _compute_silent_outlets(group),
                "lead_articles": {},
                "framing_differences": get_topic_service()._compute_framing_differences(
                    group
                )
                if get_topic_service()
                else {},
                "linguistic_framing": get_topic_service()._analyze_linguistic_framing(
                    group
                )
                if get_topic_service()
                else {},
                "articles": group[keep_cols].to_dict(orient="records"),
            }
        )

    # Hottest first (most sources), most recent as tiebreaker
    topics_out.sort(
        key=lambda t: (t["source_count"], t.get("latest_date", "")),
        reverse=True,
    )
    return topics_out


def _stable_id(value: str) -> int:
    """Same as _topic_id but accepts any string."""
    return int(hashlib.md5(str(value).encode("utf-8")).hexdigest()[:8], 16)


def _normalize_bias_label(bias: str) -> str:
    b = (bias or "").lower().replace("_", "-").replace(" ", "-").strip()
    if b in ["left", "lean-left", "leaning-left"]:
        return "lean-left" if "lean" in b else "left"
    if b in ["right", "lean-right", "leaning-right"]:
        return "lean-right" if "lean" in b else "right"
    if b in ["center", "centre", "neutral", "balanced"]:
        return "center"
    return b or "center"

def _bias_distribution(group: pd.DataFrame) -> dict:
    counts = {
        "left": 0,
        "lean-left": 0,
        "center": 0,
        "lean-right": 0,
        "right": 0,
    }
    col = group.get("political_bias", pd.Series(dtype=str)).fillna("")
    for b in col:
        norm = _normalize_bias_label(b)
        if norm == "left":
            counts["left"] += 1
        elif norm == "right":
            counts["right"] += 1
        elif norm == "center":
            counts["center"] += 1
        elif norm == "lean-left":
            counts["lean-left"] += 1
        elif norm == "lean-right":
            counts["lean-right"] += 1
        else:
            counts["center"] += 1
    total = max(sum(counts.values()), 1)
    return {k: round(v / total * 100, 1) for k, v in counts.items()}


def _compute_silent_outlets(group: pd.DataFrame) -> dict:
    """Flag bias categories with zero articles when others have significant coverage."""
    counts: dict[str, int] = {
        "left": 0,
        "lean-left": 0,
        "center": 0,
        "lean-right": 0,
        "right": 0,
    }
    col = group.get("political_bias", pd.Series(dtype=str)).fillna("")
    for b in col:
        norm = _normalize_bias_label(b)
        if norm == "left":
            counts["left"] += 1
        elif norm == "right":
            counts["right"] += 1
        elif norm == "center":
            counts["center"] += 1
        elif norm == "lean-left":
            counts["lean-left"] += 1
        elif norm == "lean-right":
            counts["lean-right"] += 1
        else:
            counts["center"] += 1

    total = max(sum(counts.values()), 1)
    threshold = max(1, total // 4)  # at least 25% covered by another group
    left_vol = counts["left"] + counts["lean-left"]
    right_vol = counts["right"] + counts["lean-right"]
    center_vol = counts["center"]

    return {
        "left_silent": left_vol == 0
        and (right_vol >= threshold or center_vol >= threshold),
        "right_silent": right_vol == 0
        and (left_vol >= threshold or center_vol >= threshold),
        "center_silent": center_vol == 0
        and (left_vol >= threshold or right_vol >= threshold),
    }


# ---------------------------------------------------------------------------
# Backfill cluster_id into local CSV after on-demand S-BERT clustering
# ---------------------------------------------------------------------------


def _backfill_cluster_ids(df: pd.DataFrame, topics: list[dict]) -> None:
    """Write cluster_id back into the local CSV so future cache misses use the fast path."""
    try:
        cluster_map: dict[str, str] = {}
        for topic in topics:
            cid = str(topic.get("id", ""))
            for article in topic.get("articles", []):
                title = article.get("title", "")
                if title:
                    cluster_map[title] = cid

        df["cluster_id"] = df["title"].map(cluster_map).fillna("unclustered")
        df.to_csv(SCRAPED_DATA_PATH, index=False)
        print(f"[backfill] Wrote cluster_id to local CSV ({len(cluster_map)} mapped).")
    except Exception as e:
        print(f"[backfill] Failed to write cluster_id to CSV: {e}")


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
