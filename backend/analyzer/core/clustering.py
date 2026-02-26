import pandas as pd
from typing import Any
from sklearn.cluster import AgglomerativeClustering
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
        self, articles_df: pd.DataFrame, distance_threshold: float = 1.0
    ) -> list[dict[str, Any]]:
        """
        Clusters articles based on title semantic similarity.

        Args:
            articles_df (pd.DataFrame): DataFrame containing 'title', 'source', 'political_bias'.
            distance_threshold (float): Threshold for Agglomerative Clustering.

        Returns:
            list: List of topic dictionaries.
        """
        if articles_df.empty:
            return []

        # 0. Filter non-English titles
        # A title is considered non-English if fewer than 80% of its
        # alphabetic characters are plain ASCII (catches Spanish/French/etc.)
        def _is_english(title: str) -> bool:
            alpha = [c for c in str(title) if c.isalpha()]
            if not alpha:
                return True  # no alphabetic chars — keep (don't filter numbers/symbols)
            ascii_ratio = sum(1 for c in alpha if ord(c) < 128) / len(alpha)
            return ascii_ratio >= 0.80

        original_count = len(articles_df)
        articles_df = articles_df[articles_df["title"].apply(_is_english)].reset_index(
            drop=True
        )
        filtered_count = original_count - len(articles_df)
        if filtered_count > 0:
            print(
                f"[clustering] Dropped {filtered_count} non-English article(s) before clustering."
            )

        if articles_df.empty:
            return []

        # 1. Generate Embeddings
        embeddings = self._generate_embeddings(articles_df)

        # 2. Cluster
        labels = self._perform_clustering(embeddings, distance_threshold)

        # 3. Group & Aggregate
        articles_df = articles_df.copy()
        articles_df["cluster"] = labels
        clustered_topics = []

        for cluster_id in sorted(list(set(labels))):
            mask = articles_df["cluster"] == cluster_id
            group = articles_df[mask]
            group_embeddings = embeddings[mask.values]  # numpy slice
            topic = self._process_cluster_group(cluster_id, group, group_embeddings)
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
        self, cluster_id: int, group: pd.DataFrame, group_embeddings=None
    ) -> dict[str, Any]:
        bias_counts = self._calculate_bias_counts(group)
        total = len(group)
        bias_distribution = {
            k: round((v / total) * 100, 1) for k, v in bias_counts.items()
        }

        rep = group.iloc[0]
        # Date handling
        dates = pd.to_datetime(group["published_at"], errors="coerce")
        latest_date = dates.max()
        latest_date_str = (
            latest_date.strftime("%Y-%m-%d") if not pd.isnull(latest_date) else ""
        )

        # Representative image: pick first article in the cluster that has one
        image_url = ""
        if "image_url" in group.columns:
            valid_imgs = group["image_url"].astype(str).str.strip()
            valid_imgs = valid_imgs[valid_imgs.str.startswith("http")]
            if not valid_imgs.empty:
                image_url = valid_imgs.iloc[0]

        summary_text = str(rep.get("title", "News Event"))

        silent_outlets = self._compute_silent_outlets(bias_counts, total)
        lead_articles = self._compute_lead_articles(group)
        framing_differences = self._compute_framing_differences(group)
        linguistic_framing = self._analyze_linguistic_framing(group)

        # Most common CSV topic category in the cluster (drives filter pills)
        topic_name = ""
        if "topic" in group.columns:
            mode_vals = group["topic"].dropna().mode()
            if not mode_vals.empty:
                topic_name = str(mode_vals.iloc[0])

        return {
            "id": int(cluster_id),
            "title": rep["title"],
            "image": image_url,
            "source_count": int(total),
            "bias_distribution": bias_distribution,
            "latest_date": latest_date_str,
            "contextual_insight": summary_text,
            "topic_name": topic_name,
            # Analysis fields
            "silent_outlets": silent_outlets,
            "lead_articles": lead_articles,
            "framing_differences": framing_differences,
            "linguistic_framing": linguistic_framing,
            "articles": group[
                ["title", "source", "url", "political_bias", "summary"]
            ].to_dict(orient="records"),
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
            b = str(row.get("political_bias", "")).lower()
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

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _compute_silent_outlets(self, bias_counts: dict, total: int) -> dict:
        """Flag bias categories with zero articles when others have significant coverage."""
        threshold = max(
            1, total // 4
        )  # at least 25% of cluster covered by another group
        left_vol = bias_counts["left"] + bias_counts["leaning_left"]
        right_vol = bias_counts["right"] + bias_counts["leaning_right"]
        center_vol = bias_counts["center"]

        return {
            "left_silent": left_vol == 0
            and (right_vol >= threshold or center_vol >= threshold),
            "right_silent": right_vol == 0
            and (left_vol >= threshold or center_vol >= threshold),
            "center_silent": center_vol == 0
            and (left_vol >= threshold or right_vol >= threshold),
        }

    def _compute_lead_articles(self, group: pd.DataFrame) -> dict:
        """Pick the most-recent article per bias leaning as the 'Lead' article."""
        result: dict = {"left": None, "center": None, "right": None}
        group_sorted = group.copy()
        group_sorted["_parsed_date"] = pd.to_datetime(
            group_sorted.get("published_at", group_sorted.get("date", None)),
            errors="coerce",
        )
        group_sorted = group_sorted.sort_values("_parsed_date", ascending=False)

        keep_cols = [
            c
            for c in [
                "title",
                "source",
                "url",
                "political_bias",
                "summary",
                "published_at",
            ]
            if c in group_sorted.columns
        ]

        for _, row in group_sorted.iterrows():
            b = str(row.get("political_bias", "")).lower()
            article = {col: row.get(col, "") for col in keep_cols}
            if ("left" in b) and result["left"] is None:
                result["left"] = article
            elif ("center" in b) and result["center"] is None:
                result["center"] = article
            elif ("right" in b) and result["right"] is None:
                result["right"] = article
            if all(v is not None for v in result.values()):
                break
        return result

    def _compute_framing_differences(self, group: pd.DataFrame) -> dict:
        """Top distinctive keywords for each bias group vs. the other two combined."""
        left_titles: list[str] = []
        center_titles: list[str] = []
        right_titles: list[str] = []

        for _, row in group.iterrows():
            b = str(row.get("political_bias", "")).lower()
            title = str(row.get("title", ""))
            if "left" in b:
                left_titles.append(title)
            elif "right" in b:
                right_titles.append(title)
            else:
                center_titles.append(title)

        def _get_unique_keywords(
            target_corpus: list[str], reference_corpus: list[str]
        ) -> list[str]:
            try:
                from sklearn.feature_extraction.text import CountVectorizer

                vec = CountVectorizer(
                    stop_words="english", ngram_range=(1, 1), max_features=20
                )
                counts = vec.fit_transform(target_corpus).toarray().sum(axis=0)
                feature_names = vec.get_feature_names_out()
                freq_a = dict(zip(feature_names, counts))
                other_text = " ".join(reference_corpus).lower()
                distinctive = []
                for word, count in sorted(
                    freq_a.items(), key=lambda x: x[1], reverse=True
                ):
                    if word not in other_text or other_text.count(word) < count * 0.2:
                        distinctive.append(word)
                    if len(distinctive) >= 3:
                        break
                return distinctive
            except ValueError:
                return []

        def safe_keywords(target: list[str], others: list[list[str]]) -> list[str]:
            if not target:
                return []
            reference = [t for group_list in others for t in group_list]
            return (
                _get_unique_keywords(target, reference)
                if reference
                else _get_unique_keywords(target, ["placeholder"])
            )

        return {
            "left": safe_keywords(left_titles, [center_titles, right_titles]),
            "center": safe_keywords(center_titles, [left_titles, right_titles]),
            "right": safe_keywords(right_titles, [left_titles, center_titles]),
        }

    def _analyze_linguistic_framing(self, group: pd.DataFrame) -> dict:
        """
        Detects passive vs active voice in headlines per bias group.
        Uses regex — no spaCy required.
        Returns: { "left": {passive_pct, active_pct, top_agents}, ... }
        """
        import re

        # Auxiliary verbs for passive construction
        AUX = r"(?:am|is|are|was|were|be|been|being)"
        # Common past-participle endings
        PP_SUFFIX = r"\b\w+(?:ed|en|wn|ld|nt|ught|ought)\b"
        PASSIVE_RE = re.compile(rf"\b{AUX}\b\s+(?:\w+\s+){{0,2}}{PP_SUFFIX}", re.I)

        def _analyze_titles(titles: list[str]) -> dict:
            if not titles:
                return {"passive_pct": 0.0, "active_pct": 0.0, "top_agents": []}

            passive_count = 0
            agents: list[str] = []

            for title in titles:
                if PASSIVE_RE.search(title):
                    passive_count += 1
                else:
                    # Extract first noun phrase (capitalised word after the start)
                    # as a heuristic for the grammatical subject / agent
                    match = re.match(
                        r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", title.strip()
                    )
                    if match:
                        agents.append(match.group(1))

            n = len(titles)
            passive_pct = round(passive_count / n * 100, 1)
            active_pct = round(100.0 - passive_pct, 1)

            # Top-2 agents by frequency
            from collections import Counter

            top_agents = [w for w, _ in Counter(agents).most_common(2)]

            return {
                "passive_pct": passive_pct,
                "active_pct": active_pct,
                "top_agents": top_agents,
            }

        left_titles: list[str] = []
        center_titles: list[str] = []
        right_titles: list[str] = []

        for _, row in group.iterrows():
            b = str(row.get("political_bias", "")).lower()
            title = str(row.get("title", ""))
            if "left" in b:
                left_titles.append(title)
            elif "right" in b:
                right_titles.append(title)
            else:
                center_titles.append(title)

        return {
            "left": _analyze_titles(left_titles),
            "center": _analyze_titles(center_titles),
            "right": _analyze_titles(right_titles),
        }

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
