from __future__ import annotations

from domain.models import PetProfile, PetRecord, ShoppingRecommendation


DOG_TERMS = ("강아지", "반려견", "애견", "댕댕", "멍멍")


class ShoppingRecommendationProvider:
    def __init__(self, shopping_client) -> None:
        self._shopping_client = shopping_client

    def recommend(
        self,
        pet: PetProfile,
        text: str,
        records: tuple[PetRecord, ...],
    ) -> tuple[ShoppingRecommendation, ...]:
        if not records or not _is_dog_context(pet, text, records):
            return ()

        recommendations: list[ShoppingRecommendation] = []
        seen_urls: set[str] = set()
        for record in records:
            query = _query_for_record(text, record)
            if query is None:
                continue

            items = self._shopping_client.search(
                query,
                reason=f"{record.title} 기록과 관련된 상품 추천",
                source_record_ids=(record.id,),
            )
            for item in items:
                if item.product_url in seen_urls:
                    continue
                seen_urls.add(item.product_url)
                recommendations.append(item)

        return tuple(recommendations)


def _is_dog_context(pet: PetProfile, text: str, records: tuple[PetRecord, ...]) -> bool:
    if (pet.species or "").lower() == "dog":
        return True
    haystack = " ".join((text, pet.breed or "", pet.personality or "", *pet.notes, *(_record_text(record) for record in records)))
    return any(term in haystack for term in DOG_TERMS)


def _query_for_record(text: str, record: PetRecord) -> str | None:
    haystack = f"{text} {_record_text(record)}"
    if "배변패드" in haystack or "패드" in haystack:
        return "반려견 배변패드"
    if "배변봉투" in haystack or record.category == "stool":
        return "반려견 배변봉투"
    if record.category == "meal" or _contains_any(haystack, ("사료", "밥", "급여", "간식")):
        return "반려견 사료"
    if record.category == "walk":
        return "반려견 산책용품"
    if record.category == "medical":
        return "반려견 영양제"
    if record.category == "behavior":
        return "반려견 장난감"
    return None


def _record_text(record: PetRecord) -> str:
    return f"{record.title} {record.detail}"


def _contains_any(value: str, terms: tuple[str, ...]) -> bool:
    return any(term in value for term in terms)
