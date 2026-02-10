# application/dashboard_methods.py

import os
import re
import pandas as pd

SCRAPER_DATA_DIR = os.getenv("SCRAPER_DATA_DIR", "/backend/scraper/data")
SCRAPED_DATA_PATH = os.path.join(SCRAPER_DATA_DIR, "scraped_articles.csv")

BIAS_LABELS = ["Left", "Center", "Right"]


def _detect_bias_column(df: pd.DataFrame) -> str | None:
    if df is None or df.empty:
        return None
    candidates = [
        "bias",
        "bias_type",
        "bias_label",
        "biasCategory",
        "bias_category",
        "political_bias",
    ]
    cols = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in cols:
            return cols[c.lower()]
    return None


def _normalize_bias_to_3(label: str) -> str | None:
    s = (label or "").strip().lower()
    if not s:
        return None
    s = s.replace("_", "-")
    s = re.sub(r"\s+", "-", s)

    if s in {"left", "liberal", "lean-left", "leaning-left", "center-left", "left-leaning"}:
        return "Left"
    if s in {"center", "centre", "neutral", "balanced"}:
        return "Center"
    if s in {"right", "conservative", "lean-right", "leaning-right", "center-right", "right-leaning"}:
        return "Right"
    return None


def load_dashboard_data(country: str | None = None, outlet: str | None = None):
    """
    Returns data for /application/bias_dashboard.
    Source of truth: scraped_articles.csv

    If a bias column exists (bias / bias_type / bias_label / ...), use it.
    Otherwise, bias counts default to Center.
    """
    if not os.path.exists(SCRAPED_DATA_PATH):
        raise FileNotFoundError(f"Missing required file: {SCRAPED_DATA_PATH}")

    df = pd.read_csv(SCRAPED_DATA_PATH).fillna("")

    required = {"source", "country"}
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"scraped_articles.csv missing columns: {missing}")

    bias_col = _detect_bias_column(df)

    if country:
        df = df[df["country"].astype(str).str.lower() == country.lower()]
    if outlet:
        df = df[df["source"].astype(str).str.lower() == outlet.lower()]

    grouped = df.groupby(["country", "source"], dropna=False)

    outlets: list[dict] = []
    for (cty, src), g in grouped:
        total = int(len(g))

        counts = {"Left": 0, "Center": 0, "Right": 0}
        if bias_col:
            for raw in g[bias_col].astype(str).tolist():
                b = _normalize_bias_to_3(raw)
                if b:
                    counts[b] += 1

        # if no bias labels yet → default to Center
        if sum(counts.values()) == 0:
            counts["Center"] = total

        outlets.append({
            "country": str(cty).strip() or "Unknown",
            "outlet": str(src).strip() or "Unknown",
            "totalArticles": total,
            "biasCounts": counts,
        })

    outlets.sort(key=lambda x: x["totalArticles"], reverse=True)

    # IMPORTANT: your frontend expects the array under key "outlets"
    return {
        "biasLabels": BIAS_LABELS,
        "outlets": outlets,
    }
