from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List
import ast
import pandas as pd


# -----------------------------
# Helpers
# -----------------------------
BIAS_NORMALIZATION_MAP = {
    # Left-ish
    "left": "Left",
    "leaning-left": "Left",
    "leans-left": "Left",
    "far-left": "Left",
    "extreme-left": "Left",
    # Center-ish
    "center": "Center",
    "centre": "Center",
    "leaning-center": "Center",
    "leaning-centre": "Center",
    "mixed": "Center",
    "neutral": "Center",
    # Right-ish
    "right": "Right",
    "leaning-right": "Right",
    "leans-right": "Right",
    "far-right": "Right",
    "extreme-right": "Right",
}

DEFAULT_BIAS_LABELS = ["Left", "Center", "Right"]


def _repo_root() -> Path:
    # application/ is one level under repo root
    return Path(__file__).resolve().parent.parent


def _datasets_dir() -> Path:
    return _repo_root() / "datasets"


def _parse_bias_distribution(value: Any) -> Dict[str, int]:
    """
    Parses 'Bias Distribution' stored as a stringified dict
    e.g. "{'right': 1707}"
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return {}
    if isinstance(value, dict):
        return {str(k): int(v) for k, v in value.items()}
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return {}
        try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, dict):
                out = {}
                for k, v in parsed.items():
                    try:
                        out[str(k)] = int(v)
                    except Exception:
                        continue
                return out
        except Exception:
            return {}
    return {}


def _normalize_bias_counts(raw_counts: Dict[str, int]) -> Dict[str, int]:
    normalized = {label: 0 for label in DEFAULT_BIAS_LABELS}
    for raw_label, count in raw_counts.items():
        key = str(raw_label).strip().lower()
        mapped = BIAS_NORMALIZATION_MAP.get(key)
        if mapped is None:
            # unknown label -> ignore for MVP
            continue
        normalized[mapped] += int(count)
    return normalized


def load_dashboard_data() -> Dict[str, Any]:
    """
    Sprint 1 MVP: loads aggregated dashboard data from
    datasets/news_outlets_summary.csv
    """
    summary_path = _datasets_dir() / "news_outlets_summary.csv"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing required file: {summary_path}")

    df = pd.read_csv(summary_path)

    df["Country"] = df["Country"].fillna("Unknown").astype(str)
    df["Outlet"] = df["Outlet"].fillna("Unknown").astype(str)
    df["Total Articles"] = pd.to_numeric(df.get("Total Articles", 0), errors="coerce").fillna(0).astype(int)

    outlets: List[Dict[str, Any]] = []
    bias_totals = {label: 0 for label in DEFAULT_BIAS_LABELS}

    for _, row in df.iterrows():
        raw_dist = _parse_bias_distribution(row.get("Bias Distribution"))
        norm_counts = _normalize_bias_counts(raw_dist)

        for label in DEFAULT_BIAS_LABELS:
            bias_totals[label] += int(norm_counts.get(label, 0))

        outlets.append(
            {
                "outlet": row["Outlet"],
                "country": row["Country"],
                "totalArticles": int(row["Total Articles"]),
                "biasCounts": norm_counts,
                "firstArticle": str(row.get("First Article", "")) if not pd.isna(row.get("First Article", "")) else "",
                "lastArticle": str(row.get("Last Article", "")) if not pd.isna(row.get("Last Article", "")) else "",
                "uniqueTopics": int(row.get("Unique Topics", 0)) if not pd.isna(row.get("Unique Topics", 0)) else 0,
            }
        )

    total_articles = int(df["Total Articles"].sum())
    total_outlets = int(df["Outlet"].nunique())
    total_countries = int(df["Country"].nunique())

    # Country aggregates (useful later)
    country_bias: Dict[str, Dict[str, int]] = {}
    for o in outlets:
        c = o["country"]
        if c not in country_bias:
            country_bias[c] = {label: 0 for label in DEFAULT_BIAS_LABELS}
        for label in DEFAULT_BIAS_LABELS:
            country_bias[c][label] += int(o["biasCounts"].get(label, 0))

    return {
        "biasLabels": DEFAULT_BIAS_LABELS,
        "kpis": {
            "totalArticles": total_articles,
            "totalOutlets": total_outlets,
            "countriesCovered": total_countries,
            "biasTotals": bias_totals,
        },
        "outlets": outlets,
        "countryBias": country_bias,
        "source": {
            "type": "pre_aggregated_csv",
            "path": str(summary_path),
        },
    }
