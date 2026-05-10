from __future__ import annotations

from domain.models import CareContext
from infrastructure.knowledge import CareKnowledgeRetriever
from infrastructure.llm.base_provider import BaseLLMProvider
from infrastructure.llm.care_answer.mapper import message_content_to_text
from infrastructure.llm.care_answer.model import (
    DEFAULT_CARE_ANSWER_MODEL,
    CareAnswerModel,
    CareAnswerModelFactory,
    build_care_answer_model,
)
from infrastructure.llm.care_answer.prompt import build_care_answer_messages
from infrastructure.llm.provider_config import LLMProviderConfig


class CareAnswerProvider(BaseLLMProvider[CareAnswerModel]):
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
        super().__init__(
            config=LLMProviderConfig.from_env(
                provider_name="CareAnswerProvider",
                model_env="OPENAI_CARE_ANSWER_MODEL",
                default_model=DEFAULT_CARE_ANSWER_MODEL,
                fallback_model_env="OPENAI_CARE_ANSWER_FALLBACK_MODEL",
                api_key=api_key,
                model=model,
                timeout=timeout,
            ),
            model_factory=model_factory,
            model=chat_model,
        )
        self._knowledge_retriever = knowledge_retriever

    def answer(self, context: CareContext, question: str) -> str:
        knowledge_hits = ()
        if self._knowledge_retriever is not None:
            knowledge_hits = self._knowledge_retriever.search(question)

        result = self._invoke_llm(build_care_answer_messages(context, question, knowledge_hits))
        return message_content_to_text(result)
