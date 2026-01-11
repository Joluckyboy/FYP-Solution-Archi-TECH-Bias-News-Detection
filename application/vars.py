import os

# get the urls from the environment variable or use the default value
# Fixed: Corrected fallback ports to match actual service ports in docker-compose
sentiment_url = os.getenv("SENTIMENT_URL") or "http://localhost:8012"
emotion_url = os.getenv("EMOTION_URL") or "http://localhost:8013"
propaganda_url = os.getenv("PROPAGANDA_URL") or "http://localhost:8014"
factcheck_url = os.getenv("FACTCHECK_URL") or "http://localhost:8016"

scraper_url = os.getenv("SCRAPER_URL") or "http://localhost:8015"
database_url = os.getenv("DATABASE_URL") or "http://localhost:8011"

prescrape_num = os.getenv("SCRAPE_NUM") or 10
prescrape_feature_toggle = os.getenv("PRESCRAPE") == "1"
prescrape_interval = 30 # in minutes