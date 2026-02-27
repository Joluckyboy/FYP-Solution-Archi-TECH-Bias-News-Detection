from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
from datetime import date, timedelta
from zoneinfo import ZoneInfo
import os

import s3_sync

def _repo_root() -> Path:
    return Path("/application")

def _datasets_dir() -> Path:
    return Path(os.getenv("SCRAPER_DATA_DIR", "/app/data"))

def load_scraper_stats() -> Dict[str, Any]:

    s3_sync.ensure_scraped_csv()
    
    csv_path = _datasets_dir() / "scraped_articles.csv"
    
    if not csv_path.exists():
        return {"error": f"CSV not found: {csv_path}", "coreStats": {"yesterdayArticles": 0, "todayArticles": 0, "cumulativeTotal": 0}}
    
    df = pd.read_csv(csv_path)
    
    if len(df) == 0:
        return {"error": "Empty CSV", "coreStats": {"yesterdayArticles": 0, "todayArticles": 0, "cumulativeTotal": 0}}
    
    # Parse dates - try multiple formats (DD/MM/YYYY, YYYY-MM-DD, etc)
    df['published_at'] = pd.to_datetime(df['published_at'], format='mixed', dayfirst=True, errors='coerce')
    
    yesterday_sgt = pd.Timestamp.now(ZoneInfo("Asia/Singapore")).normalize() - pd.Timedelta(days=1)
    
    yesterday_articles = len(df[
        df['published_at'].dt.tz_localize(None).dt.date == yesterday_sgt.date()
    ])
    
    today_articles = len(df[
        df['published_at'].dt.tz_localize(None).dt.date == pd.Timestamp.now().normalize().date()
    ])

    cumulative = len(df)
    
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=14)
    trend = (df[df['published_at'] >= cutoff]
            .groupby(df['published_at'].dt.date)
            .size()
            .reset_index(name='count')
            .rename(columns={'published_at': 'date'})
            .to_dict('records'))
    
    return {
        "coreStats": {
            "yesterdayArticles": yesterday_articles,  
            "todayArticles": today_articles,          
            "cumulativeTotal": cumulative,
            "avgDaily": round(cumulative / df['published_at'].dt.date.nunique() if df['published_at'].dt.date.nunique() > 0 else 1),
            "countries": df['country'].dropna().unique().tolist()
        },
        "sourceBreakdown": df['source'].value_counts().head(5).to_dict(),
        "countriesDistribution": df['country'].value_counts().head(8).to_dict(),
        "dailyTrend": trend,
        "debug": {
            "rows": len(df), 
            "path": str(csv_path),
            "yesterdayCount": yesterday_articles,
            "todayCount": today_articles
        }
    }
