"""Command line: atlair-growth {visibility,threads,launch-kit,all} [--product cloud|post|all]"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import launch, threads, visibility
from .config import DEFAULT_CONFIG, REPORTS_DIR, Product, load_products


def write_report(product: Product, name: str, text: str) -> Path:
    path = REPORTS_DIR / product.id / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def cmd_visibility(product: Product) -> None:
    print(f"[{product.id}] asking {len(product.prompts)} prompts…", flush=True)
    record = visibility.run(product)
    visibility.save(product, record)
    summary = visibility.summarize(record)
    path = write_report(product, "visibility.md", visibility.render(product, visibility.load_history(product)))
    print(f"[{product.id}] mentioned in {summary['mentioned']}/{summary['answered']} answers → {path}")


def cmd_threads(product: Product) -> None:
    print(f"[{product.id}] scouting threads…", flush=True)
    found = threads.run(product)
    path = write_report(product, "threads.md", threads.render(product, found))
    print(f"[{product.id}] {len(found)} new threads to review → {path}")


def cmd_launch(product: Product) -> None:
    print(f"[{product.id}] drafting launch kit…", flush=True)
    kit = launch.run(product)
    path = write_report(product, "launch-kit.md", launch.render(product, kit))
    print(f"[{product.id}] launch kit → {path}")


COMMANDS = {
    "visibility": [cmd_visibility],
    "threads": [cmd_threads],
    "launch-kit": [cmd_launch],
    "all": [cmd_visibility, cmd_threads, cmd_launch],
}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="atlair-growth", description=__doc__)
    parser.add_argument("command", choices=COMMANDS)
    parser.add_argument("--product", default="all", help="product id from products.toml, or 'all'")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)

    products = load_products(args.config)
    if args.product == "all":
        selected = list(products.values())
    elif args.product in products:
        selected = [products[args.product]]
    else:
        parser.error(f"unknown product {args.product!r}; choose from {', '.join(products)} or all")

    failed = False
    for product in selected:
        for command in COMMANDS[args.command]:
            try:
                command(product)
            except Exception as exc:
                failed = True
                print(f"[{product.id}] {command.__name__} failed: {type(exc).__name__}: {exc}", file=sys.stderr)
    sys.exit(1 if failed else 0)
