import pandas as pd
from typing import Any
from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import CountVectorizer
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import os


class TopicClusteredService:
    def __init__(self):
        # Load the S-BERT model. This might take a moment on first run.
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        try:
            # Initialize summarization pipeline (lightweight model)
            self.summarizer = pipeline(
                "summarization", model="sshleifer/distilbart-cnn-12-6"
            )
        except Exception as e:
            print(f"Warning: Could not load summarization model: {e}")
            self.summarizer = None

        self.api_key = os.getenv("API_KEY")

    def cluster_articles(
        self, articles_df: pd.DataFrame, distance_threshold: float = 0.5
    ) -> list[dict[str, Any]]:
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
        embeddings = self._generate_embeddings(articles_df)

        # 2. Cluster
        labels = self._perform_clustering(embeddings, distance_threshold)

        # 3. Group & Aggregate
        articles_df["cluster"] = labels
        clustered_topics = []

        for cluster_id in sorted(list(set(labels))):
            group = articles_df[articles_df["cluster"] == cluster_id]
            topic = self._process_cluster_group(cluster_id, group)
            clustered_topics.append(topic)

        # 4. Sort by source count (hottest topics first)
        clustered_topics.sort(key=lambda x: x["source_count"], reverse=True)

        return clustered_topics

    def _generate_embeddings(self, articles_df):
        titles = articles_df["title"].fillna("").tolist()
        embeddings = self.model.encode(titles, convert_to_tensor=True)
        # Move to CPU for sklearn
        embeddings = embeddings.cpu().numpy()

        # Normalize embeddings for cosine distance to work with Euclidean metric
        from sklearn.preprocessing import normalize

        return normalize(embeddings)

    def _perform_clustering(self, embeddings, distance_threshold):
        # Using cosine distance: 1 - cosine_similarity
        # Since we normalized, euclidean distance on unit sphere is related to cosine.
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=distance_threshold,
            metric="euclidean",
            linkage="average",
        )
        return clustering.fit_predict(embeddings)

    def _process_cluster_group(
        self, cluster_id: int, group: pd.DataFrame
    ) -> dict[str, Any]:
        bias_counts = self._calculate_bias_counts(group)
        total = len(group)
        bias_distribution = {
            k: round((v / total) * 100, 1) for k, v in bias_counts.items()
        }

        consensus_score = self._calculate_consensus(group, total)
        polarization_alert, selection_bias_alert = self._check_alerts(
            bias_counts, total
        )
        framing_gap = self._analyze_framing_gap(group)

        insight = self._generate_insight(
            total, consensus_score, polarization_alert, framing_gap
        )

        # Default/Fallback Summary
        summary_text = f"Event Summary: {group.iloc[0].get('title', 'News Event')}"

        try:
            summary_text = f"{group.iloc[0].get('title', 'News Event')}"
        except Exception:
            summary_text = "News Event"

        rep = group.iloc[0]
        # Date handling
        dates = pd.to_datetime(group["date"], errors="coerce")
        latest_date = dates.max()
        latest_date_str = (
            latest_date.strftime("%Y-%m-%d") if not pd.isnull(latest_date) else ""
        )

        return {
            "id": int(cluster_id),
            "title": rep["title"],
            "source_count": int(total),
            "bias_distribution": bias_distribution,
            "latest_date": latest_date_str,
            "framing_gap": framing_gap,
            "base_insight": insight,
            "base_summary": summary_text,
            "contextual_insight": f"{summary_text}\n\nCoverage Analysis: {insight}",
            "articles": group[["title", "source", "url", "bias", "page_text"]].to_dict(
                orient="records"
            ),
        }

    def _calculate_bias_counts(self, group):
        counts = {
            "left": 0,
            "leaning_left": 0,
            "center": 0,
            "leaning_right": 0,
            "right": 0,
        }
        for _, row in group.iterrows():
            b = str(row.get("bias", "")).lower()
            if b == "left":
                counts["left"] += 1
            elif b == "right":
                counts["right"] += 1
            elif b == "center":
                counts["center"] += 1
            elif "left" in b:
                counts["leaning_left"] += 1
            elif "right" in b:
                counts["leaning_right"] += 1
            else:
                counts["center"] += 1
        return counts

    def _calculate_consensus(self, group, total):
        # Calculate average pairwise cosine similarity within the cluster
        if total <= 1:
            return 10.0

        # Optimization: Re-calculate centroid distance for simplicity
        group_titles = group["title"].fillna("").tolist()
        group_emb = self.model.encode(group_titles, convert_to_tensor=True)
        centroid = group_emb.mean(dim=0)

        from sentence_transformers.util import cos_sim

        scores = cos_sim(group_emb, centroid)
        return float(scores.mean()) * 10

    def _check_alerts(self, bias_counts, total):
        polarization_alert = None
        selection_bias_alert = None

        if total > 5:
            left_total = bias_counts["left"] + bias_counts["leaning_left"]
            right_total = bias_counts["right"] + bias_counts["leaning_right"]

            if left_total > right_total * 2 and right_total < total * 0.15:
                polarization_alert = "Heavily skewed towards Left sources"
            elif right_total > left_total * 2 and left_total < total * 0.15:
                polarization_alert = "Heavily skewed towards Right sources"

            if left_total == 0:
                selection_bias_alert = "High Selection Bias: Ignored by Left Sources"
            elif right_total == 0:
                selection_bias_alert = "High Selection Bias: Ignored by Right Sources"

        return polarization_alert, selection_bias_alert

    def _analyze_framing_gap(self, group):
        left_headlines = []
        right_headlines = []
        for _, row in group.iterrows():
            b = str(row.get("bias", "")).lower()
            title = str(row.get("title", ""))
            if "left" in b:
                left_headlines.append(title)
            elif "right" in b:
                right_headlines.append(title)

        if not (left_headlines and right_headlines):
            return {}

        try:
            l_kw = self._get_unique_keywords(left_headlines, right_headlines)
            r_kw = self._get_unique_keywords(right_headlines, left_headlines)
            if l_kw and r_kw:
                return {"left_keywords": l_kw, "right_keywords": r_kw}
        except Exception as e:
            print(f"Error in framing analysis: {e}")
        return {}

    def _get_unique_keywords(self, target_corpus, reference_corpus):
        # Words common in A but rare in B
        try:
            vec = CountVectorizer(
                stop_words="english", ngram_range=(1, 1), max_features=20
            )
            counts = vec.fit_transform(target_corpus).toarray().sum(axis=0)
            feature_names = vec.get_feature_names_out()
            freq_a = dict(zip(feature_names, counts))

            other_text = " ".join(reference_corpus).lower()
            distinctive = []

            for word, count in sorted(freq_a.items(), key=lambda x: x[1], reverse=True):
                # Simple heuristic
                if word not in other_text or other_text.count(word) < count * 0.2:
                    distinctive.append(word)
                if len(distinctive) >= 3:
                    break
            return distinctive
        except ValueError:
            # Corpus too small or empty vocab
            return []

    def _generate_insight(
        self, total, consensus_score, polarization_alert, framing_gap
    ):
        # insight = f"This story is covered by {total} unique sources."
        insight = ""
        if total > 1:
            if consensus_score < 5.0:
                insight += " There is significant disagreement on the core facts across sources (Low Consensus)."
            elif consensus_score > 8.0:
                insight += " Sources largely agree on the core facts (High Consensus)."
            else:
                insight += " There is moderate agreement across sources."

        if polarization_alert:
            insight += f" Coverage is {polarization_alert.lower()}."

        if framing_gap:
            l_words = ", ".join([f"'{w}'" for w in framing_gap["left_keywords"][:2]])
            r_words = ", ".join([f"'{w}'" for w in framing_gap["right_keywords"][:2]])
            insight += f" Left-leaning sources tend to emphasize {l_words}, while Right-leaning sources focus on {r_words}."

        if len(insight) < 60:
            insight += " This topic is receiving broad attention."
        return insight

    def _generate_local_summary(self, titles):
        try:
            unique_titles = list(set(titles))[:15]
            input_text = ". ".join(unique_titles)[:3000]
            summary_result = self.summarizer(
                input_text, max_length=60, min_length=20, do_sample=False
            )
            if summary_result:
                return summary_result[0]["summary_text"]
        except Exception as e:
            print(f"Local Summarization failed: {e}")
        return None

    def cluster_articles_fallback(
        self, articles_df: pd.DataFrame, error_detail: str = ""
    ) -> list[dict[str, Any]]:
        """
        Fallback clustering using simple Jaccard similarity when the main model fails.
        """
        print("Using Fallback Jaccard Grouping...")
        # Use a smaller subset for fallback to ensure speed
        subset = articles_df.head(200).fillna("")
        groups = []

        def calculate_similarity(text1, text2):
            set1 = set(text1.lower().split())
            set2 = set(text2.lower().split())
            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))
            return intersection / union if union > 0 else 0

        for _, row in subset.iterrows():
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
                    "framing_gap": None,
                    "base_insight": "Fallback analysis (Jaccard)",
                    "base_summary": f"Event Summary: {group['title']}",
                    "contextual_insight": f"AI analysis unavailable (Fallback Mode). Error: {error_detail}"
                    if error_detail
                    else "AI analysis unavailable (Fallback Mode).",
                    "articles": articles_list,
                }
            )

        topics.sort(key=lambda x: x["source_count"], reverse=True)
        return topics
