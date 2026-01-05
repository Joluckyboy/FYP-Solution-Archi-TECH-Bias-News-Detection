from dotenv import load_dotenv
import os

load_dotenv()

mongo_server = os.getenv("MONGO_SERVER") or "change as needed"
