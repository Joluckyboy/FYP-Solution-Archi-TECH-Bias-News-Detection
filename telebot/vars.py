import os

from dotenv import load_dotenv

load_dotenv()

# get the urls from the environment variable or use the default value
# sentiment_url = os.getenv("SENTIMENT_URL") or "http://localhost:8000"
# emotion_url = os.getenv("EMOTION_URL") or "http://localhost:8000"
# propaganda_url = os.getenv("PROPAGANDA_URL") or "http://localhost:8000"
# factcheck_url = os.getenv("FACTCHECK_URL") or "http://localhost:8000"

# scraper_url = os.getenv("SCRAPER_URL") or "http://localhost:8000"
# database_url = os.getenv("DATABASE_URL") or "http://localhost:8000"

# prescrape_num = os.getenv("SCRAPE_NUM") or 10
# prescrape_feature_toggle = os.getenv("PRESCRAPE") == 1
# prescrape_interval = 30 # in minutes

application_url = os.getenv("APPLICATION_URL") or "http://localhost:8010"
# application_url = os.getenv("APPLICATION_URL") or "https://service.chfwhitehats2024.games"

web_url = os.getenv("WEB_APP_URL") or "http://localhost:5173"
# web_url = os.getenv("WEB_APP_URL") or "https://chfwhitehats2024.games"

telebot_token = os.getenv("TELEBOT_TOKEN") or "YOUR_TELEGRAM"