"""
Political bias classification helper.
Uses the political_bias service and returns None when classification fails.

IMPORTANT: This module is OPTIONAL. If SKIP_BIAS_CLASSIFICATION=true,
the bias classification service is not required and articles will be
saved without bias labels.
"""
import json
import logging
import os
import time
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)

VALID_BIAS_LABELS = {
    "left",
    "leaning-left",
    "center",
    "leaning-right",
    "right",
}


def _normalize_label(value: Any) -> str | None:
    if value is None:
        return None

    label = str(value).strip().lower().replace("_", "-")
    label = label.replace(" ", "-")

    return label if label in VALID_BIAS_LABELS else None


def classify_political_bias(
    article: Dict[str, Any],
    base_url: str | None = None,
    timeout: tuple[float, float] = (2.0, 10.0),  # Reduced timeout
    max_retries: int = 1,  # Only 1 retry to avoid long waits
    retry_delay: float = 0.5,  # Shorter delay
) -> str | None:
    """
    Classify an article's political bias.
    Returns None on any failure or invalid label.
    
    IMPORTANT: If SKIP_BIAS_CLASSIFICATION=true, this function should
    not be called. The caller should check the environment variable first.
    """
    # Check if bias classification is disabled
    skip_bias = os.getenv('SKIP_BIAS_CLASSIFICATION', 'false').lower() == 'true'
    if skip_bias:
        logger.debug("Bias classification is disabled (SKIP_BIAS_CLASSIFICATION=true)")
        return None
    
    if not article:
        return None

    site = article.get("source") or article.get("site") or ""
    title = article.get("title") or ""
    page_text = (
        article.get("page_text")
        or article.get("summary")
        or article.get("body")
        or ""
    )

    if not (title or page_text):
        return None

    api_base = (base_url or os.getenv("BIAS_ENGINE_URL", "http://political_bias:9000")).rstrip("/")
    url = f"{api_base}/biasengine/rate_bias_no_perplexity"

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                url,
                params={"site": site, "title": title, "page_text": page_text},
                timeout=timeout,
            )
            if response.status_code == 200:
                try:
                    data = response.json()
                except ValueError:
                    data = json.loads(response.text or "{}")

                return _normalize_label(data.get("rating"))

            if response.status_code not in {429, 502, 503, 504}:
                logger.debug(f"Bias API returned {response.status_code}, skipping")
                return None

        except requests.exceptions.ConnectionError as exc:
            # Political bias service not available (expected when SKIP_BIAS_CLASSIFICATION=true)
            logger.debug(f"Political bias service not available: {exc}")
            return None
        except requests.exceptions.Timeout as exc:
            logger.debug(f"Bias classification timeout: {exc}")
            return None
        except Exception as exc:
            logger.debug(f"Bias classification error (attempt {attempt}/{max_retries}): {exc}")

        if attempt < max_retries:
            time.sleep(retry_delay)

    return None