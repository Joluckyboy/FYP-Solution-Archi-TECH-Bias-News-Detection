import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.functions.get_model import get_model
from app.blueprints.biasengine import biasengine  # APIRouter, was Flask Blueprint

load_dotenv()

# Shared model state — equivalent to app.device / app.model / app.tokenizer / app.pkey
model_state: dict = {}


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Replaces Flask create_app() model loading."""
    state = get_model()
    model_state["device"] = state["device"]
    model_state["model"] = state["model"]
    model_state["tokenizer"] = state["tokenizer"]
    model_state["pkey"] = os.environ.get("API_KEY") or os.environ.get("KEY")
    print(f"[startup] Model loaded on device: {state['device']}")
    yield


app = FastAPI(title="Political Bias API", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Replaces app.register_blueprint(biasengine)
app.include_router(biasengine)



@app.get("/")
def health_check():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "political_bias"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=False)