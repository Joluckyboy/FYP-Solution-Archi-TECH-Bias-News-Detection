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
                "image": t.get("image") or "https://placehold.co/600x400?text=No+Image",
                "sourceCount": t.get("source_count", 0),
                "biasDistribution": t.get(
                    "bias_distribution", dict(DEFAULT_BIAS_DISTRIBUTION)
                ),
                "date": t.get("latest_date", ""),
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
    topics_data, error = fetch_topics_data()
    if error:
        return jsonify({"error": error}), 404

    topic = next((t for t in topics_data if t["id"] == topic_id), None)
    if not topic:
        return jsonify({"error": "Topic not found"}), 404

    # Perform LLM enrichment
    svc = get_summary_service()
    if svc:
        topic = svc.enrich_topic_with_deep_summary(topic)
        topic = svc.generate_comparative_analysis(topic)

    return jsonify(
        {
            "contextual_insight": topic.get("contextual_insight", ""),
            "comparative_analysis": topic.get("comparative_analysis", ""),
            "has_deep_summary": topic.get("has_deep_summary", False),
        }
    ), 200


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8017)
