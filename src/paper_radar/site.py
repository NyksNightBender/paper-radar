"""Renders the static site from data/days and data/weeks."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, date, datetime, time
from email.utils import format_datetime
from importlib.resources import files
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape

from .config import INTERESTS, REPO_URL, SITE_URL
from .store import Store, week_label

NAMES = {i.key: i.name for i in INTERESTS}


def long_date(value: str) -> str:
    d = date.fromisoformat(value[:10])
    return f"{d:%A}, {d.day} {d:%B %Y}"


def short_date(value: str) -> str:
    d = date.fromisoformat(value[:10])
    return f"{d.day} {d:%b}"


def authors(names: list[str], limit: int = 4) -> str:
    return ", ".join(names) if len(names) <= limit else f"{', '.join(names[:limit])} et al."


def week_title(label: str) -> str:
    year, week = label.split("-W")
    monday = date.fromisocalendar(int(year), int(week), 1)
    friday = date.fromisocalendar(int(year), int(week), 5)
    return f"Week of {monday.day} {monday:%b} – {friday.day} {friday:%b %Y}"


def bar(score: float) -> int:
    """Width of the score bar: cosine similarities from BGE-small mostly fall in 0.5-0.9."""
    return max(4, min(100, round((score - 0.5) / 0.4 * 100)))


def environment() -> Environment:
    env = Environment(
        loader=PackageLoader("paper_radar", "templates"),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters.update(
        long_date=long_date,
        short_date=short_date,
        authors=authors,
        week_title=week_title,
        topic=lambda key: NAMES.get(key, key),
        bar=bar,
    )
    env.globals.update(repo_url=REPO_URL, site_url=SITE_URL, interests=INTERESTS)
    return env


def build(store: Store, out: Path) -> int:
    env = environment()
    days = [store.load_day(d) for d in store.days()]
    weeks = [store.load_week(w) for w in store.weeks()]
    if out.exists():
        shutil.rmtree(out)
    for folder in ("days", "weeks", "api"):
        (out / folder).mkdir(parents=True)
    static = files("paper_radar") / "static"
    for name in ("style.css", "favicon.svg"):
        (out / name).write_bytes((static / name).read_bytes())
    env.globals["asset_version"] = hashlib.sha1((static / "style.css").read_bytes()).hexdigest()[:8]

    day_tpl = env.get_template("digest.html")
    for i, day in enumerate(days):
        html = day_tpl.render(
            digest=day,
            kind="day",
            root="../",
            prev=days[i - 1]["date"] if i > 0 else None,
            next=days[i + 1]["date"] if i + 1 < len(days) else None,
        )
        (out / "days" / f"{day['date']}.html").write_text(html, encoding="utf-8")
    for week in weeks:
        html = day_tpl.render(digest=week, kind="week", root="../", prev=None, next=None)
        (out / "weeks" / f"{week['week']}.html").write_text(html, encoding="utf-8")

    latest = days[-1] if days else None
    this_week = None
    if latest:
        label = week_label(date.fromisoformat(latest["date"]))
        this_week = next((w for w in weeks if w["week"] == label), None)
        (out / "api" / "latest.json").write_text(
            json.dumps(latest, ensure_ascii=False), encoding="utf-8"
        )
    (out / "index.html").write_text(
        day_tpl.render(
            digest=latest,
            kind="day",
            root="",
            is_index=True,
            this_week=this_week,
            prev=days[-2]["date"] if len(days) > 1 else None,
            next=None,
        ),
        encoding="utf-8",
    )
    (out / "archive.html").write_text(
        env.get_template("archive.html").render(
            days=list(reversed(days)), weeks=list(reversed(weeks)), root=""
        ),
        encoding="utf-8",
    )
    (out / "about.html").write_text(
        env.get_template("about.html").render(root=""), encoding="utf-8"
    )

    def pub_date(d: dict[str, Any]) -> str:
        stamp = d.get("generated_at")
        if stamp:
            return format_datetime(datetime.fromisoformat(stamp))
        return format_datetime(datetime.combine(date.fromisoformat(d["date"]), time(), UTC))

    (out / "feed.xml").write_text(
        env.get_template("feed.xml").render(days=list(reversed(days[-30:])), pub_date=pub_date),
        encoding="utf-8",
    )
    (out / ".nojekyll").write_text("", encoding="utf-8")
    return len(days) + len(weeks) + 3
