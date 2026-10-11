"""Launch kit: positioning, GitHub copy, a Show HN post and Reddit posts drafted from the product facts."""

from __future__ import annotations

from pydantic import BaseModel

from . import llm, visibility
from .config import Product

LAUNCH_SYSTEM = """You write launch material for a small developer-tools team.

Use only what the product facts say the product does today. Name what isn't built yet instead of
hiding it; developers trust a launch that is upfront about its limits. Write plainly, without
hype words, emoji or exclamation marks.

- Positioning: one sentence a developer would repeat to a colleague, naming the category and
  the one thing that is different. Pick the angle that the named competitors don't already own.
- GitHub description: under 300 characters, states the category and the difference.
- GitHub topics: 5-12 lowercase, hyphenated topics developers actually search.
- README intro: Markdown for the top of the README: the pitch, who it's for, a short feature
  list, what's not built yet, and a placeholder for a quickstart.
- Show HN: title in the form "Show HN: <Name> – <what it is>" under 80 characters; body written
  by the maker in first person: what it is, why it was built, what's different, what's
  missing, and a request for specific feedback.
- Reddit: one post per suggested subreddit, written for that community's norms. Lead with
  something useful (what was learned building it), not a pitch.
- Places to be listed: directories, awesome-lists and framework docs pages where this kind of
  tool is listed and where AI assistants often source recommendations. Names only, no URLs.
- Gaps: missing features most likely to make an evaluating developer leave, most important
  first."""


class RedditPost(BaseModel):
    subreddit: str
    title: str
    body: str


class LaunchKit(BaseModel):
    positioning: str
    github_description: str
    github_topics: list[str]
    readme_intro: str
    show_hn_title: str
    show_hn_body: str
    reddit_posts: list[RedditPost]
    places_to_be_listed: list[str]
    gaps_to_close: list[str]


def run(product: Product) -> LaunchKit:
    competitors = ", ".join(c.name for c in product.competitors)
    context = ""
    history = visibility.load_history(product)
    if history:
        summary = visibility.summarize(history[-1])
        named = ", ".join(f"{name} ({n})" for name, n in summary["share_of_voice"][:8])
        sources = ", ".join(d for d, _ in summary["top_domains"][:10])
        context = (
            f"\n\n<latest_ai_visibility>\nMentioned in {summary['mentioned']} of "
            f"{summary['answered']} AI answers. Tools those answers recommend: {named}. "
            f"Sites they cite: {sources}.\n</latest_ai_visibility>"
        )
    prompt = (
        f"<product_facts>\n{product.facts}\n</product_facts>\n\n"
        f"Product site: {product.url}\nMain competitors: {competitors}{context}\n\n"
        f"Write the launch kit for {product.name}."
    )
    return llm.structured(LAUNCH_SYSTEM, prompt, LaunchKit)


def render(product: Product, kit: LaunchKit) -> str:
    lines = [
        f"# {product.name}: launch kit (draft)",
        "",
        "Review everything before using it. Check every claim against the product.",
        "",
        "## Positioning",
        "",
        kit.positioning,
        "",
        "## GitHub",
        "",
        f"**Description:** {kit.github_description}",
        "",
        f"**Topics:** {', '.join(f'`{t}`' for t in kit.github_topics)}",
        "",
        "### README intro",
        "",
        kit.readme_intro,
        "",
        "## Show HN",
        "",
        f"**{kit.show_hn_title}**",
        "",
        kit.show_hn_body,
        "",
        "## Reddit",
        "",
    ]
    for post in kit.reddit_posts:
        lines += [f"### r/{post.subreddit.removeprefix('r/')}: {post.title}", "", post.body, ""]
    lines += ["## Places to be listed", ""]
    lines += [f"- {p}" for p in kit.places_to_be_listed]
    lines += ["", "## Gaps to close before pushing traffic", ""]
    lines += [f"{i}. {g}" for i, g in enumerate(kit.gaps_to_close, 1)]
    return "\n".join(lines) + "\n"
