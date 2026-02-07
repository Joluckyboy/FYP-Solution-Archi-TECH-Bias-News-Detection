from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent

def _datasets_dir() -> Path:
    return _repo_root() / "datasets"

# Bias bucket mapping
BIAS_BUCKET_MAP = {
    "left": "left",
    "leaning-left": "leaning-left", 
    "center": "center",
    "leaning-right": "leaning-right",
    "right": "right"
}

DEFAULT_BIAS_BUCKETS = ["left", "leaning-left", "center", "leaning-right", "right"]

def load_visualisations_data() -> Dict[str, Any]:
    
    # 1. OUTLET BIAS CHART DATA
    outlet_bias_data = _get_outlet_bias_groups()
    
    # 2. TRENDING KEYWORDS (TF-IDF on all headlines)
    trending_keywords = _get_trending_keywords(top_n=8)
    
    # 3. TOPIC-OUTLET COMPARISON (articles per outlet by topic)
    topic_outlet_data = _get_topic_outlet_distribution()
    
    return {
        "outletBiasGroups": outlet_bias_data,
        "trendingKeywords": trending_keywords,
        "topicOutletDistribution": topic_outlet_data,
        "source": {"type": "processed_csv", "timestamp": pd.Timestamp.now().isoformat()}
    }

def _get_outlet_bias_groups() -> Dict[str, List[str]]:
    """1. OutletBiasChart.jsx - bucket groups by bias"""
    # Load csv
    csv_path = _datasets_dir() / "Kaggle News Articles For Political Bias Classification.csv"
    if not csv_path.exists():
        return {b: [] for b in DEFAULT_BIAS_BUCKETS}
    
    df = pd.read_csv(csv_path)
    groups = {b: set() for b in DEFAULT_BIAS_BUCKETS}
    
    for _, row in df.iterrows():
        outlet = str(row.get('site', '')).strip()
        bias = str(row.get('bias', '')).strip().lower()
        
        bucket = BIAS_BUCKET_MAP.get(bias)
        if outlet and bucket:
            groups[bucket].add(outlet)
    
    # Convert sets to sorted lists
    return {k: sorted(v) for k, v in groups.items()}

def _get_trending_keywords(top_n: int = 8) -> List[Dict[str, Any]]:
    """2. TrendingKeywords.jsx - TF-IDF top 8 keywords/phrases"""
    csv_path = _datasets_dir() / "Kaggle News Articles For Political Bias Classification.csv"
    if not csv_path.exists():
        print(f"Warning: {csv_path} not found, returning empty keywords")
        return []
    
    try:
        df = pd.read_csv(csv_path)
        headlines = df['title'].dropna().astype(str).tolist()
    except:
        print("No headlines CSV found, skipping keywords")
        return []
    
    if len(headlines) < 2:  # Need multiple docs for TF-IDF
        return []
    
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        import numpy as np
        
        vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2),  # Just words + bigrams
            min_df=2
        )
        
        tfidf_matrix = vectorizer.fit_transform(headlines)
        feature_names = vectorizer.get_feature_names_out()
        
        tfidf_sums = np.array(tfidf_matrix.sum(axis=0)).flatten()
        
        # Get top keywords by raw TF-IDF sum 
        top_indices = np.argsort(tfidf_sums)[-top_n:][::-1]
        keywords = []
        
        for idx in top_indices:
            if tfidf_sums[idx] > 0:
                keywords.append({
                    "term": feature_names[idx],
                    "score": float(tfidf_sums[idx])
                })
        
        return keywords[:top_n]
        
    except Exception as e:
        print(f"TF-IDF failed: {e}, returning empty keywords")
        return []


def _get_topic_outlet_distribution() -> Dict[str, Dict[str, int]]:
    """3. TopicOutletComparison.jsx - articles per outlet by topic"""
    csv_path = _datasets_dir() / "Kaggle News Articles For Political Bias Classification.csv"
    if not csv_path.exists():
        return {}
    
    df = pd.read_csv(csv_path)
    topic_outlet_counts = {}
    
    for _, row in df.iterrows():
        outlet = str(row.get('site', '')).strip()
        topic = str(row.get('topic', '')).strip()  # adjust column name
        
        if outlet and topic:
            if topic not in topic_outlet_counts:
                topic_outlet_counts[topic] = {}
            topic_outlet_counts[topic][outlet] = topic_outlet_counts[topic].get(outlet, 0) + 1
    
    # Convert to sorted dicts by count
    for topic, outlets in topic_outlet_counts.items():
        sorted_outlets = dict(sorted(outlets.items(), key=lambda x: x[1], reverse=True))
        topic_outlet_counts[topic] = sorted_outlets
    
    return topic_outlet_counts
