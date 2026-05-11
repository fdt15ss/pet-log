from __future__ import annotations

import os


DEFAULT_LOCAL_GEMMA_MODEL = "gemma4:e4b"
DEFAULT_LOCAL_GEMMA_API_KEY = "local-gemma"

OLLAMA_GEMMA_MODEL_ALIASES = {
    "google/gemma-3n-E4B-it": "gemma3n:e4b",
    "google/gemma-4-E2B-it": "gemma4:e2b",
    "google/gemma-4-E4B-it": "gemma4:e4b",
    "google/gemma-4-26B-A4B-it": "gemma4:26b",
    "google/gemma-4-31B-it": "gemma4:31b",
}


def local_gemma_model(default: str = DEFAULT_LOCAL_GEMMA_MODEL) -> str:
    return normalize_local_gemma_model(os.environ.get("GEMMA_MODEL", default))


def normalize_local_gemma_model(model: str) -> str:
    return OLLAMA_GEMMA_MODEL_ALIASES.get(model, model)


def local_gemma_api_key() -> str:
    return os.environ.get("GEMMA_API_KEY", DEFAULT_LOCAL_GEMMA_API_KEY)
