"""
helpers/related_helpers.py
~~~~~~~~~~~~~~~~~~~~~~~~~~
Related-articles lookup helpers used by analyzer routes.
"""

import re

import numpy as np
import pandas as pd

from .data_helpers import fetch_topics_data
from ..core.services import get_topic_service


def _l2_normalize_rows(values: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return values / norms


# ── Source name → domain mapping ─────────────────────────────────────────────
# CSV stores display names (e.g. "Yahoo News Singapore") but we need to match
# against the submitted article's domain (e.g. "sg.news.yahoo.com").
# Add new sources here whenever the scraper config is updated.
SOURCE_NAME_TO_DOMAIN = {
    "yahoo news singapore":  "sg.news.yahoo.com",
    "channel newsasia":      "channelnewsasia.com",
    "the straits times":     "straitstimes.com",
    "today online":          "todayonline.com",
    "the business times":    "businesstimes.com.sg",
    "mothership":            "mothership.sg",
    "cnn":                   "cnn.com",
    "fox news":              "foxnews.com",
    "nbc news":              "nbcnews.com",
    "usa today":             "usatoday.com",
    "npr":                   "npr.org",
}


def _is_same_outlet(source_name: str, source_domain: str) -> bool:
    """
    Returns True if the article's source name resolves to the same domain
    as the submitted article's domain. Handles the CSV display name vs domain mismatch.

    Two checks:
      1. Slug match  — strip spaces/dots/dashes and do substring comparison
                       (original logic, handles most cases)
      2. Name→domain — look up display name in SOURCE_NAME_TO_DOMAIN map,
                       then compare resolved domain against submitted domain
                       (handles "Yahoo News Singapore" vs "sg.news.yahoo.com")
    """
    if not source_domain:
        return False

    source_name_lower   = source_name.lower().strip()
    source_domain_lower = source_domain.lower().strip()

    # Check 1: slug substring match
    domain_slug = source_domain_lower.replace(".", "").replace("-", "").replace("/", "")
    source_slug = source_name_lower.replace(" ", "").replace("-", "").replace(".", "")
    if source_slug in domain_slug or domain_slug[:8] in source_slug:
        return True

    # Check 2: display name → known domain lookup
    mapped_domain = SOURCE_NAME_TO_DOMAIN.get(source_name_lower)
    if mapped_domain:
        # Compare core domain parts (ignore subdomains like "sg.news.")
        # e.g. "sg.news.yahoo.com" and "sg.news.yahoo.com" → match
        # e.g. "sg.news.yahoo.com" and "yahoo.com" → also match via core
        mapped_core = mapped_domain.lower().replace("www.", "")
        submit_core = source_domain_lower.replace("www.", "")
        if mapped_core == submit_core:
            return True
        # One contains the other (handles sg.news.yahoo.com vs yahoo.com)
        if mapped_core in submit_core or submit_core in mapped_core:
            return True

    return False


def find_cluster_id_by_title(df: pd.DataFrame, query_title: str):
    """Find the cluster_id for a given title using exact → substring → word-overlap."""
    query_lower  = query_title.lower().strip()
    query_tokens = set(re.findall(r"[a-z]{3,}", query_lower))

    titles      = df["title"].astype(str).str.strip()
    cluster_ids = df["cluster_id"].astype(str)

    # 1. Exact match
    exact = titles.str.lower() == query_lower
    if exact.any():
        return cluster_ids[exact].iloc[0]

    # 2. Substring match
    for idx, title in titles.items():
        title_lower = title.lower()
        if query_lower in title_lower or title_lower in query_lower:
            return cluster_ids[idx]

    # 3. Word-overlap (≥60%)
    if not query_tokens:
        return None

    best_score = 0.0
    best_cid   = None
    threshold  = 0.6

    for idx, title in titles.items():
        title_tokens = set(re.findall(r"[a-z]{3,}", title.lower()))
        if not title_tokens:
            continue
        overlap = len(query_tokens & title_tokens) / len(query_tokens)
        if overlap > best_score:
            best_score = overlap
            best_cid   = cluster_ids[idx]

    return best_cid if best_score >= threshold else None


def filter_related(cluster_df: pd.DataFrame, source_domain: str, query_title: str) -> list:
    """Return 1 article per outlet (excluding submitter and exact match), sorted by bias."""
    keep_cols = [
        "title", "source", "url", "political_bias",
        "summary", "published_at", "image_url",
    ]
    available = [c for c in keep_cols if c in cluster_df.columns]

    bias_order = {
        "left": 0, "leaning left": 1, "leaning-left": 1,
        "center": 2, "centre": 2, "neutral": 2,
        "leaning right": 3, "leaning-right": 3, "right": 4,
    }

    seen_sources: set = set()
    related: list     = []

    # Sort by most recent first so we pick the freshest article per outlet
    sort_col = "published_at" if "published_at" in cluster_df.columns else None
    if sort_col:
        cluster_df = cluster_df.sort_values(sort_col, ascending=False)

    for _, row in cluster_df.iterrows():
        source = str(row.get("source", "") or "").strip()
        title  = str(row.get("title",  "") or "").strip()

        if not source:
            continue

        # Skip exact article being analysed
        if title.lower() == query_title.lower():
            continue

        # Exclude the submitter's outlet using the improved check
        # (handles both slug match and display name → domain mapping)
        if _is_same_outlet(source, source_domain):
            continue

        # One article per outlet
        if source in seen_sources:
            continue

        seen_sources.add(source)
        related.append({c: str(row.get(c, "") or "") for c in available})

    # Sort by bias spectrum
    related.sort(
        key=lambda a: bias_order.get(
            (a.get("political_bias") or "").lower().strip(), 5
        )
    )
    return related[:15]


def related_articles_sbert(df: pd.DataFrame, query_title: str, source_domain: str):
    """
    S-BERT fallback — returns a (dict, status_code) tuple.
    Only reached when CSV has no cluster_id column.
    """
    topics_data, error = fetch_topics_data()
    if error or not topics_data:
        return {"matched": False, "articles": [], "reason": error or "no topics"}, 200

    svc = get_topic_service()
    if svc is None:
        return {"matched": False, "articles": [], "reason": "embedding model unavailable"}, 200

    try:
        query_embedding = (
            svc.model.encode([query_title], convert_to_tensor=True).cpu().numpy()
        )
        query_embedding    = _l2_normalize_rows(query_embedding)
        cluster_titles     = [t.get("title", "") for t in topics_data]
        cluster_embeddings = (
            svc.model.encode(cluster_titles, convert_to_tensor=True).cpu().numpy()
        )
        cluster_embeddings = _l2_normalize_rows(cluster_embeddings)
    except Exception as e:
        return {"matched": False, "articles": [], "reason": f"embedding failed: {e}"}, 200

    similarities = (cluster_embeddings @ query_embedding.T).flatten()
    best_idx     = int(np.argmax(similarities))
    best_score   = float(similarities[best_idx])

    if best_score < 0.55:
        return {
            "matched": False,
            "articles": [],
            "reason": f"No close match (best similarity: {best_score:.2f})",
        }, 200

    matched_topic = topics_data[best_idx]
    cluster_df    = pd.DataFrame(matched_topic.get("articles", []))

    if cluster_df.empty:
        return {"matched": False, "articles": [], "reason": "cluster empty"}, 200

    related = filter_related(cluster_df, source_domain, query_title)
    return {
        "matched": True,
        "cluster_title": matched_topic.get("title", ""),
        "similarity": round(best_score, 3),
        "articles": related,
    }, 200