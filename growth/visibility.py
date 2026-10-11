"""Visibility tracker: ask the fixed prompts, then check whether the answers mention the product.

The answering call never sees the product name, so the result reflects what an assistant
says on its own. Mention detection is plain regex matching, so it is cheap and repeatable.
"""

from __future__ import annotations

import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from . import llm
from .config import DATA_DIR, Product

ANSWER_SYSTEM = (
    "You are an AI assistant answering a developer's question. Search the web when it helps, "
    "then give a concise, practical answer that names the specific tools or services you "
    "recommend and briefly says why."
)


@dataclass
class PromptResult:
    prompt: str
    mentioned: bool = False
    position: int | None = None  # 1 = first tool named in the answer
    competitors: list[str] = field(default_factory=list)  # in order of first mention
    cited_domains: list[str] = field(default_factory=list)
    answer: str = ""
    error: str | None = None


def domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host.removeprefix("www.")


def analyze(product: Product, prompt: str, result: llm.ResearchResult) -> PromptResult:
    text = result.text
    first_seen: dict[str, int] = {}

    brand = product.brand_regex.search(text)
    if brand:
        first_seen[product.name] = brand.start()
    for competitor in product.competitors:
        match = competitor.regex.search(text)
        if match:
            first_seen[competitor.name] = match.start()

    ranked = sorted(first_seen, key=first_seen.get)
    urls = result.cited_urls or [s.url for s in result.sources]
    domains = list(dict.fromkeys(domain(u) for u in urls if u))

    return PromptResult(
        prompt=prompt,
        mentioned=brand is not None,
        position=ranked.index(product.name) + 1 if brand else None,
        competitors=[name for name in ranked if name != product.name],
        cited_domains=domains,
        answer=text,
    )


def ask(product: Product, prompt: str) -> PromptResult:
    try:
        result = llm.research(ANSWER_SYSTEM, prompt, max_searches=3, effort="medium")
    except Exception as exc:  # one failed prompt shouldn't sink the whole run
        return PromptResult(prompt=prompt, error=f"{type(exc).__name__}: {exc}")
    return analyze(product, prompt, result)


def run(product: Product, workers: int = 4) -> dict:
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda p: ask(product, p), product.prompts))
    return {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": llm.MODEL,
        "product": product.id,
        "results": [asdict(r) for r in results],
    }


def history_path(product: Product) -> Path:
    return DATA_DIR / "visibility" / f"{product.id}.jsonl"


def save(product: Product, record: dict) -> Path:
    path = history_path(product)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def load_history(product: Product) -> list[dict]:
    path = history_path(product)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def summarize(record: dict) -> dict:
    ok = [r for r in record["results"] if not r.get("error")]
    mentioned = [r for r in ok if r["mentioned"]]
    voice = Counter(name for r in ok for name in r["competitors"])
    domains = Counter(d for r in ok for d in r["cited_domains"])
    return {
        "answered": len(ok),
        "failed": len(record["results"]) - len(ok),
        "mentioned": len(mentioned),
        "rate": len(mentioned) / len(ok) if ok else 0.0,
        "share_of_voice": voice.most_common(),
        "top_domains": domains.most_common(15),
    }


def render(product: Product, history: list[dict]) -> str:
    latest = history[-1]
    now = summarize(latest)
    lines = [
        f"# {product.name}: AI answer visibility",
        "",
        f"Run: {latest['run_at']} · model `{latest['model']}` · {now['answered']} prompts answered"
        + (f", {now['failed']} failed" if now["failed"] else ""),
        "",
        f"**Mentioned in {now['mentioned']} of {now['answered']} answers ({now['rate']:.0%}).**",
    ]
    if len(history) > 1:
        before = summarize(history[-2])
        lines.append(f"Previous run ({history[-2]['run_at']}): {before['rate']:.0%}.")

    lines += ["", "## Per prompt", "", "| Prompt | Mentioned | Position | Tools named instead |", "|---|---|---|---|"]
    for r in latest["results"]:
        if r.get("error"):
            lines.append(f"| {r['prompt']} | error | | {r['error'][:80]} |")
            continue
        lines.append(
            f"| {r['prompt']} | {'yes' if r['mentioned'] else 'no'} | {r['position'] or ''} "
            f"| {', '.join(r['competitors'][:5])} |"
        )

    lines += ["", "## Who the answers recommend", "", "| Tool | Answers naming it |", "|---|---|"]
    lines += [f"| {name} | {count} |" for name, count in now["share_of_voice"]]

    lines += [
        "",
        "## Where the answers get their information",
        "",
        "These sites shape the answers. Getting a fair mention on them (a listing, a guide, an "
        "honest reply in a thread) is the main way to show up in future answers.",
        "",
        "| Domain | Answers citing it |",
        "|---|---|",
    ]
    lines += [f"| {d} | {count} |" for d, count in now["top_domains"]]

    lines += ["", "## Full answers", ""]
    for r in latest["results"]:
        if r.get("error"):
            continue
        lines += [f"<details><summary>{r['prompt']}</summary>", "", r["answer"], "", "</details>", ""]
    return "\n".join(lines)
