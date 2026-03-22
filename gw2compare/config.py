"""Data model and YAML persistence for gw2-compare."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

CONFIG_PATH = Path("config.yaml")


class GroupType(str, Enum):
    SIMPLE = "simple"
    PROMOTION = "promotion"


@dataclass
class Item:
    item_id: int
    quantity: int


@dataclass
class Group:
    name: str
    type: GroupType
    items: list[Item] = field(default_factory=list)


@dataclass
class AppConfig:
    groups: list[Group] = field(default_factory=list)


def load_config(path: Path = CONFIG_PATH) -> AppConfig:
    if not path.exists():
        return AppConfig()
    with path.open("r", encoding="utf-8") as f:
        data: Any = yaml.safe_load(f) or {}
    groups: list[Group] = []
    for g in data.get("groups", []):
        items = [Item(item_id=i["item_id"], quantity=i["quantity"]) for i in g.get("items", [])]
        groups.append(Group(name=g["name"], type=GroupType(g["type"]), items=items))
    return AppConfig(groups=groups)


def save_config(cfg: AppConfig, path: Path = CONFIG_PATH) -> None:
    data: dict[str, Any] = {
        "groups": [
            {
                "name": g.name,
                "type": g.type.value,
                "items": [{"item_id": i.item_id, "quantity": i.quantity} for i in g.items],
            }
            for g in cfg.groups
        ]
    }
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
