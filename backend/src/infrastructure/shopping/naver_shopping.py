from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from domain.models import ShoppingRecommendation


logger = logging.getLogger(__name__)

NAVER_SHOPPING_ENDPOINT = "https://openapi.naver.com/v1/search/shop.json"
ALLOWED_SORTS = {"sim", "date", "asc", "dsc"}


@dataclass(frozen=True)
class NaverShoppingConfig:
    client_id: str
    client_secret: str
    display: int = 3
    sort: str = "sim"
    filter: str | None = None
    exclude: str | None = "used:rental:cbshop"
    timeout: float = 3.0

    @classmethod
    def from_env(cls) -> NaverShoppingConfig:
        return cls(
            client_id=os.environ.get("NAVER_SHOPPING_CLIENT_ID", ""),
            client_secret=os.environ.get("NAVER_SHOPPING_CLIENT_SECRET", ""),
            display=_bounded_int(os.environ.get("NAVER_SHOPPING_DISPLAY"), default=3, minimum=1, maximum=10),
            sort=_allowed_sort(os.environ.get("NAVER_SHOPPING_SORT", "sim")),
            filter=os.environ.get("NAVER_SHOPPING_FILTER") or None,
            exclude=os.environ.get("NAVER_SHOPPING_EXCLUDE", "used:rental:cbshop") or None,
            timeout=_bounded_float(os.environ.get("NAVER_SHOPPING_TIMEOUT"), default=3.0, minimum=0.1),
        )

    @property
    def has_credentials(self) -> bool:
        return bool(self.client_id and self.client_secret)


class NaverShoppingClient:
    def __init__(self, config: NaverShoppingConfig | None = None) -> None:
        self._config = config or NaverShoppingConfig.from_env()

    def search(
        self,
        query: str,
        *,
        reason: str,
        source_record_ids: tuple[str, ...],
    ) -> tuple[ShoppingRecommendation, ...]:
        if not self._config.has_credentials:
            return ()

        params = {
            "query": query,
            "display": str(self._config.display),
            "start": "1",
            "sort": self._config.sort,
        }
        if self._config.filter:
            params["filter"] = self._config.filter
        if self._config.exclude:
            params["exclude"] = self._config.exclude

        request = Request(
            f"{NAVER_SHOPPING_ENDPOINT}?{urlencode(params)}",
            headers={
                "X-Naver-Client-Id": self._config.client_id,
                "X-Naver-Client-Secret": self._config.client_secret,
            },
            method="GET",
        )

        try:
            with urlopen(request, timeout=self._config.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            logger.warning("naver_shopping_search_failed query=%s error=%s", query, exc.__class__.__name__)
            return ()

        return tuple(
            _item_to_recommendation(item, query, reason, source_record_ids)
            for item in payload.get("items", ())
            if isinstance(item, dict)
        )


def _item_to_recommendation(
    item: dict[str, object],
    query: str,
    reason: str,
    source_record_ids: tuple[str, ...],
) -> ShoppingRecommendation:
    return ShoppingRecommendation(
        title=_clean_title(str(item.get("title", ""))),
        product_url=str(item.get("link", "")),
        image_url=str(item.get("image", "")),
        mall_name=str(item.get("mallName", "")),
        lowest_price=_int_or_zero(item.get("lprice")),
        query=query,
        reason=reason,
        source_record_ids=source_record_ids,
    )


def _clean_title(value: str) -> str:
    return unescape(value.replace("<b>", "").replace("</b>", ""))


def _int_or_zero(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _bounded_int(value: str | None, *, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value) if value else default
    except ValueError:
        return default
    return min(max(parsed, minimum), maximum)


def _bounded_float(value: str | None, *, default: float, minimum: float) -> float:
    try:
        parsed = float(value) if value else default
    except ValueError:
        return default
    return max(parsed, minimum)


def _allowed_sort(value: str) -> str:
    return value if value in ALLOWED_SORTS else "sim"
