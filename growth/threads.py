"""Community scout: find public threads where the product genuinely helps, and draft replies.

Nothing is ever posted. Drafts go into a review queue for a person to edit and post (or not).
Only threads whose URL came back from web search are kept, so the queue can't contain
invented links.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from . import llm
from .config import DATA_DIR, Product

SCOUT_SYSTEM = (
    "You find public developer discussions. Search the allowed communities for recent threads "
    "(ideally from the last six months) where someone describes a problem or asks for a "
    "recommendation. For each thread you find, report its exact URL, its title, roughly when it "
    "was posted if you can tell, and in one or two sentences what the person needs."
)

REPLY_SYSTEM = """You help a small developer-tools team take part in community threads honestly.

For each thread, decide how well the product fits what the person actually needs:
- strong: the product directly solves the stated problem today.
- partial: it helps, but the person needs something the product doesn't do yet.
- none: it doesn't help, the thread is off-topic, or the thread is mainly about something else.

Then draft a reply a real engineer on the team could post:
- Answer the question first, with useful advice that stands on its own even without the product.
- Mention the product only where it fits, once, by name. Say plainly that the writer works on it.
- State relevant limits from the product facts (features that aren't built yet, no pricing yet).
- Mention competitors fairly when they are the better fit.
- Write in a plain, conversational tone, under 150 words, without marketing language, emoji or
  more than one link.
For fit "none", leave the reply empty."""


class Thread(BaseModel):
    url: str
    title: str
    platform: str
    posted: str
    need: str
    fit: Literal["strong", "partial", "none"]
    fit_reason: str
    reply: str


class ThreadBatch(BaseModel):
    threads: list[Thread]


def normalize(url: str) -> str:
    return url.split("#")[0].split("?")[0].rstrip("/").lower()


def seen_path(product: Product) -> Path:
    return DATA_DIR / "threads" / f"{product.id}-seen.json"


def load_seen(product: Product) -> set[str]:
    path = seen_path(product)
    return set(json.loads(path.read_text(encoding="utf-8"))) if path.exists() else set()


def save_seen(product: Product, seen: set[str]) -> None:
    path = seen_path(product)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(seen), indent=2) + "\n", encoding="utf-8")


def keep(threads: list[Thread], found_urls: set[str], seen: set[str]) -> list[Thread]:
    """Drop invented URLs, threads already handled, duplicates, and threads that don't fit."""
    kept: list[Thread] = []
    for t in threads:
        key = normalize(t.url)
        if key not in found_urls or key in seen:
            continue
        seen.add(key)  # judged once, so it isn't re-drafted next run
        if t.fit != "none":
            kept.append(t)
    order = {"strong": 0, "partial": 1}
    return sorted(kept, key=lambda t: order[t.fit])


def run(product: Product, limit: int = 15) -> list[Thread]:
    queries = "\n".join(f"- {q}" for q in product.thread_queries)
    found = llm.research(
        SCOUT_SYSTEM,
        f"Find up to {limit} threads. Searches worth trying:\n{queries}",
        allowed_domains=product.communities or None,
        max_searches=8,
        effort="high",
    )
    found_urls = {normalize(s.url) for s in found.sources} | {normalize(u) for u in found.cited_urls}
    if not found_urls:
        return []

    batch = llm.structured(
        REPLY_SYSTEM,
        f"<product_facts>\n{product.facts}\n</product_facts>\n\n"
        f"<scout_notes>\n{found.text}\n</scout_notes>\n\n"
        "Return one entry per thread in the scout notes, using each thread's exact URL.",
        ThreadBatch,
    )
    seen = load_seen(product)
    threads = keep(batch.threads, found_urls, seen)
    save_seen(product, seen)
    return threads


def render(product: Product, threads: list[Thread]) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        f"# {product.name}: threads to reply to ({stamp})",
        "",
        "Drafts only. Read each thread in full, edit the reply in your own voice, and post it "
        "yourself only if it really helps. Follow each community's rules on self-promotion.",
        "",
    ]
    if not threads:
        lines.append("No new threads found this run.")
    for t in threads:
        lines += [
            f"## [{t.title}]({t.url})",
            "",
            f"*{t.platform} · {t.posted or 'date unknown'} · fit: **{t.fit}** ({t.fit_reason})*",
            "",
            f"**Need:** {t.need}",
            "",
            "**Draft reply:**",
            "",
            *[f"> {line}" if line else ">" for line in t.reply.splitlines()],
            "",
        ]
    return "\n".join(lines)
