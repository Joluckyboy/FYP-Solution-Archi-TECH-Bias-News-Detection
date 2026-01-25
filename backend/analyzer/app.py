from flask import Flask, request, jsonify
import pandas as pd
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


@app.route("/dashboard/topics", methods=["GET"])
def dashboard_topics():
    """Get topics (articles) for the dashboard from the Kaggle dataset"""
    try:
        if not os.path.exists(DATASET_PATH):
            return {"error": "Dataset not found"}, 404

        df = pd.read_csv(DATASET_PATH)

        # --- Try Advanced Clustering (Semantic) ---
        try:
            print(f"Running clustering on {len(df)} articles...")
            # Use a sample for speed (e.g. 500 articles), or full dataset if small
            subset = df.head(500).fillna("")

            # Direct call to service
            topics_data = service.cluster_articles(subset)
            print(f"Generated {len(topics_data)} topics.")

            # Transform to frontend expected format
            formatted_topics = []
            for t in topics_data:
                headline = t["title"]
                short_headline = (
                    (headline[:30] + "..") if len(headline) > 30 else headline
                )
                import urllib.parse

                encoded_text = urllib.parse.quote(short_headline)
                image_url = f"https://placehold.co/600x400?text={encoded_text}"

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
            print(f"Failed to contact Analyzer service, using local fallback: {e}")

        # --- Fallback: Simple Jaccard Grouping ---
        print("Using Fallback Jaccard Grouping...")
        # Take a larger sample to find matches
        subset = df.head(200).fillna("")

        # Grouping Logic
        groups = []  # List of dicts: { 'title': '...', 'articles': [...], 'bias_counts': {...} }

        def calculate_similarity(text1, text2):
            # Simple Jaccard similarity on lowercased words
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

            # Check if this article belongs to an existing group
            match_found = False
            for group in groups:
                # Check similarity with the group's "representative" title (the first one)
                sim = calculate_similarity(title, group["title"])
                if sim > 0.3:  # Threshold for similarity
                    group["articles"].append(row)
                    group["source_count"] += 1

                    # Update bias counts
                    if "left" in bias_val:
                        group["bias_counts"]["left"] += 1
                    elif "right" in bias_val:
                        group["bias_counts"]["right"] += 1
                    else:
                        group["bias_counts"]["center"] += 1

                    match_found = True
                    break

            if not match_found:
                # Create new group
                new_group = {
                    "title": title,
                    "articles": [row],
                    "source_count": 1,
                    "bias_counts": {"left": 0, "center": 0, "right": 0},
                    "date": str(row.get("date", "")),
                }
                if "left" or "leaning_left" in bias_val:
                    new_group["bias_counts"]["left"] += 1
                elif "right" or "leaning_right" in bias_val:
                    new_group["bias_counts"]["right"] += 1
                else:
                    new_group["bias_counts"]["center"] += 1
                groups.append(new_group)

        # Format groups for frontend (Fallback)
        topics = []
        for i, group in enumerate(groups):
            total = group["source_count"]
            distribution = {
                "left": (group["bias_counts"]["left"] / total) * 100,
                "center": (group["bias_counts"]["center"] / total) * 100,
                "right": (group["bias_counts"]["right"] / total) * 100,
            }

            headline = group["title"]
            short_headline = (headline[:30] + "..") if len(headline) > 30 else headline
            import urllib.parse

            encoded_text = urllib.parse.quote(short_headline)
            image_url = f"https://placehold.co/600x400?text={encoded_text}"

            topics.append(
                {
                    "id": i,
                    "title": headline,
                    "image": image_url,
                    "sourceCount": group["source_count"],
                    "biasDistribution": distribution,
                    "date": group["date"],
                }
            )

        topics.sort(key=lambda x: x["sourceCount"], reverse=True)
        return {"topics": topics[:50]}, 200

    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "analyzer"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8017)
