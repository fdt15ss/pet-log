# 쇼핑 추천 에이전트 LangGraph 전환 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기존 쇼핑 추천 결과와 공개 호출 방식은 유지하면서 `ShoppingAgent` 내부 실행 흐름을 LangGraph `StateGraph` 기반 워크플로우로 전환한다.

**Architecture:** `ShoppingAgent.recommend()`는 기존처럼 동기 메서드로 남기고, 내부에서 컴파일된 LangGraph를 `invoke()`한다. 그래프 노드는 카테고리 요청 생성, 상품 검색, 후보 선택, 결과 생성으로 나누며, Pet Log 파이프라인의 `stream_updates()` 패턴과 맞춰 쇼핑 에이전트도 노드 업데이트를 스트리밍할 수 있게 한다.

**Tech Stack:** Python 3.12, LangGraph `StateGraph`, `unittest`, 기존 `ShoppingRecommendationProvider`, `ShoppingRecommendationAgent`, `ShoppingFallbackMiddleware`

---

## 성공 기준

- 기존 `ShoppingAgent.recommend(pet, text, records, suggestions)` 호출 방식이 유지된다.
- 기존 쇼핑 추천 테스트가 모두 통과한다.
- `ShoppingAgent.stream_updates(...)`가 LangGraph 노드별 업데이트를 반환한다.
- 카테고리 생성 실패, 상품 선택 실패, 추천 에이전트 미설정 시 기존 동작을 유지한다.

## 변경 파일

- 수정: `backend/src/application/agents/shopping.py`
  - `ShoppingAgentState`를 추가한다.
  - `ShoppingAgent`가 초기화 시 LangGraph를 빌드하고 컴파일한다.
  - 기존 helper 메서드는 노드 내부에서 재사용한다.
  - `stream_updates()`를 추가해 그래프 실행 관찰 지점을 제공한다.
- 수정: `backend/tests/test_shopping_agent.py`
  - LangGraph 노드 업데이트가 순서대로 스트리밍되는지 확인하는 테스트를 추가한다.
  - `BaseLLMProvider`의 `invoke(..., config=...)` 호출 계약에 맞게 테스트용 `FakeChatModel` 시그니처를 유지한다.
- 생성: `docs/superpowers/plans/2026-07-06-shopping-langgraph-agent.md`
  - 이 구현 계획을 기록한다.

---

### Task 1: LangGraph 스트리밍 테스트 추가

**Files:**
- Modify: `backend/tests/test_shopping_agent.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`TestShoppingAgent`에 아래 테스트를 추가한다.

```python
    def test_streams_langgraph_node_updates(self) -> None:
        recommendation_provider = FakeRecommendationProvider()
        recommendation_agent_provider = FakeShoppingRecommendationProvider()
        recommendation_agent = ShoppingRecommendationAgent(recommendation_agent_provider)
        agent = ShoppingAgent(recommendation_provider, recommendation_agent=recommendation_agent)

        updates = tuple(
            agent.stream_updates(
                PetProfile(id="pet-1", name="Buddy", breed="Maltese", species="dog", weight_label="3.4kg"),
                "meal log",
                (_meal_record(),),
            )
        )

        self.assertEqual(
            [next(iter(update)) for update in updates],
            ["prepare_categories", "search_products", "select_recommendations", "build_result"],
        )
        self.assertEqual(
            updates[-1]["build_result"]["result"][0].product_url,
            "https://shopping.example/products/food-2",
        )
```

- [ ] **Step 2: RED 확인**

Run:

```bash
cd backend
uv run python -B -m unittest tests.test_shopping_agent.TestShoppingAgent.test_streams_langgraph_node_updates -v
```

Expected: `AttributeError: 'ShoppingAgent' object has no attribute 'stream_updates'`

---

### Task 2: ShoppingAgent 내부 LangGraph 전환

**Files:**
- Modify: `backend/src/application/agents/shopping.py`

- [ ] **Step 1: 상태 타입과 LangGraph import 추가**

```python
import warnings
from collections.abc import Iterator
from typing import TypedDict

from langchain_core._api.deprecation import LangChainPendingDeprecationWarning

warnings.simplefilter("ignore", LangChainPendingDeprecationWarning)

from langgraph.graph import END, START, StateGraph  # noqa: E402
```

```python
class ShoppingAgentState(TypedDict, total=False):
    pet: PetProfile
    text: str
    records: tuple[PetRecord, ...]
    suggestions: tuple[CareSuggestion, ...]
    category_requests: tuple[ShoppingCategoryRequest, ...]
    recommendations: tuple[ShoppingRecommendation, ...]
    selected_recommendations: tuple[ShoppingRecommendation, ...]
    result: tuple[ShoppingRecommendation, ...]
```

- [ ] **Step 2: 그래프 빌드와 실행 메서드 추가**

`ShoppingAgent.__init__()`에서 `self._graph = self._build_graph()`를 설정한다.

`recommend()`는 아래 흐름으로 바꾼다.

```python
        result = self._graph.invoke(
            {
                "pet": pet,
                "text": text,
                "records": records,
                "suggestions": suggestions,
            }
        )
        return result["result"]
```

`stream_updates()`는 아래처럼 추가한다.

```python
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
```

- [ ] **Step 3: 노드 메서드 추가**

```python
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
```

노드는 기존 helper를 재사용한다. `search_products`는 추천 에이전트가 있는데 카테고리 요청이 비어 있으면 provider를 호출하지 않고 빈 추천을 반환한다.

- [ ] **Step 4: GREEN 확인**

Run:

```bash
cd backend
uv run python -B -m unittest tests.test_shopping_agent.TestShoppingAgent.test_streams_langgraph_node_updates -v
```

Expected: `OK`

---

### Task 3: 쇼핑 추천 회귀 테스트 실행

**Files:**
- Test: `backend/tests/test_shopping_agent.py`
- Test: `backend/tests/test_shopping_fallback_middleware.py`
- Test: `backend/tests/test_pet_log_agent_pipeline.py`

- [ ] **Step 1: 쇼핑 에이전트 단위 테스트 실행**

```bash
cd backend
uv run python -B -m unittest tests.test_shopping_agent -v
```

Expected: 전체 `OK`

- [ ] **Step 2: 쇼핑 fallback 테스트 실행**

```bash
cd backend
uv run python -B -m unittest tests.test_shopping_fallback_middleware -v
```

Expected: 전체 `OK`

- [ ] **Step 3: Pet Log LangGraph 파이프라인 회귀 테스트 실행**

```bash
cd backend
uv run python -B -m unittest tests.test_pet_log_agent_pipeline -v
```

Expected: 전체 `OK`

---

## 완료 후 확인할 설명 포인트

- 이제 쇼핑 추천 에이전트 자체도 LangGraph `StateGraph`로 실행된다고 설명할 수 있다.
- 기존 Pet Log 전체 파이프라인의 `recommend_shopping` 노드는 새 LangGraph 기반 `ShoppingAgent.recommend()`를 호출한다.
- 병원 추천 에이전트는 이번 변경 범위가 아니므로 여전히 직접 provider 호출 구조로 남는다.
