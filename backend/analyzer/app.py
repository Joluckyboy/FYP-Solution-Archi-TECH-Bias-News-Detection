from flask import Flask, request, jsonify
import pandas as pd

try:
    from .clustering import TopicClusteredService
except ImportError:
    from clustering import TopicClusteredService
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Initialize service (loads model once on startup)
print("Loading Analyzer Model...")
service = TopicClusteredService()
print("Analyzer Model Loaded.")


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

        # Direct call to service
        topics_data = service.cluster_articles(subset)
        print(f"Generated {len(topics_data)} topics.")
        return topics_data, None

    except Exception as e:
        print(f"Failed to contact Analyzer service, using local fallback: {e}")

    # --- Fallback: Simple Jaccard Grouping ---
    print("Using Fallback Jaccard Grouping...")
    subset = df.head(200).fillna("")

    groups = []  # List of dicts

    def calculate_similarity(text1, text2):
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0

    for index, row in subset.iterrows():
        title = str(row.get("title", ""))
        if not title.strip():
            continue

        bias_val = str(row.get("bias", "center")).lower()

        match_found = False
        for group in groups:
            sim = calculate_similarity(title, group["title"])
            if sim > 0.3:
                group["articles"].append(row)
                group["source_count"] += 1
                if "left" in bias_val:
                    group["bias_counts"]["left"] += 1
                elif "right" in bias_val:
                    group["bias_counts"]["right"] += 1
                else:
                    group["bias_counts"]["center"] += 1
                match_found = True
                break

        if not match_found:
            new_group = {
                "title": title,
                "articles": [row],
                "source_count": 1,
                "bias_counts": {
                    "left": 0,
                    "leaning_left": 0,
                    "center": 0,
                    "leaning_right": 0,
                    "right": 0,
                },
                "date": str(row.get("date", "")),
            }
            if bias_val == "left":
                new_group["bias_counts"]["left"] += 1
            elif bias_val == "leaning-left":
                new_group["bias_counts"]["leaning_left"] += 1
            elif bias_val == "right":
                new_group["bias_counts"]["right"] += 1
            elif bias_val == "leaning-right":
                new_group["bias_counts"]["leaning_right"] += 1
            else:
                new_group["bias_counts"]["center"] += 1
            groups.append(new_group)

    # Format fallback groups to match service output structure
    topics = []
    for i, group in enumerate(groups):
        total = group["source_count"]
        distribution = {
            "left": (group["bias_counts"]["left"] / total) * 100,
            "leaning_left": (group["bias_counts"]["leaning_left"] / total) * 100,
            "center": (group["bias_counts"]["center"] / total) * 100,
            "leaning_right": (group["bias_counts"]["leaning_right"] / total) * 100,
            "right": (group["bias_counts"]["right"] / total) * 100,
        }

        # Convert df rows in articles to dict records
        articles_list = []
        for row in group["articles"]:
            articles_list.append(
                {
                    "title": row.get("title"),
                    "source": row.get("site"),
                    "url": row.get("url"),
                    "bias": row.get("bias"),
                }
            )

        topics.append(
            {
                "id": i,
                "title": group["title"],
                "source_count": group["source_count"],
                "bias_distribution": distribution,
                "latest_date": group["date"],
                # Placeholder for advanced analytics fields
                "consensus_score": None,  # Placeholder for fallback
                "polarization_alert": None,
                "under_reported_alert": None,
                "framing_gap": None,
                "contextual_insight": "AI analysis unavailable.",
                "articles": articles_list,
            }
        )

    topics.sort(key=lambda x: x["source_count"], reverse=True)
    return topics, None


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

    return topic, 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "analyzer"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8017)
