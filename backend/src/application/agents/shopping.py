from __future__ import annotations

import logging
import warnings
from collections.abc import Iterator
from dataclasses import replace
from typing import TypedDict

from domain.models import CareSuggestion, PetProfile, PetRecord, ShoppingCategoryRequest, ShoppingRecommendation
from langchain_core._api.deprecation import LangChainPendingDeprecationWarning

warnings.simplefilter("ignore", LangChainPendingDeprecationWarning)

from langgraph.graph import END, START, StateGraph  # noqa: E402


logger = logging.getLogger(__name__)


class ShoppingAgentState(TypedDict, total=False):
    pet: PetProfile
    text: str
    records: tuple[PetRecord, ...]
    suggestions: tuple[CareSuggestion, ...]
    category_requests: tuple[ShoppingCategoryRequest, ...]
    recommendations: tuple[ShoppingRecommendation, ...]
    selected_recommendations: tuple[ShoppingRecommendation, ...]
    result: tuple[ShoppingRecommendation, ...]


class ShoppingAgent:
    def __init__(self, recommendation_provider, recommendation_agent=None, reason_agent=None) -> None:
        self._recommendation_provider = recommendation_provider
        self._recommendation_agent = recommendation_agent or reason_agent
        self._graph = self._build_graph()

    def recommend(
        self,
        pet: PetProfile,
        text: str,
        records: tuple[PetRecord, ...],
        suggestions: tuple[CareSuggestion, ...] = (),
    ) -> tuple[ShoppingRecommendation, ...]:
        result = self._graph.invoke(
            {
                "pet": pet,
                "text": text,
                "records": records,
                "suggestions": suggestions,
            }
        )
        return result["result"]

    def stream_updates(
        self,
        pet: PetProfile,
        text: str,
        records: tuple[PetRecord, ...],
        suggestions: tuple[CareSuggestion, ...] = (),
    ) -> Iterator[dict[str, ShoppingAgentState]]:
        return self._graph.stream(
            {
                "pet": pet,
                "text": text,
                "records": records,
                "suggestions": suggestions,
            },
            stream_mode="updates",
        )

    def _build_graph(self):
        graph = StateGraph(ShoppingAgentState)
        graph.add_node("prepare_categories", self._prepare_categories)
        graph.add_node("search_products", self._search_products)
        graph.add_node("select_recommendations", self._select_recommendations_node)
        graph.add_node("build_result", self._build_result)
        graph.add_edge(START, "prepare_categories")
        graph.add_edge("prepare_categories", "search_products")
        graph.add_edge("search_products", "select_recommendations")
        graph.add_edge("select_recommendations", "build_result")
        graph.add_edge("build_result", END)
        return graph.compile()

    def _prepare_categories(self, state: ShoppingAgentState) -> ShoppingAgentState:
        return {
            "category_requests": self._category_requests_for(
                state["pet"],
                state["text"],
                state["records"],
                state["suggestions"],
            )
        }

    def _search_products(self, state: ShoppingAgentState) -> ShoppingAgentState:
        category_requests = state["category_requests"]
        if self._recommendation_agent is not None and not category_requests:
            return {"recommendations": ()}
        return {
            "recommendations": self._recommendation_provider.recommend(
                state["pet"],
                state["text"],
                state["records"],
                category_requests=category_requests,
                suggestions=state["suggestions"],
            )
        }

    def _select_recommendations_node(self, state: ShoppingAgentState) -> ShoppingAgentState:
        return {
            "selected_recommendations": self._select_recommendations(
                state["pet"],
                state["text"],
                state["records"],
                state["suggestions"],
                state["recommendations"],
            )
        }

    def _build_result(self, state: ShoppingAgentState) -> ShoppingAgentState:
        return {"result": state["selected_recommendations"]}

    def _category_requests_for(
        self,
        pet: PetProfile,
        text: str,
        records: tuple[PetRecord, ...],
        suggestions: tuple[CareSuggestion, ...],
    ) -> tuple[ShoppingCategoryRequest, ...]:
        if self._recommendation_agent is None:
            return ()
        try:
            return self._recommendation_agent.category_requests_for(
                pet=pet,
                text=text,
                records=records,
                suggestions=suggestions,
            )
        except Exception as exc:
            logger.warning(
                "shopping_category_agent_failed error=%s detail=%s",
                exc.__class__.__name__,
                exc,
            )
            return ()

    def _select_recommendations(
        self,
        pet: PetProfile,
        text: str,
        records: tuple[PetRecord, ...],
        suggestions: tuple[CareSuggestion, ...],
        recommendations: tuple[ShoppingRecommendation, ...],
    ) -> tuple[ShoppingRecommendation, ...]:
        if self._recommendation_agent is None:
            return recommendations

        selected: list[ShoppingRecommendation] = []
        for query, candidates in _recommendations_by_query(recommendations):
            selected.append(
                self._select_recommendation(
                    pet=pet,
                    text=text,
                    records=records,
                    suggestions=suggestions,
                    query=query,
                    candidates=candidates[:3],
                )
            )
        return tuple(selected)

    def _select_recommendation(
        self,
        *,
        pet: PetProfile,
        text: str,
        records: tuple[PetRecord, ...],
        suggestions: tuple[CareSuggestion, ...],
        query: str,
        candidates: tuple[ShoppingRecommendation, ...],
    ) -> ShoppingRecommendation:
        fallback = candidates[0]
        try:
            selection = self._recommendation_agent.select_recommendation(
                pet=pet,
                text=text,
                records=records,
                suggestions=suggestions,
                query=query,
                candidates=candidates,
            )
        except Exception as exc:
            logger.warning(
                "shopping_selection_agent_failed error=%s detail=%s",
                exc.__class__.__name__,
                exc,
            )
            return fallback

        selected = _find_selected_candidate(selection.product_url, candidates)
        if selected is None:
            return fallback
        return replace(selected, reason=selection.reason)


class ShoppingRecommendationAgent:
    def __init__(self, recommendation_provider) -> None:
        self._recommendation_provider = recommendation_provider

    def category_requests_for(
        self,
        *,
        pet: PetProfile,
        text: str,
        records: tuple[PetRecord, ...],
        suggestions: tuple[CareSuggestion, ...],
    ) -> tuple[ShoppingCategoryRequest, ...]:
        return self._recommendation_provider.category_requests_for(
            pet=pet,
            text=text,
            records=records,
            suggestions=suggestions,
        )

    def select_recommendation(
        self,
        *,
        pet: PetProfile,
        text: str,
        records: tuple[PetRecord, ...],
        suggestions: tuple[CareSuggestion, ...],
        query: str,
        candidates: tuple[ShoppingRecommendation, ...],
    ):
        return self._recommendation_provider.select_recommendation(
            pet=pet,
            text=text,
            records=records,
            suggestions=suggestions,
            query=query,
            candidates=candidates,
        )


ShoppingRecommendationReasonAgent = ShoppingRecommendationAgent


def _recommendations_by_query(
    recommendations: tuple[ShoppingRecommendation, ...],
) -> tuple[tuple[str, tuple[ShoppingRecommendation, ...]], ...]:
    grouped: dict[str, list[ShoppingRecommendation]] = {}
    for recommendation in recommendations:
        grouped.setdefault(recommendation.query, []).append(recommendation)
    return tuple((query, tuple(candidates)) for query, candidates in grouped.items())


def _find_selected_candidate(
    product_url: str,
    candidates: tuple[ShoppingRecommendation, ...],
) -> ShoppingRecommendation | None:
    for candidate in candidates:
        if candidate.product_url == product_url or candidate.id == product_url:
            return candidate
    return None
