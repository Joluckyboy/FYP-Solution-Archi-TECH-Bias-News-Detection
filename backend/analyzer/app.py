import os
import tempfile
import time as _time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core import s3_sync, get_summary_service
from .helpers import (
    DEFAULT_BIAS_DISTRIBUTION,
    SCRAPED_DATA_PATH,
    extract_keywords,
    fetch_topics_data,
    bust_topics_cache,
    _safe_read_csv,
    find_cluster_id_by_title,
    filter_related,
    related_articles_sbert,
)
from .core.services import get_topic_service

# ---------------------------------------------------------------------------
# In-memory enrichment cache
# Stores Perplexity results so each topic is only enriched once per TTL window.
# Structure: { topic_id: {"data": {...}, "ts": float} }
# ---------------------------------------------------------------------------
_ENRICHMENT_CACHE: dict = {}
_ENRICHMENT_TTL: int = 3600  # 1 hour in seconds


def _resolve_writable_scraped_data_path() -> str:
    default_path = SCRAPED_DATA_PATH
    target_dir = os.path.dirname(default_path) or "."

    try:
        os.makedirs(target_dir, exist_ok=True)
        return default_path
    except PermissionError:
        fallback_dir = os.path.join(tempfile.gettempdir(), "analyzer-data")
        os.makedirs(fallback_dir, exist_ok=True)
        fallback_path = os.path.join(fallback_dir, os.path.basename(default_path) or "scraped_articles.csv")
        print(f"[cluster] Falling back to writable path: {fallback_path}")
        return fallback_path


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Analyzer starting (lazy model loading).")
    s3_sync.ensure_scraped_csv()

    # Pre-warm topics cache on startup so the first request is instant
    print("Pre-warming topics cache...")
    topics, err = fetch_topics_data()
    if err:
        print(f"Pre-warm failed: {err}")
    else:
        print(f"Pre-warm complete: {len(topics)} topics cached.")

    yield


app = FastAPI(title="Analyzer API", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "service": "analyzer"}


@app.get("/")
def health_check():
    return {"status": "ok"}

@app.get("/dashboard/topics")
def dashboard_topics():
    topics_data, error = fetch_topics_data()
    if error:
        return JSONResponse({"error": error}, status_code=404)
    try:
        formatted_topics = [
            {
                "id": t["id"],
                "title": t["title"],
                "topicName": t.get("topic_name", ""),
                "image": t.get("image") or "https://placehold.co/600x400?text=No+Image",
                "allImages": t.get("all_images", []),
                "sourceCount": t.get("source_count", 0),
                "biasDistribution": t.get("bias_distribution", dict(DEFAULT_BIAS_DISTRIBUTION)),
                "date": t.get("latest_date", ""),
                "frontUrl": t["articles"][0]["url"] if t.get("articles") else None,
            }
            for t in topics_data
        ]
        return {"topics": formatted_topics[:50]}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/dashboard/topic_details/{topic_id}")
def get_topic_details(topic_id: int):
    topics_data, error = fetch_topics_data()
    if error:
        return JSONResponse({"error": error}, status_code=404)
    topic = next((t for t in topics_data if t["id"] == topic_id), None)
    if not topic:
        return JSONResponse({"error": "Topic not found"}, status_code=404)
    return {
        "id": topic["id"],
        "title": topic["title"],
        "image": topic.get("image"),
        "bias_distribution": topic.get("bias_distribution", dict(DEFAULT_BIAS_DISTRIBUTION)),
        "source_count": topic.get("source_count", 0),
        "latest_date": topic.get("latest_date", ""),
        "contextual_insight": topic.get("contextual_insight", ""),
        "articles": topic.get("articles", []),
        "silent_outlets": topic.get("silent_outlets", {}),
        "framing_differences": topic.get("framing_differences", {}),
        "lead_articles": topic.get("lead_articles", {}),
        "linguistic_framing": topic.get("linguistic_framing", {}),
    }


    # ── Check cache first ────────────────────────────────────────────────────
@app.get("/dashboard/topic_enrichment/{topic_id}")
def get_topic_enrichment(topic_id: int):
    now = _time.time()
    cached = _ENRICHMENT_CACHE.get(topic_id)
    if cached and (now - cached["ts"]) < _ENRICHMENT_TTL:
        print(f"[enrichment cache] HIT for topic {topic_id}")
        return cached["data"]

    # ── Cache miss — fetch base topic data ───────────────────────────────────
    topics_data, error = fetch_topics_data()
    if error:
        return JSONResponse({"error": error}, status_code=404)
    topic = next((t for t in topics_data if t["id"] == topic_id), None)
    if not topic:
        return JSONResponse({"error": "Topic not found"}, status_code=404)

    # ── Perform LLM enrichment ───────────────────────────────────────────────
    svc = get_summary_service()
    if svc:
        topic = svc.enrich_topic_with_deep_summary(topic)
        topic = svc.generate_comparative_analysis(topic)

    result = {
        "contextual_insight": topic.get("contextual_insight", ""),
        "comparative_analysis": topic.get("comparative_analysis", ""),
        "has_deep_summary": topic.get("has_deep_summary", False),
    }

    # ── Store in cache ───────────────────────────────────────────────────────
    _ENRICHMENT_CACHE[topic_id] = {"data": result, "ts": now}
    print(f"[enrichment cache] STORED for topic {topic_id}")
    return result


@app.get("/dashboard/trending_keywords")
def trending_keywords():
    df = _safe_read_csv(SCRAPED_DATA_PATH)
    if df is None or len(df) == 0:
        return {"keywords": []}
    df = df.fillna("")
    return {"keywords": extract_keywords(df, top_k=10)}


@app.get("/dashboard/topic_coverage")
def topic_coverage(topic: str = ""):
    df = _safe_read_csv(SCRAPED_DATA_PATH)
    if df is None or len(df) == 0:
        return {"topics": [], "coverage": []}
    df = df.fillna("")
    if "topic" not in df.columns or "source" not in df.columns:
        return {"topics": [], "coverage": []}
    df["topic"] = df["topic"].astype(str).str.strip()
    df.loc[df["topic"] == "", "topic"] = "General"
    if topic:
        df = df[df["topic"] == topic]
    counts = df.groupby("source").size().sort_values(ascending=False).head(50)
    coverage = [{"source": str(src), "count": int(cnt)} for src, cnt in counts.items()]
    topics = sorted(df["topic"].unique().tolist())
    return {"topics": topics, "coverage": coverage}


@app.post("/dashboard/cluster")
def cluster_and_save():
    """
    Called once per day by the ECS bias-classifier container after it finishes
    uploading the cleaned CSV to S3.

    Steps:
      1. Force re-download fresh CSV from S3 (bypass local 12h cache)
      2. Run TopicClusteredService → assign cluster_id to every article
      3. Write cluster_id back into the local CSV file
      4. Upload enriched CSV to S3 (overwrites cleaned CSV)
      5. Bust in-memory topics cache so next /dashboard/topics
         request reads the new cluster_ids immediately

    Returns JSON: { "status": "ok", "articles": N, "clusters": N }
    """
    import boto3
    import analyzer.helpers.data_helpers as _dh
    from .core.services import get_topic_service

    S3_BUCKET = os.environ.get("S3_BUCKET")
    S3_KEY = os.environ.get("SCRAPER_S3_KEY", "scraped_articles/scraped_articles.csv")
    AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-1")

    if not S3_BUCKET:
        return JSONResponse({"error": "S3_BUCKET env var not set"}, status_code=500)

    scraped_data_path = _resolve_writable_scraped_data_path()

    # ── 1. Force download fresh CSV from S3 ───────────────────────────────────
    # Bypass the 12h TTL — we know S3 just got a new file from bias-classifier.
    try:
        s3 = boto3.client("s3", region_name=AWS_REGION)
        s3.download_file(S3_BUCKET, S3_KEY, scraped_data_path)
        print(f"[cluster] Downloaded fresh CSV from s3://{S3_BUCKET}/{S3_KEY}")
    except Exception as e:
        return JSONResponse({"error": f"S3 download failed: {e}"}, status_code=500)

    # ── 2. Read CSV ───────────────────────────────────────────────────────────
    df = _safe_read_csv(scraped_data_path)
    if df is None or df.empty:
        return JSONResponse({"error": "CSV is empty after download"}, status_code=500)

    # ── 3. Cluster ────────────────────────────────────────────────────────────
    try:
        svc = get_topic_service()
        topics = svc.cluster_articles(df)
    except Exception as e:
        return JSONResponse({"error": f"Clustering failed: {e}"}, status_code=500)

    # Build title → cluster_id lookup
    cluster_map: dict[str, str] = {}
    for topic in topics:
        cid = str(topic["id"])
        for article in topic.get("articles", []):
            title = article.get("title", "")
            if title:
                cluster_map[title] = cid

    df["cluster_id"] = df["title"].map(cluster_map).fillna("unclustered")

    # ── 4. Save locally + upload enriched CSV to S3 ───────────────────────────
    df.to_csv(scraped_data_path, index=False)

    try:
        s3.upload_file(scraped_data_path, S3_BUCKET, S3_KEY)
        print(f"[cluster] Uploaded enriched CSV → s3://{S3_BUCKET}/{S3_KEY}")
    except Exception as e:
        return JSONResponse({"error": f"S3 upload failed: {e}"}, status_code=500)

    # ── 5. Bust topics cache (memory + Redis) ──────────────────────────────────
    bust_topics_cache()

    print(f"[cluster] Done. {len(topics)} clusters from {len(df)} articles.")
    return {"status": "ok", "articles": len(df), "clusters": len(topics)}


@app.post("/dashboard/related_articles")
async def related_articles(request: Request):
    import pandas as pd

    body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    query_title = (body.get("title") or "").strip()
    source_domain = (body.get("source_domain") or "").strip().lower()

    if not query_title:
        return JSONResponse(
            {"matched": False, "articles": [], "reason": "title required"},
            status_code=400,
        )

    # ── Load CSV ──────────────────────────────────────────────────────────────
    csv_path = os.getenv("SCRAPER_DATA_DIR", "/app/data") + "/scraped_articles.csv"
    if not os.path.exists(csv_path):
        return {"matched": False, "articles": [], "reason": "CSV not found"}

    try:
        df = pd.read_csv(csv_path).fillna("")
    except Exception as e:
        return {"matched": False, "articles": [], "reason": f"CSV read error: {e}"}

    # ── Fast path: use precomputed cluster_id ─────────────────────────────────
    if "cluster_id" in df.columns and df["cluster_id"].notna().any():
        cluster_id = find_cluster_id_by_title(df, query_title)
        if cluster_id is None:
            return {
                "matched": False,
                "articles": [],
                "reason": "Article title not found in cluster database",
            }

        cluster_articles = df[df["cluster_id"].astype(str) == str(cluster_id)]

        # Representative cluster title = most recent article title
        cluster_title = query_title
        if "published_at" in cluster_articles.columns:
            sorted_cluster = cluster_articles.sort_values("published_at", ascending=False)
            cluster_title = str(sorted_cluster.iloc[0].get("title", query_title))

        related = filter_related(cluster_articles, source_domain, query_title)
        return {
            "matched": True,
            "cluster_title": cluster_title,
            "cluster_id": str(cluster_id),
            "articles": related,
        }

    # Slow fallback: S-BERT
    print(f"[related_articles] No cluster_id — falling back to S-BERT for: {query_title[:60]}")
    # related_articles_sbert returns (JSONResponse, status_code) tuple from Flask;
    # unwrap it for FastAPI
    result, status_code = related_articles_sbert(df, query_title, source_domain)
    return JSONResponse(result.get_json(), status_code=status_code)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("analyzer.app:app", host="0.0.0.0", port=8017, reload=False)