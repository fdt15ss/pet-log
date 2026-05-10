from __future__ import annotations

import os


DEFAULT_LOCAL_GEMMA_MODEL = "google/gemma-3n-E4B-it"
DEFAULT_LOCAL_GEMMA_API_KEY = "local-gemma"


def local_gemma_model(default: str = DEFAULT_LOCAL_GEMMA_MODEL) -> str:
    return os.environ.get("GEMMA_MODEL", default)


def local_gemma_api_key() -> str:
    return os.environ.get("GEMMA_API_KEY", DEFAULT_LOCAL_GEMMA_API_KEY)
