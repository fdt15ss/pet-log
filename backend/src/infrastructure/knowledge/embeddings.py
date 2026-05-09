from __future__ import annotations

import os

from application.interfaces import EmbeddingProviderInterface


DEFAULT_CARE_KNOWLEDGE_EMBEDDING_MODEL = "text-embedding-3-small"


class OpenAIEmbeddingProvider(EmbeddingProviderInterface):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY", "")
        self._model = model or os.environ.get(
            "OPENAI_CARE_KNOWLEDGE_EMBEDDING_MODEL",
            DEFAULT_CARE_KNOWLEDGE_EMBEDDING_MODEL,
        )
        self._timeout = timeout

    def embed(self, text: str) -> tuple[float, ...]:
        raise NotImplementedError
