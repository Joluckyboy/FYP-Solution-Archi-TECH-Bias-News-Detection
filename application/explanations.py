from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
from datetime import date, timedelta

def _repo_root() -> Path:
    return Path("/application")

def _datasets_dir() -> Path:
    return Path("/backend/scraper/data") 

def load_scraper_stats() -> Dict[str, Any]:
    
    csv_path = _datasets_dir() / "scraped_articles.csv"
    
    if not csv_path.exists():
        return {"error": f"CSV not found: {csv_path}", "coreStats": {"todayArticles": 0, "cumulativeTotal": 0}}
    
    df = pd.read_csv(csv_path)
    
    if len(df) == 0:
        return {"error": "Empty CSV", "coreStats": {"todayArticles": 0, "cumulativeTotal": 0}}
    
    df['published_at'] = pd.to_datetime(df['published_at'], format='%Y-%m-%d')
    
    today_str = date.today().isoformat()
    today_articles = len(df[df['published_at'].dt.date == pd.to_datetime(today_str).date()])
    cumulative = len(df)
    
    cutoff = pd.to_datetime(today_str) - timedelta(days=14)
    trend = (df[df['published_at'] >= cutoff]
            .groupby(df['published_at'].dt.date)
            .size()
            .reset_index(name='count')
            .rename(columns={'published_at': 'date'})
            .to_dict('records'))
    
    return {
        "coreStats": {
            "todayArticles": today_articles,
            "cumulativeTotal": cumulative,
            "avgDaily": round(cumulative / df['published_at'].dt.date.nunique()),
            "countries": df['country'].unique().tolist()
        },
        "sourceBreakdown": df['source'].value_counts().head(5).to_dict(),
        "countriesDistribution": df['country'].value_counts().head(8).to_dict(),
        "dailyTrend": trend,
        "debug": {"rows": len(df), "path": str(csv_path)}
    }
