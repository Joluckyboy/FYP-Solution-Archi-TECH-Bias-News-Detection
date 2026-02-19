import hashlib
from typing import Optional, List, Dict, Any
from flask import Flask, jsonify, request
import pandas as pd
import os
import re
from flask_cors import CORS
from collections import Counter

try:
    from .clustering import TopicClusteredService
    from .summary import SummaryService
    from . import s3_sync
except ImportError:
    from clustering import TopicClusteredService
    from summary import SummaryService
    import s3_sync

app = Flask(__name__)
CORS(app)

print("Loading Analyzer Model...")
service = None
summary_service = None

print("Analyzer starting (lazy model loading).")

def _get_topic_service():
    global service
    if service is not None:
        return service
    # Only load if we truly need it (fallback path)
    service = TopicClusteredService()
    return service

def _get_summary_service():
    global summary_service
    if summary_service is not None:
        return summary_service
    try:
        summary_service = SummaryService()
    except Exception as e:
        print(f"SummaryService disabled: {e}")
        summary_service = None
    return summary_service

print("Analyzer Model Loaded.")

# Path to Scraper Data (downloaded from S3 on startup)
SCRAPER_DATA_DIR = os.getenv("SCRAPER_DATA_DIR", "/app/data")
SCRAPED_DATA_PATH = os.path.join(SCRAPER_DATA_DIR, "scraped_articles.csv")

s3_sync.ensure_scraped_csv()

# Fallback Kaggle dataset if needed
DATASET_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "datasets",
    "kaggle news articles for political bias classification.csv",
)

DEFAULT_BIAS_DISTRIBUTION = {
    "left": 0,
    "leaning_left": 0,
    "center": 1,          # <- since you don't have bias yet
    "leaning_right": 0,
    "right": 0,
}

def _safe_read_csv(path: str) -> Optional[pd.DataFrame]:
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path)
        return df
    except Exception as e:
        print(f"Error reading CSV {path}: {e}")
        return None

def _parse_published_at(df: pd.DataFrame) -> pd.DataFrame:
    if "published_at" in df.columns:
        df["published_at_dt"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)
        df["published_at_dt"] = df["published_at_dt"].fillna(pd.Timestamp.min.tz_localize("UTC"))
    else:
        df["published_at_dt"] = pd.Timestamp.min.tz_localize("UTC")
    return df

def _topic_id(topic_name: str) -> int:
    return int(hashlib.md5(topic_name.encode("utf-8")).hexdigest()[:8], 16)

def _build_topics_from_scraped_csv(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Groups by df['topic'] and returns topic objects that match what your frontend expects.
    """
    required_cols = {"title", "source", "url", "published_at", "summary", "image_url", "topic"}
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"scraped_articles.csv missing columns: {missing}")

    df = df.fillna("")
    df = _parse_published_at(df)

    # If topic is empty for some rows, put them into "General"
    df["topic"] = df["topic"].replace("", "General")

    topics_out = []
    grouped = df.groupby("topic", dropna=False)

    # Build topic objects
    for idx, (topic_name, g) in enumerate(grouped):
        g = g.copy()
        g = g.sort_values("published_at_dt", ascending=False, na_position="last")

        latest_row = g.iloc[0]

        # Representative image: first non-empty image_url in that topic, else blank
        image_url = ""
        non_empty_imgs = g[g["image_url"].astype(str).str.strip() != ""]
        if len(non_empty_imgs) > 0:
            image_url = non_empty_imgs.iloc[0]["image_url"]
        else:
            # still safe: frontend <img> will show broken icon; you can optionally put placeholder here
            image_url = "https://placehold.co/600x400?text=No+Image"

        source_count = int(g["source"].nunique())

        latest_date = ""
        if pd.notna(latest_row.get("published_at_dt")) and str(latest_row.get("published_at_dt")) != "NaT":
            latest_date = latest_row["published_at_dt"].isoformat()

        # "Daily Briefing & AI Analysis" expects topic.contextual_insight
        # We'll build it from your scraped summaries (top few)
        top_summaries = (
            g["summary"]
            .astype(str)
            .str.strip()
        )
        top_summaries = [s for s in top_summaries.tolist() if s][:5]

        if top_summaries:
            contextual_insight = "Event Summary:\n" + "\n\n".join(top_summaries)
        else:
            contextual_insight = "Event Summary:\nSummary not available yet."

        # Articles list for FullCoveragePage
        articles = []
        for _, r in g.iterrows():
            articles.append({
                "title": r["title"],
                "source": r["source"],
                "url": r["url"],
                "published_at": r["published_at"],
                "summary": r["summary"],
                "image_url": r["image_url"],
                "bias": "center",  # placeholder until you add real bias
            })

        topics_out.append({
            "id": _topic_id(str(topic_name)),  # stable id derived from topic name
            "topic_name": str(topic_name),
            "title": str(latest_row["title"]),
            "image": str(image_url),
            "source_count": source_count,
            "bias_distribution": dict(DEFAULT_BIAS_DISTRIBUTION),
            "latest_date": latest_date,
            "contextual_insight": contextual_insight,
            "articles": articles,
        })

    # Sort topics by latest_date descending
    topics_out.sort(key=lambda t: t.get("latest_date", ""), reverse=True)
    return topics_out

def _fetch_topics_data():
    """
    Priority:
    1) scraped_articles.csv (topic column)
    No fallback (to avoid HuggingFace downloads in restricted environments)
    """
    s3_sync.ensure_scraped_csv()
    df = _safe_read_csv(SCRAPED_DATA_PATH)
    if df is not None and len(df) > 0 and "topic" in df.columns:
        print(f"Loading topics directly from scraped CSV: {SCRAPED_DATA_PATH} ({len(df)} rows)")
        return _build_topics_from_scraped_csv(df), None

    return None, (
        f"scraped_articles.csv not found/invalid at {SCRAPED_DATA_PATH}. "
        "Ensure the scraper writes scraped_articles.csv and the analyzer volume mount is correct."
    )

_STOPWORDS = {
    "the","a","an","and","or","but","if","then","than","to","of","in","on","for","with","at","by","from",
    "is","are","was","were","be","been","being","as","it","its","this","that","these","those","into","over",
    "after","before","about","against","between","during","without","within","while","not","no","yes",
    "says","said","new","latest","update","updates","live","gen"
}

def _extract_keywords(df: pd.DataFrame, top_k: int = 10) -> list[str]:
    # Use title + summary if available
    text_parts = []
    if "title" in df.columns:
        text_parts.append(df["title"].astype(str))
    if "summary" in df.columns:
        text_parts.append(df["summary"].astype(str))

    if not text_parts:
        return []

    text = (" ".join(pd.concat(text_parts, axis=0).tolist())).lower()

    # words >= 3 chars, letters only
    tokens = re.findall(r"[a-z]{3,}", text)
    tokens = [t for t in tokens if t not in _STOPWORDS]

    counts = Counter(tokens)
    return [w for w, _ in counts.most_common(top_k)]


@app.route("/dashboard/topics", methods=["GET"])
def dashboard_topics():
    topics_data, error = _fetch_topics_data()
    if error:
        return jsonify({"error": error}), 404

    try:
        formatted_topics = []
        for t in topics_data:
            formatted_topics.append({
                "id": t["id"],
                "title": t["title"],
                "image": t.get("image") or "https://placehold.co/600x400?text=No+Image",
                "sourceCount": t.get("source_count", 0),
                "biasDistribution": t.get("bias_distribution", dict(DEFAULT_BIAS_DISTRIBUTION)),
                "date": t.get("latest_date", ""),
            })

        return jsonify({"topics": formatted_topics[:50]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/dashboard/topic_details/<int:topic_id>", methods=["GET"])
def get_topic_details(topic_id):
    topics_data, error = _fetch_topics_data()
    if error:
        return jsonify({"error": error}), 404

    topic = next((t for t in topics_data if t["id"] == topic_id), None)
    if not topic:
        return jsonify({"error": "Topic not found"}), 404

    # Return in the shape FullCoveragePage expects
    return jsonify({
        "id": topic["id"],
        "title": topic["title"],
        "image": topic.get("image"),
        "bias_distribution": topic.get("bias_distribution", dict(DEFAULT_BIAS_DISTRIBUTION)),
        "source_count": topic.get("source_count", 0),
        "latest_date": topic.get("latest_date", ""),
        "contextual_insight": topic.get("contextual_insight", ""),
        "selection_bias_alert": "",  # optional placeholder
        "articles": topic.get("articles", []),
    }), 200

@app.route("/dashboard/trending_keywords", methods=["GET"])
def trending_keywords():
    df = _safe_read_csv(SCRAPED_DATA_PATH)
    if df is None or len(df) == 0:
        return jsonify({"keywords": []}), 200

    # Optional: keep only last N articles for "trending"
    df = df.fillna("")
    keywords = _extract_keywords(df, top_k=10)
    return jsonify({"keywords": keywords}), 200

@app.route("/dashboard/topic_coverage", methods=["GET"])
def topic_coverage():
    df = _safe_read_csv(SCRAPED_DATA_PATH)
    if df is None or len(df) == 0:
        return jsonify({"topics": [], "coverage": []}), 200

    df = df.fillna("")
    if "topic" not in df.columns or "source" not in df.columns:
        return jsonify({"topics": [], "coverage": []}), 200

    # Normalize topics
    df["topic"] = df["topic"].astype(str).str.strip()
    df.loc[df["topic"] == "", "topic"] = "General"

    selected_topic = request.args.get("topic", "").strip()
    if selected_topic:
        df = df[df["topic"] == selected_topic]

    # coverage: count articles per source
    counts = (
        df.groupby("source")
          .size()
          .sort_values(ascending=False)
          .head(50)
    )

    coverage = [{"source": str(src), "count": int(cnt)} for src, cnt in counts.items()]
    topics = sorted(df["topic"].unique().tolist())

    return jsonify({"topics": topics, "coverage": coverage}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "analyzer"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8017)
