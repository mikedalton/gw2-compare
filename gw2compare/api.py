"""Async GW2 API client with in-memory cache."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx

BASE = "https://api.guildwars2.com/v2"


@dataclass
class ItemData:
    item_id: int
    name: str
    buy_price: int   # copper; 0 if no buy orders
    sell_price: int  # copper; 0 if no sell listings


def format_price(copper: int) -> str:
    """Format a copper-coin value as Xg XXs XXc. Returns '-' for zero."""
    if copper <= 0:
        return "-"
    gold, remainder = divmod(copper, 10000)
    silver, copper_r = divmod(remainder, 100)
    parts: list[str] = []
    if gold:
        parts.append(f"{gold}g")
    if silver:
        parts.append(f"{silver:02d}s")
    parts.append(f"{copper_r:02d}c")
    return " ".join(parts)


class GW2Client:
    def __init__(self) -> None:
        self._cache: dict[int, ItemData] = {}
        self._http: httpx.AsyncClient | None = None

    def _client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(timeout=10.0)
        return self._http

    async def fetch_item(self, item_id: int) -> ItemData:
        if item_id in self._cache:
            return self._cache[item_id]

        client = self._client()
        name = f"Unknown ({item_id})"
        buy_price = 0
        sell_price = 0

        try:
            item_resp, price_resp = await asyncio.gather(
                client.get(f"{BASE}/items/{item_id}"),
                client.get(f"{BASE}/commerce/prices/{item_id}"),
                return_exceptions=True,
            )

            if not isinstance(item_resp, Exception) and item_resp.status_code == 200:
                name = item_resp.json().get("name", name)

            if not isinstance(price_resp, Exception) and price_resp.status_code == 200:
                price_data = price_resp.json()
                buy_price = price_data.get("buys", {}).get("unit_price", 0)
                sell_price = price_data.get("sells", {}).get("unit_price", 0)
        except Exception:
            pass

        data = ItemData(item_id=item_id, name=name, buy_price=buy_price, sell_price=sell_price)
        self._cache[item_id] = data
        return data

    async def fetch_many(self, item_ids: list[int]) -> dict[int, ItemData]:
        uncached = [i for i in item_ids if i not in self._cache]
        if uncached:
            results = await asyncio.gather(*[self.fetch_item(i) for i in uncached])
            for r in results:
                self._cache[r.item_id] = r
        return {i: self._cache[i] for i in item_ids if i in self._cache}

    def clear_cache(self) -> None:
        self._cache.clear()

    async def close(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()
