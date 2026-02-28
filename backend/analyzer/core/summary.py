import requests
import time
import os
from typing import Any


import re


class SummaryService:
    def __init__(self):
        self.api_key = os.getenv("API_KEY")

    def _summarize_with_perplexity(self, articles: list[dict]) -> str | None:
        """Summarize a news story using article headlines as search context.

        Passes structured headline + source pairs so Perplexity can search
        the web for the story without needing direct URL access.
        """
        if not self.api_key:
            return None

        url = "https://api.perplexity.ai/chat/completions"

        # Build a readable article list using titles and sources
        article_lines = []
        for i, a in enumerate(articles, 1):
            title = a.get("title", "").strip()
            source = a.get("source", "").strip()
            excerpt = a.get("summary", "").strip()
            line = f"{i}. [{source}] {title}"
            if excerpt:
                line += f"\n   Excerpt: {excerpt[:200]}"
            article_lines.append(line)

        articles_text = "\n".join(article_lines)

        payload = {
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a news summarizer. You will be given a list of news article headlines "
                        "with their sources. Use these headlines as search queries to find and summarize "
                        "the news story they cover.\n\n"
                        "Write a concise summary of 3-5 bullet points covering the key facts of this story. "
                        "Focus on what happened, who is involved, and why it matters. "
                        "ABSOLUTELY NO citation markers (e.g. [1], [2]) in the output. Clean plain text only."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Summarize the news story covered by these articles:\n\n{articles_text}",
                },
            ],
            "max_tokens": 300,
            "temperature": 0.2,
            "return_citations": False,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(3):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                if response.status_code == 200:
                    content = response.json()["choices"][0]["message"]["content"]
                    cleaned_content = re.sub(r"\[[\d,\s]+\]", "", content)
                    return cleaned_content.strip()
                elif response.status_code == 429:
                    wait_time = 2 ** (attempt + 1)
                    print(f"Perplexity Rate Limit (429). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(
                        f"Perplexity API Error: {response.status_code} - {response.text}"
                    )
                    if 400 <= response.status_code < 500:
                        return None
            except Exception as e:
                print(f"Perplexity API Request Failed: {e}")
                time.sleep(1)

        return None

    def enrich_topic_with_deep_summary(self, topic: dict[str, Any]) -> dict[str, Any]:
        """
        Generates a deep summary for a single topic using Perplexity API.
        Modifies the topic dictionary in-place.
        """
        if not self.api_key:
            return topic

        try:
            # Reconstruct context from articles dict
            arts = topic.get("articles", [])

            # Select unique articles (up to 5) for headline context
            seen_titles = set()
            unique_arts = []
            for a in arts:
                title = a.get("title", "")
                if title not in seen_titles:
                    unique_arts.append(a)
                    seen_titles.add(title)
                if len(unique_arts) >= 5:
                    break

            if unique_arts:
                print(
                    f"Generating On-Demand Summary for Topic {topic['id']} using {len(unique_arts)} articles..."
                )
                perplexity_summary = self._summarize_with_perplexity(unique_arts)

                if perplexity_summary:
                    deep_summary_text = f"{perplexity_summary}"
                    # Update the insight
                    base_insight = topic.get("base_insight", "")
                    topic["contextual_insight"] = (
                        f"{deep_summary_text}\n\nCoverage Analysis: {base_insight}"
                    )
                    topic["has_deep_summary"] = True
        except Exception as e:
            print(f"Deep summarization failed for topic {topic['id']}: {e}")

        return topic

    def generate_comparative_analysis(self, topic: dict[str, Any]) -> dict[str, Any]:
        """
        Calls Perplexity with up to 3 article URLs per bias group (9 total).
        Asks the model to compare how Left / Center / Right framing differs.
        Stores the result in topic['comparative_analysis'].
        """
        if not self.api_key:
            return topic

        try:
            arts = topic.get("articles", [])

            # Group article headlines by bias (up to 3 each)
            groups: dict[str, list[str]] = {"left": [], "center": [], "right": []}
            for a in arts:
                b = str(a.get("political_bias", "")).lower()
                title = a.get("title", "").strip()
                source = a.get("source", "").strip()
                if not title:
                    continue
                entry = f"[{source}] {title}" if source else title
                if "left" in b and len(groups["left"]) < 3:
                    groups["left"].append(entry)
                elif "right" in b and len(groups["right"]) < 3:
                    groups["right"].append(entry)
                elif len(groups["center"]) < 3:
                    groups["center"].append(entry)

            all_entries = groups["left"] + groups["center"] + groups["right"]
            if not all_entries:
                return topic

            def fmt(label, entries):
                if not entries:
                    return ""
                bullet = "\n".join(f"  - {e}" for e in entries)
                return f"{label}:\n{bullet}"

            url_block = "\n\n".join(
                filter(
                    None,
                    [
                        fmt("Left-leaning sources", groups["left"]),
                        fmt("Center sources", groups["center"]),
                        fmt("Right-leaning sources", groups["right"]),
                    ],
                )
            )

            payload = {
                "model": "sonar",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a media bias analyst. You will be given news article headlines "
                            "grouped by political leaning. Use these headlines to search for the story "
                            "and write a SHORT comparative analysis in exactly this format:\n\n"
                            "LEFT: <one sentence on how left-leaning outlets frame this story>\n"
                            "CENTER: <one sentence on how center outlets frame this story>\n"
                            "RIGHT: <one sentence on how right-leaning outlets frame this story>\n\n"
                            "Focus on: language choice, who they blame or credit, what they emphasise or downplay. "
                            "Be concise and factual. No citations. No extra text outside the three lines."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Compare how these outlets cover the same story:\n\n{url_block}",
                    },
                ],
                "max_tokens": 250,
                "temperature": 0.3,
                "return_citations": False,
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            print(
                f"Generating Comparative Analysis for Topic {topic['id']} ({len(all_entries)} headlines)..."
            )
            import time as _time

            for attempt in range(3):
                try:
                    resp = requests.post(
                        "https://api.perplexity.ai/chat/completions",
                        json=payload,
                        headers=headers,
                        timeout=40,
                    )
                    if resp.status_code == 200:
                        raw = resp.json()["choices"][0]["message"]["content"].strip()
                        # Strip citation markers
                        import re

                        raw = re.sub(r"\[[\d,\s]+\]", "", raw).strip()
                        topic["comparative_analysis"] = raw
                        break
                    elif resp.status_code == 429:
                        _time.sleep(2 ** (attempt + 1))
                    else:
                        print(f"Comparative analysis API error: {resp.status_code}")
                        break
                except Exception as exc:
                    print(f"Comparative analysis request failed: {exc}")
                    _time.sleep(1)

        except Exception as e:
            print(f"Comparative analysis failed for topic {topic.get('id')}: {e}")

        return topic
