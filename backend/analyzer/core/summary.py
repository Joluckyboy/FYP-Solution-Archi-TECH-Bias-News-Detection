import requests
import time
import os
from typing import Any


import re


class SummaryService:
    def __init__(self):
        self.api_key = os.getenv("API_KEY")

    def _summarize_with_perplexity(self, article_urls):
        if not self.api_key:
            return None

        url = "https://api.perplexity.ai/chat/completions"

        # Format URLs for the user message
        urls_list = "\n".join([f"- {u}" for u in article_urls])

        payload = {
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a specialized news summarizer. Your task is to visit the provided news article URLs and summarize them into a concise list of 3-5 bullet points that reflect the consensus facts.\n\nCRITICAL STRICTNESS RULES:\n1. YOU MUST VISIT AND READ THE CONTENT OF THE PROVIDED URLS.\n2. USE ONLY THE CONTENT FOUND IN THESE SPECIFIC ARTICLES.\n3. DO NOT PERFORM ANY OTHER BROAD WEB SEARCHES OR USE EXTERNAL KNOWLEDGE UNRELATED TO THESE URLS.\n4. If the provided URLs are inaccessible or yield no content, state 'Insufficient information to generate summary'.\n5. Focus on the core facts reported in these specific articles.\n6. ABSOLUTELY NO CITATION MARKERS (e.g., [1], [2]) are allowed in the output. The output must be clean plain text.",
                },
                {
                    "role": "user",
                    "content": f"Here are the URLs of the articles to summarize:\n{urls_list}",
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
                    # Post-processing: Remove distinct citation markers like [1], [1, 2], [1][2] using regex
                    # This pattern matches brackets containing digits, commas, or spaces
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
                    # Don't retry for other client errors (4xx)
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

            article_urls = [art.get("url") for art in unique_arts if art.get("url")]

            if article_urls:
                print(
                    f"Generating On-Demand Summary for Topic {topic['id']} using {len(article_urls)} URLs..."
                )
                perplexity_summary = self._summarize_with_perplexity(article_urls)

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

            # Group URLs by bias (up to 3 each)
            groups: dict[str, list[str]] = {"left": [], "center": [], "right": []}
            for a in arts:
                b = str(a.get("political_bias", "")).lower()
                url = a.get("url", "")
                if not url:
                    continue
                if "left" in b and len(groups["left"]) < 3:
                    groups["left"].append(url)
                elif "right" in b and len(groups["right"]) < 3:
                    groups["right"].append(url)
                elif len(groups["center"]) < 3:
                    groups["center"].append(url)

            all_urls = groups["left"] + groups["center"] + groups["right"]
            if not all_urls:
                return topic

            def fmt(label, urls):
                if not urls:
                    return ""
                bullet = "\n".join(f"  - {u}" for u in urls)
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
                            "You are a media bias analyst. You will be given news article URLs "
                            "grouped by political leaning. Visit each URL and write a SHORT comparative "
                            "analysis in exactly this format:\n\n"
                            "LEFT: <one sentence on how left-leaning outlets frame this story>\n"
                            "CENTER: <one sentence on how center outlets frame this story>\n"
                            "RIGHT: <one sentence on how right-leaning outlets frame this story>\n\n"
                            "Focus on: language choice, who they blame or credit, what they emphasise or downplay. "
                            "Be concise and factual. No citations. No extra text outside the three lines."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Compare how these articles cover the same story:\n\n{url_block}",
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
                f"Generating Comparative Analysis for Topic {topic['id']} ({len(all_urls)} URLs)..."
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
