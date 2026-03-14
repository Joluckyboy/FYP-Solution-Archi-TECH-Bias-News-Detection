import os
import time as _time
from flask import Flask, jsonify, request
from flask_cors import CORS

from .core import s3_sync, get_summary_service
from .helpers import (
    DEFAULT_BIAS_DISTRIBUTION,
    SCRAPED_DATA_PATH,
    extract_keywords,
    fetch_topics_data,
    _safe_read_csv,
)

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# In-memory enrichment cache
# Stores Perplexity results so each topic is only enriched once per TTL window.
# Structure: { topic_id: {"data": {...}, "ts": float} }
# ---------------------------------------------------------------------------
_ENRICHMENT_CACHE: dict = {}
_ENRICHMENT_TTL: int = 3600  # 1 hour in seconds

print("Analyzer starting (lazy model loading).")
s3_sync.ensure_scraped_csv()


@app.route("/dashboard/topics", methods=["GET"])
def dashboard_topics():
    topics_data, error = fetch_topics_data()
    if error:
        return jsonify({"error": error}), 404

    try:
        formatted_topics = [
            {
                "id": t["id"],
                "title": t["title"],
                "topicName": t.get("topic_name", ""),
                "image": t.get("image") or "https://placehold.co/600x400?text=No+Image",
                "allImages": t.get("all_images", []),
                "sourceCount": t.get("source_count", 0),
                "biasDistribution": t.get(
                    "bias_distribution", dict(DEFAULT_BIAS_DISTRIBUTION)
                ),
                "date": t.get("latest_date", ""),
                "frontUrl": t["articles"][0]["url"] if t.get("articles") else None,
            }
            for t in topics_data
        ]
        return jsonify({"topics": formatted_topics[:50]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/dashboard/topic_details/<int:topic_id>", methods=["GET"])
def get_topic_details(topic_id):
    topics_data, error = fetch_topics_data()
    if error:
        return jsonify({"error": error}), 404

    topic = next((t for t in topics_data if t["id"] == topic_id), None)
    if not topic:
        return jsonify({"error": "Topic not found"}), 404

    # Returning base data ONLY - no LLM enrichment here to keep it fast
    return jsonify(
        {
            "id": topic["id"],
            "title": topic["title"],
            "image": topic.get("image"),
            "bias_distribution": topic.get(
                "bias_distribution", dict(DEFAULT_BIAS_DISTRIBUTION)
            ),
            "source_count": topic.get("source_count", 0),
            "latest_date": topic.get("latest_date", ""),
            "contextual_insight": topic.get("contextual_insight", ""),
            "articles": topic.get("articles", []),
            "silent_outlets": topic.get("silent_outlets", {}),
            "framing_differences": topic.get("framing_differences", {}),
            "lead_articles": topic.get("lead_articles", {}),
            "linguistic_framing": topic.get("linguistic_framing", {}),
        }
    ), 200


@app.route("/dashboard/topic_enrichment/<int:topic_id>", methods=["GET"])
def get_topic_enrichment(topic_id):
    # ── Check cache first ────────────────────────────────────────────────────
    now = _time.time()
    cached = _ENRICHMENT_CACHE.get(topic_id)
    if cached and (now - cached["ts"]) < _ENRICHMENT_TTL:
        print(f"[enrichment cache] HIT for topic {topic_id}")
        return jsonify(cached["data"]), 200

    # ── Cache miss — fetch base topic data ───────────────────────────────────
    topics_data, error = fetch_topics_data()
    if error:
        return jsonify({"error": error}), 404

    topic = next((t for t in topics_data if t["id"] == topic_id), None)
    if not topic:
        return jsonify({"error": "Topic not found"}), 404

    # ── Perform LLM enrichment ───────────────────────────────────────────────
    svc = get_summary_service()
    if svc:
        topic = svc.enrich_topic_with_deep_summary(topic)
        topic = svc.generate_comparative_analysis(topic)

    result = {
        "contextual_insight": topic.get("contextual_insight", ""),
        "comparative_analysis": topic.get("comparative_analysis", ""),
        "has_deep_summary": topic.get("has_deep_summary", False),
    }

    # ── Store in cache ───────────────────────────────────────────────────────
    _ENRICHMENT_CACHE[topic_id] = {"data": result, "ts": now}
    print(f"[enrichment cache] STORED for topic {topic_id}")

    return jsonify(result), 200


@app.route("/dashboard/trending_keywords", methods=["GET"])
def trending_keywords():
    df = _safe_read_csv(SCRAPED_DATA_PATH)
    if df is None or len(df) == 0:
        return jsonify({"keywords": []}), 200
    df = df.fillna("")
    return jsonify({"keywords": extract_keywords(df, top_k=10)}), 200


@app.route("/dashboard/topic_coverage", methods=["GET"])
def topic_coverage():
    df = _safe_read_csv(SCRAPED_DATA_PATH)
    if df is None or len(df) == 0:
        return jsonify({"topics": [], "coverage": []}), 200

    df = df.fillna("")
    if "topic" not in df.columns or "source" not in df.columns:
        return jsonify({"topics": [], "coverage": []}), 200

    df["topic"] = df["topic"].astype(str).str.strip()
    df.loc[df["topic"] == "", "topic"] = "General"

    selected_topic = request.args.get("topic", "").strip()
    if selected_topic:
        df = df[df["topic"] == selected_topic]

    counts = df.groupby("source").size().sort_values(ascending=False).head(50)
    coverage = [{"source": str(src), "count": int(cnt)} for src, cnt in counts.items()]
    topics = sorted(df["topic"].unique().tolist())

    return jsonify({"topics": topics, "coverage": coverage}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "analyzer"}), 200

@app.route("/", methods=["GET"])
def root():
    return {
        "service": "analyzer",
        "status": "ok",
        "message": "Analyzer API is running"
    }, 200

# ---------------------------------------------------------------------------
# NEW — called by bias-classifier sidecar after upload_csv()
# ---------------------------------------------------------------------------

@app.route("/dashboard/cluster", methods=["POST"])
def cluster_and_save():
    """
    Called once per day by the ECS bias-classifier container after it finishes
    uploading the cleaned CSV to S3.

    Steps:
      1. Force re-download fresh CSV from S3 (bypass local 12h cache)
      2. Run TopicClusteredService → assign cluster_id to every article
      3. Write cluster_id back into the local CSV file
      4. Upload enriched CSV to S3 (overwrites cleaned CSV)
      5. Bust in-memory topics cache so next /dashboard/topics
         request reads the new cluster_ids immediately

    Returns JSON: { "status": "ok", "articles": N, "clusters": N }
    """
    import boto3
    import analyzer.helpers.data_helpers as _dh
    from .core.services import get_topic_service

    S3_BUCKET  = os.environ.get("S3_BUCKET")
    S3_KEY     = os.environ.get("SCRAPER_S3_KEY", "scraped_articles/scraped_articles.csv")
    AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-1")

    if not S3_BUCKET:
        return jsonify({"error": "S3_BUCKET env var not set"}), 500

    os.makedirs(os.path.dirname(SCRAPED_DATA_PATH), exist_ok=True)

    # ── 1. Force download fresh CSV from S3 ───────────────────────────────────
    # Bypass the 12h TTL — we know S3 just got a new file from bias-classifier.
    try:
        s3 = boto3.client("s3", region_name=AWS_REGION)
        s3.download_file(S3_BUCKET, S3_KEY, SCRAPED_DATA_PATH)
        print(f"[cluster] Downloaded fresh CSV from s3://{S3_BUCKET}/{S3_KEY}")
    except Exception as e:
        return jsonify({"error": f"S3 download failed: {e}"}), 500

    # ── 2. Read CSV ───────────────────────────────────────────────────────────
    df = _safe_read_csv(SCRAPED_DATA_PATH)
    if df is None or df.empty:
        return jsonify({"error": "CSV is empty after download"}), 500

    # ── 3. Cluster ────────────────────────────────────────────────────────────
    try:
        svc    = get_topic_service()
        topics = svc.cluster_articles(df)
    except Exception as e:
        return jsonify({"error": f"Clustering failed: {e}"}), 500

    # Build title → cluster_id lookup
    cluster_map: dict[str, str] = {}
    for topic in topics:
        cid = str(topic["id"])
        for article in topic.get("articles", []):
            title = article.get("title", "")
            if title:
                cluster_map[title] = cid

    df["cluster_id"] = df["title"].map(cluster_map).fillna("unclustered")

    # ── 4. Save locally + upload enriched CSV to S3 ───────────────────────────
    df.to_csv(SCRAPED_DATA_PATH, index=False)

    try:
        s3.upload_file(SCRAPED_DATA_PATH, S3_BUCKET, S3_KEY)
        print(f"[cluster] Uploaded enriched CSV → s3://{S3_BUCKET}/{S3_KEY}")
    except Exception as e:
        return jsonify({"error": f"S3 upload failed: {e}"}), 500

    # ── 5. Bust in-memory topics cache ────────────────────────────────────────
    _dh._topics_cache           = None
    _dh._topics_cache_time      = 0.0
    _dh._topics_cache_csv_mtime = 0.0

    print(f"[cluster] Done. {len(topics)} clusters from {len(df)} articles.")
    return jsonify({
        "status":   "ok",
        "articles": len(df),
        "clusters": len(topics),
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8017)
