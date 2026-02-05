import pandas as pd
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import CountVectorizer
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import os
import requests
import json
import time


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

        self.perplexity_api_key = os.getenv("API_KEY")

    def _summarize_with_perplexity(self, text_content):
        if not self.perplexity_api_key:
            return None

        url = "https://api.perplexity.ai/chat/completions"
        payload = {
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a specialized news summarizer. Your task is to summarize the following news articles into a single, comprehensive event summary paragraph. \n\nCRITICAL STRICTNESS RULES:\n1. USE ONLY THE CONTENT PROVIDED IN THE 'USER' MESSAGE.\n2. DO NOT USE ANY EXTERNAL KNOWLEDGE, INTERNET SEARCH, OR OUTSIDE SOURCES.\n3. If the provided text does not contain enough information, state 'Insufficient information to generate summary'.\n4. Focus on the core facts reported in the provided text.",
                },
                {"role": "user", "content": text_content},
            ],
            "max_tokens": 300,
            "temperature": 0.2,
            "return_citations": False,
        }
        headers = {
            "Authorization": f"Bearer {self.perplexity_api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(3):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
                elif response.status_code == 429:
                    wait_time = 2 ** (attempt + 1)
                    print(f"Perplexity Rate Limit (429). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(
                        f"Perplexity API Error: {response.status_code} - {response.text}"
                    )
                    # Don't retry for other client errors (4xx)
                    if 400 <= response.status_code < 500:
                        return None
            except Exception as e:
                print(f"Perplexity API Request Failed: {e}")
                time.sleep(1)

        return None

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

            selection_bias_alert = None
            # Logic: If trending (high total) but ZERO coverage from one side -> Selection Bias
            if total > 5:
                if left_total == 0:
                    selection_bias_alert = (
                        "High Selection Bias: Ignored by Left Sources"
                    )
                elif right_total == 0:
                    selection_bias_alert = (
                        "High Selection Bias: Ignored by Right Sources"
                    )

            # --- Framing Gap Analysis (Distinctive Keywords) ---
            # Collect headlines
            left_headlines = []
            right_headlines = []

            for _, row in group.iterrows():
                b = str(row.get("bias", "")).lower()
                title = str(row.get("title", ""))
                if "left" in b:
                    left_headlines.append(title)
                elif "right" in b:
                    right_headlines.append(title)

            framing_gap = {}
            if left_headlines and right_headlines:
                try:
                    # Helper to get top words
                    def get_top_words(corpus, other_corpus):
                        # Words common in A but rare in B
                        # Simple approach: simple frequency in A, stop words removed
                        vec = CountVectorizer(
                            stop_words="english", ngram_range=(1, 1), max_features=20
                        )
                        try:
                            counts = vec.fit_transform(corpus).toarray().sum(axis=0)
                            feature_names = vec.get_feature_names_out()

                            # Get word frequencies for A
                            freq_a = dict(zip(feature_names, counts))

                            # Check existence in B (naive boolean check or low freq check)
                            other_text = " ".join(other_corpus).lower()

                            distinctive = []
                            for word, count in sorted(
                                freq_a.items(), key=lambda x: x[1], reverse=True
                            ):
                                if (
                                    word not in other_text
                                    or other_text.count(word) < count * 0.2
                                ):  # Simple heuristic
                                    distinctive.append(word)
                                if len(distinctive) >= 3:
                                    break
                            return distinctive
                        except ValueError:
                            # Corpus too small or empty vocab
                            return []

                    left_keywords = get_top_words(left_headlines, right_headlines)
                    right_keywords = get_top_words(right_headlines, left_headlines)

                    if left_keywords and right_keywords:
                        framing_gap = {
                            "left_keywords": left_keywords,
                            "right_keywords": right_keywords,
                        }
                except Exception as e:
                    print(f"Error in framing analysis: {e}")

            # --- Initial Insight Construction (Pre-Deep Summary) ---
            insight = f"This story is covered by {total} unique sources."

            # Consensus logic refinement
            if consensus_score < 5.0:
                insight += " There is significant disagreement on the core facts across sources (Low Consensus)."
            elif consensus_score > 8.0:
                insight += " Sources largely agree on the core facts (High Consensus)."
            else:
                insight += " There is moderate agreement across sources."

            if polarization_alert:
                insight += f" Coverage is {polarization_alert.lower()}."

            if framing_gap:
                l_words = ", ".join(
                    [f"'{w}'" for w in framing_gap["left_keywords"][:2]]
                )
                r_words = ", ".join(
                    [f"'{w}'" for w in framing_gap["right_keywords"][:2]]
                )
                insight += f" Left-leaning sources tend to emphasize {l_words}, while Right-leaning sources focus on {r_words}."

            # Fallback if no specific insight
            if len(insight) < 60:
                insight += " This topic is receiving broad attention."

            # --- Default/Fallback Summary ---
            summary_text = f"Event Summary: {group.iloc[0].get('title', 'News Event')}"

            # Try Local Transformers (Headlines) as robust fallback
            if self.summarizer and total > 1:
                try:
                    unique_titles = list(set(group_titles))[:15]
                    input_text = ". ".join(unique_titles)[:3000]
                    summary_result = self.summarizer(
                        input_text, max_length=60, min_length=20, do_sample=False
                    )
                    if summary_result:
                        summary_text = (
                            f"Event Summary: {summary_result[0]['summary_text']}"
                        )
                except Exception as e:
                    print(f"Local Summarization failed: {e}")

            # Define representative article for title usage
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
                "selection_bias_alert": selection_bias_alert,
                "framing_gap": framing_gap,
                "base_insight": insight,  # Store base insight separately
                "base_summary": summary_text,  # Store base summary
                "contextual_insight": f"{summary_text} coverage analysis: {insight}",  # Default value
                "articles": group[
                    ["title", "source", "url", "bias", "page_text"]
                ].to_dict(orient="records"),  # Include page_text for second pass
            }
            clustered_topics.append(topic)

        # 4. Sort by source count (hottest topics first)
        clustered_topics.sort(key=lambda x: x["source_count"], reverse=True)

        return clustered_topics

    def enrich_topic_with_deep_summary(self, topic):
        """
        Generates a deep summary for a single topic using Perplexity API.
        Modifies the topic dictionary in-place.
        """
        if not self.perplexity_api_key:
            return topic

        try:
            # Reconstruct context from articles dict
            arts = topic.get("articles", [])

            # Select unique articles (up to 3) for context
            seen_titles = set()
            unique_arts = []
            for a in arts:
                title = a.get("title", "")
                if title not in seen_titles:
                    unique_arts.append(a)
                    seen_titles.add(title)
                if len(unique_arts) >= 3:
                    break

            combined_text = ""
            for art in unique_arts:
                # Prioritize page_text if available (it might be in the dict if we preserved it)
                # Note: app.py might have stripped it, so we rely on what's passed in 'topic'
                text_snippet = str(art.get("page_text", ""))

                # If page_text is missing/empty, we can't do a "Deep" summary strictly.
                # But let's check. If it's short, we fallback to title, but that violates "Strict content"
                # if we want deep insights. However, strictly speaking, title IS provided content.
                if len(text_snippet) < 50:
                    text_snippet = art.get("title", "")

                text_snippet = text_snippet[:1500]
                combined_text += (
                    f"\n\nSource ({art.get('source', 'Unknown')}): {text_snippet}"
                )

            if len(combined_text) > 100:
                print(f"Generating On-Demand Summary for Topic {topic['id']}...")
                perplexity_summary = self._summarize_with_perplexity(combined_text)

                if perplexity_summary:
                    deep_summary_text = f"Event Summary (Deep AI): {perplexity_summary}"
                    # Update the insight
                    base_insight = topic.get("base_insight", "")
                    topic["contextual_insight"] = (
                        f"{deep_summary_text} coverage analysis: {base_insight}"
                    )
                    topic["has_deep_summary"] = True
        except Exception as e:
            print(f"Deep summarization failed for topic {topic['id']}: {e}")

        return topic
