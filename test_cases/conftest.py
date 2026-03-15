import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / 'application'
DB_DIR = ROOT / 'backend' / 'database'

for path in [str(ROOT), str(DB_DIR), str(APP_DIR)]:
    if path in sys.path:
        sys.path.remove(path)
for path in [str(ROOT), str(DB_DIR), str(APP_DIR)]:
    sys.path.insert(0, path)

# ---- Lightweight stubs for optional dependencies missing in local environments ----
if 'flask' not in sys.modules:
    flask_stub = types.ModuleType('flask')

    class _FlaskAbort(Exception):
        def __init__(self, code=None, description=None):
            super().__init__(description)
            self.code = code
            self.description = description

    def abort(code=None, description=None):
        raise _FlaskAbort(code=code, description=description)

    flask_stub.abort = abort
    flask_stub.FlaskAbort = _FlaskAbort
    sys.modules['flask'] = flask_stub

if 'redis' not in sys.modules:
    redis_stub = types.ModuleType('redis')

    class _DummyRedis:
        def ping(self):
            return True
        def get(self, *args, **kwargs):
            return None
        def set(self, *args, **kwargs):
            return True
        def delete(self, *args, **kwargs):
            return 1

    def from_url(*args, **kwargs):
        return _DummyRedis()

    redis_stub.from_url = from_url
    sys.modules['redis'] = redis_stub

if 'dotenv' not in sys.modules:
    dotenv_stub = types.ModuleType('dotenv')
    dotenv_stub.load_dotenv = lambda *args, **kwargs: None
    sys.modules['dotenv'] = dotenv_stub

if 'supabase_client' not in sys.modules:
    supabase_client_stub = types.ModuleType('supabase_client')

    class _Chain:
        def insert(self, *args, **kwargs):
            return self
        def select(self, *args, **kwargs):
            return self
        def update(self, *args, **kwargs):
            return self
        def delete(self, *args, **kwargs):
            return self
        def eq(self, *args, **kwargs):
            return self
        def execute(self):
            class _Result:
                data = []
            return _Result()

    class _DummySupabase:
        def table(self, *args, **kwargs):
            return _Chain()
        def channel(self, *args, **kwargs):
            return self
        def on_postgres_changes(self, *args, **kwargs):
            return self
        def subscribe(self):
            return self

    supabase_client_stub.get_supabase_client = lambda: _DummySupabase()
    sys.modules['supabase_client'] = supabase_client_stub

if 'openai' not in sys.modules:
    openai_stub = types.ModuleType('openai')
    class OpenAI:
        def __init__(self, *args, **kwargs):
            pass
    openai_stub.OpenAI = OpenAI
    sys.modules['openai'] = openai_stub

if 'fastapi' not in sys.modules:
    fastapi_stub = types.ModuleType('fastapi')
    middleware_mod = types.ModuleType('fastapi.middleware')
    cors_mod = types.ModuleType('fastapi.middleware.cors')
    responses_mod = types.ModuleType('fastapi.responses')

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail=None):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

    def Query(default=None, **kwargs):
        return default

    class FastAPI:
        def __init__(self, *args, **kwargs):
            self.routes = []
        def add_middleware(self, *args, **kwargs):
            return None
        def get(self, path, **kwargs):
            def decorator(fn):
                self.routes.append(('GET', path, fn))
                return fn
            return decorator
        def post(self, path, **kwargs):
            def decorator(fn):
                self.routes.append(('POST', path, fn))
                return fn
            return decorator
        def put(self, path, **kwargs):
            def decorator(fn):
                self.routes.append(('PUT', path, fn))
                return fn
            return decorator
        def delete(self, path, **kwargs):
            def decorator(fn):
                self.routes.append(('DELETE', path, fn))
                return fn
            return decorator

    class CORSMiddleware:
        pass

    class JSONResponse:
        def __init__(self, content=None, status_code=200, **kwargs):
            self.content = content
            self.status_code = status_code
            import json as _json
            self.body = _json.dumps(content).encode('utf-8')

    class StreamingResponse:
        def __init__(self, content=None, media_type=None, status_code=200, **kwargs):
            self.content = content
            self.media_type = media_type
            self.status_code = status_code

    fastapi_stub.FastAPI = FastAPI
    fastapi_stub.HTTPException = HTTPException
    fastapi_stub.Query = Query
    cors_mod.CORSMiddleware = CORSMiddleware
    responses_mod.JSONResponse = JSONResponse
    responses_mod.StreamingResponse = StreamingResponse

    sys.modules['fastapi'] = fastapi_stub
    sys.modules['fastapi.middleware'] = middleware_mod
    sys.modules['fastapi.middleware.cors'] = cors_mod
    sys.modules['fastapi.responses'] = responses_mod

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    passed = len(terminalreporter.stats.get("passed", []))
    failed = len(terminalreporter.stats.get("failed", []))
    skipped = len(terminalreporter.stats.get("skipped", []))
    errors = len(terminalreporter.stats.get("error", []))

    terminalreporter.write_sep(
        "=",
        f"TEST SUMMARY: {passed} passed, {failed} failed, {skipped} skipped, {errors} errors"
    )