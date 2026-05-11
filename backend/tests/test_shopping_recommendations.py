from __future__ import annotations

import unittest
from unittest.mock import patch

from domain.models import PetProfile, PetRecord, ShoppingRecommendation
from infrastructure.shopping import NaverShoppingClient, NaverShoppingConfig, ShoppingRecommendationProvider


class FakeShoppingClient:
    def __init__(self) -> None:
        self.searches: list[tuple[str, str, tuple[str, ...]]] = []

    def search(
        self,
        query: str,
        *,
        reason: str,
        source_record_ids: tuple[str, ...],
    ) -> tuple[ShoppingRecommendation, ...]:
        self.searches.append((query, reason, source_record_ids))
        return (
            ShoppingRecommendation(
                title="반려견 사료",
                product_url="https://shopping.example/products/food",
                image_url="https://shopping.example/products/food.jpg",
                mall_name="sample mall",
                lowest_price=12000,
                query=query,
                reason=reason,
                source_record_ids=source_record_ids,
            ),
        )


class TestShoppingRecommendations(unittest.TestCase):
    def test_recommends_dog_food_for_saved_meal_record(self) -> None:
        client = FakeShoppingClient()
        provider = ShoppingRecommendationProvider(client)
        record = PetRecord(
            id="record-1",
            pet_id="pet-1",
            category="meal",
            title="아침 식사",
            detail="사료를 조금 남겼어요.",
            status="notice",
            recorded_at="2026-05-11T08:00:00Z",
            source="manual",
        )

        recommendations = provider.recommend(
            PetProfile(id="pet-1", name="초코", species="dog"),
            "아침 식사 기록",
            (record,),
        )

        self.assertEqual(client.searches[0][0], "반려견 사료")
        self.assertEqual(recommendations[0].query, "반려견 사료")
        self.assertEqual(recommendations[0].source_record_ids, ("record-1",))

    def test_recommends_waste_bags_for_stool_record(self) -> None:
        client = FakeShoppingClient()
        provider = ShoppingRecommendationProvider(client)
        record = PetRecord(
            id="record-1",
            pet_id="pet-1",
            category="stool",
            title="배변",
            detail="산책 중 배변했어요.",
            status="normal",
            recorded_at="2026-05-11T08:00:00Z",
            source="manual",
        )

        provider.recommend(PetProfile(id="pet-1", name="초코", species="dog"), "배변 기록", (record,))

        self.assertEqual(client.searches[0][0], "반려견 배변봉투")

    def test_skips_non_dog_context(self) -> None:
        client = FakeShoppingClient()
        provider = ShoppingRecommendationProvider(client)
        record = PetRecord(
            id="record-1",
            pet_id="pet-1",
            category="meal",
            title="아침 식사",
            detail="사료를 조금 남겼어요.",
            status="notice",
            recorded_at="2026-05-11T08:00:00Z",
            source="manual",
        )

        recommendations = provider.recommend(PetProfile(id="pet-1", name="나비", species="cat"), "식사 기록", (record,))

        self.assertEqual(recommendations, ())
        self.assertEqual(client.searches, [])

    def test_naver_client_returns_empty_without_credentials(self) -> None:
        client = NaverShoppingClient(
            NaverShoppingConfig(
                client_id="",
                client_secret="",
            )
        )

        self.assertEqual(client.search("반려견 사료", reason="기록 기반 추천", source_record_ids=("record-1",)), ())

    def test_naver_client_maps_json_response(self) -> None:
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self) -> bytes:
                return (
                    b'{"items":[{"title":"<b>sample</b> food","link":"https://example.com/item",'
                    b'"image":"https://example.com/item.jpg","mallName":"mall","lprice":"9900"}]}'
                )

        client = NaverShoppingClient(
            NaverShoppingConfig(
                client_id="id",
                client_secret="secret",
            )
        )

        with patch("infrastructure.shopping.naver_shopping.urlopen", return_value=FakeResponse()):
            recommendations = client.search("반려견 사료", reason="기록 기반 추천", source_record_ids=("record-1",))

        self.assertEqual(recommendations[0].title, "sample food")
        self.assertEqual(recommendations[0].lowest_price, 9900)
        self.assertEqual(recommendations[0].source_record_ids, ("record-1",))


if __name__ == "__main__":
    unittest.main()
