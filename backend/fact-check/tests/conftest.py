import sys
from pathlib import Path
import os

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables
os.environ.setdefault("MODEL", "deepseek")
os.environ.setdefault("API_KEY", "test-api-key")
os.environ.setdefault("API_KEYDS", "test-api-keyds")
