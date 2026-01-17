import sys
from pathlib import Path
import os
import pytest

# Set test environment variables BEFORE any imports
os.environ.setdefault("MODEL", "deepseek")
os.environ.setdefault("API_KEY", "test-api-key")
os.environ.setdefault("API_KEYDS", "test-api-keyds")

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def pytest_configure(config):
    """Configure pytest with asyncio settings"""
    config.option.asyncio_default_fixture_loop_scope = "function"
