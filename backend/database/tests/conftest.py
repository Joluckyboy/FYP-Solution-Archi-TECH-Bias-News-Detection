import sys
from pathlib import Path
import os
from unittest.mock import MagicMock, patch

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up test environment variables before any imports
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

# Mock the Supabase client to prevent actual initialization during tests
mock_supabase_client = MagicMock()
mock_supabase_module = MagicMock()
mock_supabase_module.get_supabase_client = MagicMock(return_value=mock_supabase_client)
mock_supabase_module.supabase = mock_supabase_client
sys.modules['supabase_client'] = mock_supabase_module
