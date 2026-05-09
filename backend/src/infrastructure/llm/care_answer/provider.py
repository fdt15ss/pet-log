from __future__ import annotations

import os

from domain.models import CareContext
from infrastructure.knowledge import CareKnowledgeRetriever
from infrastructure.llm.care_answer.mapper import message_content_to_text
from infrastructure.llm.care_answer.model import (
    DEFAULT_CARE_ANSWER_MODEL,
    CareAnswerModel,
    CareAnswerModelFactory,
    build_care_answer_model,
)
from infrastructure.llm.care_answer.prompt import build_care_answer_messages


class CareAnswerProvider:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
        model_factory: CareAnswerModelFactory = build_care_answer_model,
        chat_model: CareAnswerModel | None = None,
        knowledge_retriever: CareKnowledgeRetriever | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY", "")
        self._model = model or os.environ.get("OPENAI_CARE_ANSWER_MODEL", DEFAULT_CARE_ANSWER_MODEL)
        self._timeout = timeout
        self._model_factory = model_factory
        self._chat_model = chat_model
        self._knowledge_retriever = knowledge_retriever

    def answer(self, context: CareContext, question: str) -> str:
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY is required to use CareAnswerProvider.")

        result = self._chat_llm().invoke(build_care_answer_messages(context, question))
        return message_content_to_text(result)

    def _chat_llm(self) -> CareAnswerModel:
        if self._chat_model is None:
            self._chat_model = self._model_factory(self._model, self._api_key, self._timeout)
        return self._chat_model
