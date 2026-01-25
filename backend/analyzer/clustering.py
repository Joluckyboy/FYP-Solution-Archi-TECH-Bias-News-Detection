import pandas as pd
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sentence_transformers import SentenceTransformer


class TopicClusteredService:
    def __init__(self):
        # Load the S-BERT model. This might take a moment on first run.
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def cluster_articles(self, articles_df, distance_threshold=0.5):
        """
        Clusters articles based on title semantic similarity.

        Args:
            articles_df (pd.DataFrame): DataFrame containing 'title', 'source', 'bias'.
            distance_threshold (float): Threshold for Agglomerative Clustering.

        Returns:
            list: List of topic dictionaries.
        """
        if articles_df.empty:
            return []

        # 1. Generate Embeddings
        titles = articles_df["title"].fillna("").tolist()
        embeddings = self.model.encode(titles, convert_to_tensor=True)
        # Move to CPU for sklearn
        embeddings = embeddings.cpu().numpy()

        # Normalize embeddings for cosine distance to work with Euclidean metric
        # (S-BERT output is usually normalized, but good to ensure)
        from sklearn.preprocessing import normalize

        embeddings = normalize(embeddings)

        # 2. Cluster
        # Using cosine distance: 1 - cosine_similarity
        # Since we normalized, euclidean distance on unit sphere is related to cosine.
        # Ideally we use metric='cosine' but Agglomerative options vary by version.
        # 'euclidean' on normalized vectors is monotonic w.r.t cosine.
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=distance_threshold,
            metric="euclidean",
            linkage="average",
        )
        labels = clustering.fit_predict(embeddings)

        # 3. Group & Aggregate
        articles_df["cluster"] = labels
        clustered_topics = []

        for cluster_id in sorted(list(set(labels))):
            group = articles_df[articles_df["cluster"] == cluster_id]

            # Simple bias aggregation
            # We want 5 buckets: Left, Leaning Left, Center, Leaning Right, Right
            # Check dataset values usually: left, right, center, leaning-left, leaning-right
            bias_counts = {
                "left": 0,
                "leaning_left": 0,
                "center": 0,
                "leaning_right": 0,
                "right": 0,
            }

            for _, row in group.iterrows():
                b = str(row.get("bias", "")).lower()
                if b == "left":
                    bias_counts["left"] += 1
                elif b == "right":
                    bias_counts["right"] += 1
                elif b == "center":
                    bias_counts["center"] += 1
                elif b == "leaning-left":
                    bias_counts["leaning_left"] += 1
                elif b == "leaning-right":
                    bias_counts["leaning_right"] += 1
                else:
                    bias_counts["center"] += 1

            total = len(group)
            bias_distribution = {
                k: round((v / total) * 100, 1) for k, v in bias_counts.items()
            }

            # Representative article (first one or longest title?)
            # Let's take the first one for now
            rep = group.iloc[0]

            # Latest date
            dates = pd.to_datetime(group["date"], errors="coerce")
            latest_date = dates.max()
            if pd.isnull(latest_date):
                latest_date_str = ""
            else:
                latest_date_str = latest_date.strftime("%Y-%m-%d")

            topic = {
                "id": int(cluster_id),
                "title": rep["title"],
                "source_count": int(total),
                "bias_distribution": bias_distribution,
                "latest_date": latest_date_str,
                "articles": group[["title", "source", "url", "bias"]].to_dict(
                    orient="records"
                ),
            }
            clustered_topics.append(topic)

        # Sort by source count (hottest topics first)
        clustered_topics.sort(key=lambda x: x["source_count"], reverse=True)

        return clustered_topics
