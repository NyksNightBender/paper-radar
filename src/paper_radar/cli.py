"""Command line: `paper-radar fetch`, `paper-radar site`, `paper-radar readme`."""

from __future__ import annotations

import argparse
import asyncio
import os
from datetime import date
from pathlib import Path

from . import readme, site
from .arxiv import fetch_recent
from .config import Settings
from .pipeline import run, utc_today
from .rank import FastEmbedder
from .store import Store


def _github_output(**values: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            for key, value in values.items():
                f.write(f"{key}={value}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="paper-radar")
    parser.add_argument("--data", type=Path, default=Path("data"))
    sub = parser.add_subparsers(dest="command", required=True)
    fetch = sub.add_parser("fetch", help="score new arXiv papers and write digests")
    fetch.add_argument("--today", type=date.fromisoformat, default=None)
    fetch.add_argument("--cache", default=".cache/fastembed", help="model cache directory")
    build = sub.add_parser("site", help="render the static site")
    build.add_argument("--out", type=Path, default=Path("_site"))
    sub.add_parser("readme", help="refresh the table in README.md")
    args = parser.parse_args(argv)
    store = Store(args.data)

    if args.command == "fetch":
        embedder = FastEmbedder(cache_dir=args.cache)
        written = asyncio.run(
            run(store, fetch_recent, embedder, Settings(), args.today or utc_today())
        )
        print("wrote:", ", ".join(written) or "nothing new")
        _github_output(written=str(len(written)), labels=" ".join(written))
    elif args.command == "site":
        print(f"Wrote {site.build(store, args.out)} pages to {args.out}")
    elif args.command == "readme":
        days = store.days()
        if days:
            readme.update(Path("README.md"), store.load_day(days[-1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
