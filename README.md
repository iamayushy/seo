# atlair-growth

A small Claude agent pipeline that tracks and grows **Atlair Cloud** and **Atlair Post** where
developers now find tools: AI assistants' answers and developer communities.

Why this and not a full "AI SEO team": see [`docs/market-research.md`](docs/market-research.md).
In short, both products are weeks old, their sites already do on-page and AI-search basics well,
and AI answers mostly draw on third-party sites (Reddit, HN, GitHub, directories, docs). So
the work that matters now is measuring visibility and showing up in those places honestly.

## What it does

| Command | What happens | Output |
|---|---|---|
| `visibility` | Asks 12 fixed developer questions per product (e.g. "open-source alternative to Resend?") through Claude with web search. The product name is never in the request. Checks which tools each answer names, in what order, and which sites it cites. Appends to history so weekly runs are comparable. | `reports/<product>/visibility.md`, `data/visibility/<product>.jsonl` |
| `threads` | Searches Reddit, HN, GitHub, Stack Overflow and dev.to for threads where someone has the problem the product solves, judges the fit (strong / partial / none) and drafts an honest reply that discloses who wrote it. **Never posts anything.** Drops any URL web search didn't actually return, and skips threads already reviewed. | `reports/<product>/threads.md` |
| `launch-kit` | Drafts positioning, a GitHub description and topics, a README intro, a Show HN post, Reddit posts, places to be listed, and the gaps to close first. Uses only the facts in `products/<id>.md` and the latest visibility results. | `reports/<product>/launch-kit.md` |
| `all` | All three. | |

## Run it

```bash
pip install -e ".[dev]"
export ANTHROPIC_API_KEY=...          # or `ant auth login`
python -m growth visibility            # both products
python -m growth threads --product post
python -m growth launch-kit --product cloud
python -m growth all
```

Results go in `reports/` and `data/`. Commit them to keep a history.

`.github/workflows/weekly.yml` runs `visibility` and `threads` every Monday and commits the results.
It needs an `ANTHROPIC_API_KEY` repository secret.

## Configure

- `products.toml`: prompts, competitors, brand terms, thread searches and allowed communities for
  each product. Add prompts rather than editing old ones, so runs stay comparable.
- `products/cloud.md`, `products/post.md`: product facts (from each site's `llms.txt`). Agents
  only claim what's written here, so update them when features ship.
- `ATLAIR_GROWTH_MODEL` env var overrides the model (default `claude-opus-5-5`).

## Limits to know

- **Only Claude is measured.** The visibility numbers are Claude-with-web-search answers, a proxy
  for AI search in general. ChatGPT, Perplexity and Gemini each cite different sites. Adding
  them means one small client per provider in `growth/visibility.py`.
- **Answers vary between runs.** Read trends over several weeks, not single-run changes.
- **Drafts need a person.** Thread replies and launch copy are drafts. Check claims against
  the product and follow each community's self-promotion rules.
- **Cost isn't measured yet.** Each run costs web-search fees plus model tokens. A rough guess is
  a few dollars per weekly run for both products; check the Anthropic console after the first run.

## Tests

```bash
python -m pytest -q
```

The tests cover config loading, mention detection, report rendering and thread filtering. They
don't call the API.
