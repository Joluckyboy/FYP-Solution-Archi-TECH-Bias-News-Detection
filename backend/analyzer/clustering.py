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

            # --- Bias Aggregation ---
            bias_counts = {
                "left": 0,
                "leaning_left": 0,
                "center": 0,
                "leaning_right": 0,
                "right": 0,
            }

            for _, row in group.iterrows():
                b = str(row.get("bias", "")).lower()
                # Normalize varied bias strings if necessary
                if b == "left":
                    bias_counts["left"] += 1
                elif b == "right":
                    bias_counts["right"] += 1
                elif b == "center":
                    bias_counts["center"] += 1
                elif b == "leaning-left" or "left" in b:  # looser matching
                    bias_counts["leaning_left"] += 1
                elif b == "leaning-right" or "right" in b:
                    bias_counts["leaning_right"] += 1
                else:
                    bias_counts["center"] += 1

            total = len(group)
            bias_distribution = {
                k: round((v / total) * 100, 1) for k, v in bias_counts.items()
            }

            # --- Consensus Score (Semantic Similarity) ---
            # Calculate average pairwise cosine similarity within the cluster
            if total > 1:
                # Get embeddings for this cluster's articles
                cluster_indices = group.index.tolist()
                # We need to map original DF indices to the embeddings array indices
                # Assuming 'articles_df' order matched 'embeddings' order 1-to-1:
                # However, we passed a subset to cluster_articles, let's assume index alignment for now.
                # Re-encoding just for the cluster is safer to avoid index confusion if subsetting happened outside.

                # Optimization: For now, lets just re-calculate centroid distance for simplicity
                group_titles = group["title"].fillna("").tolist()
                group_emb = self.model.encode(group_titles, convert_to_tensor=True)

                # Calculate centroid
                centroid = group_emb.mean(dim=0)

                # Review: Cosine similarity to centroid
                from sentence_transformers.util import cos_sim

                scores = cos_sim(group_emb, centroid)
                consensus_score = float(scores.mean()) * 10  # Scale 0-10
            else:
                consensus_score = (
                    10.0  # Single article is in perfect consensus with itself
                )

            # --- Polarization & Alerts ---
            left_total = bias_counts["left"] + bias_counts["leaning_left"]
            right_total = bias_counts["right"] + bias_counts["leaning_right"]

            polarization_alert = None
            if total > 5:  # Threshold to avoid noise
                if left_total > right_total * 2 and right_total < total * 0.15:
                    polarization_alert = "Heavily skewed towards Left sources"
                elif right_total > left_total * 2 and left_total < total * 0.15:
                    polarization_alert = "Heavily skewed towards Right sources"

            under_reported_alert = None
            # logic: if trending (high total) but near zero in one spectrum
            if total > 5:
                if left_total == 0:
                    under_reported_alert = "Invisible to Left-Leaning audiences"
                elif right_total == 0:
                    under_reported_alert = "Invisible to Right-Leaning audiences"

            # --- Contextual Insight ---
            insight = f"This story is covered by {total} sources."
            if consensus_score > 8.5:
                insight += " Sources show high agreement on the core facts."
            elif consensus_score < 5.0:
                insight += (
                    " There is significant variation in how headlines frame this story."
                )

            if polarization_alert:
                insight += f" It is {polarization_alert.lower()}."

            # --- Representative Article & Date ---
            rep = group.iloc[0]
            dates = pd.to_datetime(group["date"], errors="coerce")
            latest_date = dates.max()
            latest_date_str = (
                latest_date.strftime("%Y-%m-%d") if not pd.isnull(latest_date) else ""
            )

            topic = {
                "id": int(cluster_id),
                "title": rep["title"],
                "source_count": int(total),
                "bias_distribution": bias_distribution,
                "latest_date": latest_date_str,
                "consensus_score": round(consensus_score, 1),
                "polarization_alert": polarization_alert,
                "under_reported_alert": under_reported_alert,
                "contextual_insight": insight,
                "articles": group[["title", "source", "url", "bias"]].to_dict(
                    orient="records"
                ),
            }
            clustered_topics.append(topic)

        # Sort by source count (hottest topics first)
        clustered_topics.sort(key=lambda x: x["source_count"], reverse=True)

        return clustered_topics
