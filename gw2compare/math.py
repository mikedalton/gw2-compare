"""Promotion value-delta calculations."""

from __future__ import annotations

from dataclasses import dataclass

from .api import ItemData
from .config import Item


@dataclass
class PromotionStep:
    lower_item: ItemData
    upper_item: ItemData
    quantity: int      # how many lower_item → 1 upper_item
    lower_value: int   # quantity * lower_item.buy_price
    upper_value: int   # upper_item.buy_price
    delta: int         # upper_value - lower_value


def calc_promotion(items: list[Item], data: dict[int, ItemData]) -> list[PromotionStep]:
    """
    Items are ordered highest → lowest tier (index 0 is the top tier).
    For each adjacent pair (i, i+1):
      items[i]   = upper tier
      items[i+1] = lower tier; its quantity = how many go in
      lower_value = items[i+1].quantity * data[items[i+1].item_id].buy_price
      upper_value = data[items[i].item_id].buy_price
      delta       = upper_value - lower_value
    Assumes items are already owned — only the value difference matters, not acquisition cost.
    Buy order price is used for both sides.
    Missing items from `data` are skipped silently.
    """
    steps: list[PromotionStep] = []
    for i in range(len(items) - 1):
        upper_id = items[i].item_id
        lower_id = items[i + 1].item_id
        if upper_id not in data or lower_id not in data:
            continue
        upper = data[upper_id]
        lower = data[lower_id]
        qty = items[i + 1].quantity
        lower_value = qty * lower.buy_price
        upper_value = upper.buy_price
        steps.append(
            PromotionStep(
                lower_item=lower,
                upper_item=upper,
                quantity=qty,
                lower_value=lower_value,
                upper_value=upper_value,
                delta=upper_value - lower_value,
            )
        )
    return steps
