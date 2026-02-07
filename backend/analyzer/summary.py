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
