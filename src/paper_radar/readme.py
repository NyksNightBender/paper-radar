"""Keeps the "Latest" table in README.md current."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from .config import INTERESTS, SITE_URL

START = "<!-- LATEST:START -->"
END = "<!-- LATEST:END -->"
NAMES = {i.key: i.name for i in INTERESTS}


def render(day: dict[str, Any], limit: int = 5) -> str:
    when = date.fromisoformat(day["date"])
    papers = day["papers"][:limit]
    if not papers:
        return f"_No new papers on {when:%-d %B %Y}._"
    lines = [
        f"**Closest new papers, {when:%-d %B %Y}** ({day['count']} scanned, "
        f"[full digest]({SITE_URL}))",
        "",
        "| Score | Paper | Topic |",
        "| ---: | --- | --- |",
    ]
    for p in papers:
        title = p["title"].replace("|", "\\|")
        lines.append(
            f"| {p['score']:.2f} | [{title}]({p['url']}) | {NAMES.get(p['interest'], '')} |"
        )
    return "\n".join(lines)


def update(readme: Path, day: dict[str, Any]) -> None:
    text = readme.read_text(encoding="utf-8")
    start, end = text.find(START), text.find(END)
    if start == -1 or end < start:
        raise ValueError("README.md is missing the LATEST markers")
    readme.write_text(
        f"{text[: start + len(START)]}\n{render(day)}\n{text[end:]}", encoding="utf-8"
    )
