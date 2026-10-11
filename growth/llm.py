"""Thin wrapper around the Claude API: a web-search research call and a structured-output call."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import TypeVar

import anthropic
from pydantic import BaseModel

MODEL = os.environ.get("ATLAIR_GROWTH_MODEL", "claude-opus-5-5")
MAX_TOKENS = 64000
MAX_CONTINUATIONS = 5

# Server-side fallback: if a safety classifier declines a request, the API re-runs it on a
# fallback model chosen by refusal category instead of returning the refusal.
FALLBACK_BETA = "server-side-fallback-2026-07-01"

T = TypeVar("T", bound=BaseModel)


class AgentError(RuntimeError):
    pass


@dataclass
class Source:
    url: str
    title: str


@dataclass
class ResearchResult:
    text: str
    sources: list[Source] = field(default_factory=list)  # every page web search returned
    cited_urls: list[str] = field(default_factory=list)  # pages the answer actually cites


@lru_cache(maxsize=1)
def client() -> anthropic.Anthropic:
    return anthropic.Anthropic()


def _check_stop(response) -> None:
    if response.stop_reason == "refusal":
        details = getattr(response, "stop_details", None)
        category = getattr(details, "category", None) if details else None
        raise AgentError(f"Request declined (category: {category}).")
    if response.stop_reason == "max_tokens":
        raise AgentError("Response hit max_tokens before finishing.")


def collect(responses: list) -> ResearchResult:
    """Pull the answer text, search results and citations out of one or more responses."""
    texts: list[str] = []
    sources: dict[str, Source] = {}
    cited: dict[str, None] = {}
    for response in responses:
        for block in response.content:
            if block.type == "text":
                texts.append(block.text)
                for citation in getattr(block, "citations", None) or []:
                    url = getattr(citation, "url", None)
                    if url:
                        cited[url] = None
            elif block.type == "web_search_tool_result":
                # Success is a list of results; an error is a single object.
                if isinstance(block.content, list):
                    for result in block.content:
                        sources.setdefault(result.url, Source(result.url, result.title or ""))
    return ResearchResult("".join(texts).strip(), list(sources.values()), list(cited))


def research(
    system: str,
    prompt: str,
    *,
    allowed_domains: list[str] | None = None,
    max_searches: int = 5,
    effort: str = "medium",
) -> ResearchResult:
    """Run one request with the web search tool and return the answer plus its sources."""
    tool: dict = {"type": "web_search_20260209", "name": "web_search", "max_uses": max_searches}
    if allowed_domains:
        tool["allowed_domains"] = allowed_domains

    messages: list[dict] = [{"role": "user", "content": prompt}]
    responses = []
    assistant_blocks: list = []
    for _ in range(MAX_CONTINUATIONS + 1):
        with client().beta.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=messages,
            tools=[tool],
            output_config={"effort": effort},
            betas=[FALLBACK_BETA],
            fallbacks="default",
        ) as stream:
            response = stream.get_final_message()
        responses.append(response)
        if response.stop_reason != "pause_turn":
            break
        # The server-side search loop paused; send the turn so far back and it resumes.
        assistant_blocks.extend(response.content)
        messages = [messages[0], {"role": "assistant", "content": assistant_blocks}]
    else:
        raise AgentError("Web search kept pausing; gave up after several continuations.")

    _check_stop(responses[-1])
    return collect(responses)


def structured(system: str, prompt: str, schema: type[T], *, effort: str = "high") -> T:
    """Ask for output that matches a Pydantic schema and return the validated object."""
    with client().beta.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": prompt}],
        output_format=schema,
        output_config={"effort": effort},
        betas=[FALLBACK_BETA],
        fallbacks="default",
    ) as stream:
        response = stream.get_final_message()
    _check_stop(response)
    if response.parsed_output is None:
        raise AgentError("Model returned no structured output.")
    return response.parsed_output
