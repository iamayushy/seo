from types import SimpleNamespace as NS

import pytest

from growth import launch, llm, threads, visibility
from growth.config import load_products


@pytest.fixture(scope="module")
def products():
    return load_products()


def research(text, urls=()):
    return llm.ResearchResult(text, [llm.Source(u, "") for u in urls], list(urls))


def test_config_loads_both_products(products):
    assert set(products) == {"cloud", "post"}
    for p in products.values():
        assert p.prompts and p.competitors and p.facts
        # The answering prompts must not name the product, or the measurement is biased.
        assert not any(p.brand_regex.search(q) for q in p.prompts)


def test_brand_match_ignores_altair(products):
    cloud = products["cloud"]
    assert cloud.brand_regex.search("Try Atlair for that.")
    assert cloud.brand_regex.search("deploy to atlair.app")
    assert not cloud.brand_regex.search("Altair Engineering makes simulation software.")


def test_analyze_orders_tools_and_skips_everyday_words(products):
    cloud = products["cloud"]
    text = "First render the page. Use Vercel for Next.js; Railway or Atlair for Go. Render.com also works."
    result = visibility.analyze(cloud, "q", research(text, ["https://www.reddit.com/r/x", "https://docs.railway.com/a"]))
    assert result.mentioned and result.position == 3
    assert result.competitors == ["Vercel", "Railway", "Render"]
    assert result.cited_domains == ["reddit.com", "docs.railway.com"]


def test_analyze_not_mentioned(products):
    result = visibility.analyze(products["post"], "q", research("Use Resend or AWS SES."))
    assert not result.mentioned and result.position is None
    assert result.competitors == ["Resend", "Amazon SES"]


def test_collect_reads_text_citations_and_search_results():
    response = NS(content=[
        NS(type="server_tool_use"),
        NS(type="web_search_tool_result", content=[NS(url="https://a.dev/x", title="A")]),
        NS(type="web_search_tool_result", content=NS(error_code="max_uses_exceeded")),
        NS(type="text", text="Use X. ", citations=[NS(url="https://a.dev/x")]),
        NS(type="text", text="Done.", citations=None),
    ])
    result = llm.collect([response])
    assert result.text == "Use X. Done."
    assert [s.url for s in result.sources] == ["https://a.dev/x"]
    assert result.cited_urls == ["https://a.dev/x"]


def test_summary_and_report_render(products):
    post = products["post"]
    results = [
        visibility.analyze(post, "a", research("Atlair Post or Resend.", ["https://reddit.com/1"])),
        visibility.analyze(post, "b", research("Resend.", ["https://reddit.com/2"])),
        visibility.PromptResult(prompt="c", error="APIError: boom"),
    ]
    record = {"run_at": "2026-10-11T00:00:00+00:00", "model": "m", "product": "post",
              "results": [vars(r) for r in results]}
    summary = visibility.summarize(record)
    assert (summary["mentioned"], summary["answered"], summary["failed"]) == (1, 2, 1)
    assert summary["share_of_voice"] == [("Resend", 2)]
    assert summary["top_domains"] == [("reddit.com", 2)]
    report = visibility.render(post, [record, record])
    assert "Mentioned in 1 of 2 answers (50%)" in report and "Previous run" in report


def thread(url, fit="strong"):
    return threads.Thread(url=url, title="t", platform="reddit", posted="", need="n",
                          fit=fit, fit_reason="r", reply="hi")


def test_threads_keep_only_real_new_fitting_urls():
    found = {threads.normalize("https://reddit.com/r/a/1"), threads.normalize("https://reddit.com/r/a/2"),
             threads.normalize("https://reddit.com/r/a/3")}
    seen = {threads.normalize("https://reddit.com/r/a/2")}
    kept = threads.keep([
        thread("https://reddit.com/r/a/1/?utm=x", fit="partial"),
        thread("https://reddit.com/r/a/2"),             # already handled
        thread("https://reddit.com/r/a/3", fit="none"),  # judged, not a fit
        thread("https://reddit.com/r/invented"),         # never returned by search
        thread("https://reddit.com/r/a/1"),              # duplicate
    ], found, seen)
    assert [t.url for t in kept] == ["https://reddit.com/r/a/1/?utm=x"]
    assert threads.normalize("https://reddit.com/r/a/3") in seen


def test_launch_render(products):
    kit = launch.LaunchKit(
        positioning="p", github_description="d", github_topics=["ses"], readme_intro="# R",
        show_hn_title="Show HN: X – Y", show_hn_body="b",
        reddit_posts=[launch.RedditPost(subreddit="r/selfhosted", title="t", body="b")],
        places_to_be_listed=["awesome-selfhosted"], gaps_to_close=["Node SDK"],
    )
    text = launch.render(products["post"], kit)
    assert "### r/selfhosted: t" in text and "1. Node SDK" in text and "`ses`" in text
