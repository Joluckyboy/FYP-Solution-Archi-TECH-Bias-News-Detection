from flask import Flask, request, jsonify
import pandas as pd

try:
    from .clustering import TopicClusteredService
    from .summary import SummaryService
except ImportError:
    from clustering import TopicClusteredService
    from summary import SummaryService
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Initialize service (loads model once on startup)
print("Loading Analyzer Model...")
service = TopicClusteredService()
summary = SummaryService()
print("Analyzer Model Loaded.")

# Path to the Kaggle dataset
DATASET_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "datasets",
    "kaggle news articles for political bias classification.csv",
)


def _fetch_topics_data():
    """Helper to fetch and cluster topics from the dataset"""
    if not os.path.exists(DATASET_PATH):
        return None, "Dataset not found"

    df = pd.read_csv(DATASET_PATH)

    # --- Try Advanced Clustering (Semantic) ---
    try:
        print(f"Running clustering on {len(df)} articles...")
        # Use a sample for speed (e.g. 500 articles)
        subset = df.head(500).fillna("")
        if "site" in subset.columns:
            subset = subset.rename(columns={"site": "source"})

        # Direct call to service
        topics_data = service.cluster_articles(subset)
        print(f"Generated {len(topics_data)} topics.")
        return topics_data, None

    except Exception as e:
        print(f"Failed to contact Analyzer service, using local fallback: {e}")
        error_detail = str(e)

        # --- Fallback: Simple Jaccard Grouping (Delegated to Service) ---
        try:
            print("Using Fallback Jaccard Grouping (Service)...")
            topics = service.cluster_articles_fallback(df, error_detail)
            return topics, None
        except Exception as fb_e:
            print(f"Fallback clustering also failed: {fb_e}")
            return None, f"Clustering failed: {e}. Fallback failed: {fb_e}"


@app.route("/analyze/topics", methods=["POST"])
def analyze_topics():
    try:
        data = request.json
        if not data or "articles" not in data:
            return jsonify({"error": "Missing articles data"}), 400

        # Expecting 'articles' to be a list of dicts or DataFrame-like structure
        articles = data["articles"]
        df = pd.DataFrame(articles)

        # Run clustering
        topics = service.cluster_articles(df)

        return jsonify({"topics": topics}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/dashboard/topics", methods=["GET"])
def dashboard_topics():
    """Get topics (articles) for the dashboard from the Kaggle dataset"""
    topics_data, error = _fetch_topics_data()
    if error:
        return {"error": error}, 404

    try:
        # Transform to frontend expected format (lightweight)
        formatted_topics = []
        for t in topics_data:
            headline = t["title"]
            short_headline = (headline[:30] + "..") if len(headline) > 30 else headline
            import urllib.parse

            encoded_text = urllib.parse.quote(short_headline)
            image_url = f"https://placehold.co/600x400?text={encoded_text}"

            # Map leaning keys if needed, but assuming standard keys are fine
            formatted_topics.append(
                {
                    "id": t["id"],
                    "title": headline,
                    "image": image_url,
                    "sourceCount": t["source_count"],
                    "biasDistribution": t["bias_distribution"],
                    "date": t.get("latest_date", ""),
                }
            )

        return {"topics": formatted_topics[:50]}, 200

    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/dashboard/topic_details/<int:topic_id>", methods=["GET"])
def get_topic_details(topic_id):
    """Get full details for a specific topic"""
    topics_data, error = _fetch_topics_data()
    if error:
        return {"error": error}, 404

    # Find the topic with the matching ID
    topic = next((t for t in topics_data if t["id"] == topic_id), None)

    if not topic:
        return {"error": "Topic not found"}, 404

    # Enhance topic with image if needed
    headline = topic["title"]
    short_headline = (headline[:30] + "..") if len(headline) > 30 else headline
    import urllib.parse

    encoded_text = urllib.parse.quote(short_headline)
    topic["image"] = f"https://placehold.co/600x400?text={encoded_text}"

    # --- On-Demand Deep Summarization ---
    # Only run if not already summarized (though our simplified clustering doesn't pre-summarize anymore)
    if "has_deep_summary" not in topic:
        print(f"Triggering on-demand summary for Topic {topic_id}")
        topic = summary.enrich_topic_with_deep_summary(topic)

    # Clean up page_text (large payload) from response
    if "articles" in topic:
        for a in topic["articles"]:
            if "page_text" in a:
                del a["page_text"]

    return topic, 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "analyzer"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8017)
