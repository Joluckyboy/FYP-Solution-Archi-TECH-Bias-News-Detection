import os

# get the urls from the environment variable or use the default value
sentiment_url = os.getenv("SENTIMENT_URL") or "http://localhost:8000"
emotion_url = os.getenv("EMOTION_URL") or "http://localhost:8000"
propaganda_url = os.getenv("PROPAGANDA_URL") or "http://localhost:8000"
factcheck_url = os.getenv("FACTCHECK_URL") or "http://localhost:8000"

scraper_url = os.getenv("SCRAPER_URL") or "http://localhost:8000"
database_url = os.getenv("DATABASE_URL") or "http://localhost:8000"

prescrape_num = os.getenv("SCRAPE_NUM") or 10
prescrape_feature_toggle = os.getenv("PRESCRAPE") == "1"
prescrape_interval = 30 # in minutes