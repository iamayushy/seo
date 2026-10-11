"""Loads products.toml into typed product definitions."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "products.toml"
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"


@dataclass(frozen=True)
class Competitor:
    name: str
    regex: re.Pattern[str]


@dataclass(frozen=True)
class Product:
    id: str
    name: str
    url: str
    facts: str
    brand_regex: re.Pattern[str]
    competitors: list[Competitor]
    prompts: list[str]
    thread_queries: list[str]
    communities: list[str] = field(default_factory=list)


def _phrase_regex(phrases: list[str]) -> re.Pattern[str]:
    # Whole-word, case-insensitive match on any of the phrases.
    alternatives = "|".join(re.escape(p) for p in sorted(phrases, key=len, reverse=True))
    return re.compile(rf"(?<![\w.-])(?:{alternatives})(?![\w-])", re.IGNORECASE)


def _competitor(entry: dict) -> Competitor:
    name = entry["name"]
    if "pattern" in entry:
        return Competitor(name, re.compile(entry["pattern"]))
    return Competitor(name, _phrase_regex([name]))


def load_products(path: Path = DEFAULT_CONFIG) -> dict[str, Product]:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    products: dict[str, Product] = {}
    for entry in raw["products"]:
        facts_path = path.parent / entry["facts_file"]
        products[entry["id"]] = Product(
            id=entry["id"],
            name=entry["name"],
            url=entry["url"],
            facts=facts_path.read_text(encoding="utf-8"),
            brand_regex=_phrase_regex(entry["brand_terms"]),
            competitors=[_competitor(c) for c in entry.get("competitors", [])],
            prompts=list(entry["prompts"]),
            thread_queries=list(entry.get("thread_queries", [])),
            communities=list(entry.get("communities", [])),
        )
    return products
