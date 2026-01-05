import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Feature toggle for model selection
    # Set MODEL to "deepseek" for alternative model
    MODEL = os.getenv("MODEL", "sonar")
    
    # URLs for different models
    PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"
    DEEPSEEK_URL = "https://api.groq.com/openai/v1/chat/completions"
    
    API_KEY = os.getenv("API_KEY")
    # print(API_KEY)
    if not API_KEY:
        raise EnvironmentError("API_KEY environment variable not set")
    HEADERS = {"Authorization": f"Bearer {API_KEY}"}
    
    API_KEYDS = os.getenv("API_KEYDS")
    if not API_KEYDS:
        raise EnvironmentError("API_KEYDS environment variable not set")
    HEADERS_DS = {"Authorization": f"Bearer {API_KEYDS}"}