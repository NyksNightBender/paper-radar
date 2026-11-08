"""One run: fetch the newest matching papers, score the unseen ones, write digests."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime, timedelta
from typing import Any

from .arxiv import Paper
from .config import INTERESTS, MODEL, Settings
from .rank import Embedder, score
from .store import Store, week_label

Fetch = Callable[[int], Awaitable[list[Paper]]]


def utc_today() -> date:
    return datetime.now(UTC).date()


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def digest(day: date, ranked: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "date": day.isoformat(),
        "generated_at": _now(),
        "model": MODEL,
        "interests": [{"key": i.key, "name": i.name} for i in INTERESTS],
        "count": len(ranked),
        "papers": ranked,
    }


def week_digest(store: Store, label: str, days: list[date], shown: int) -> dict[str, Any]:
    papers: list[dict[str, Any]] = []
    for day in days:
        papers += [{**p, "date": day.isoformat()} for p in store.load_day(day)["papers"]]
    papers.sort(key=lambda p: p["score"], reverse=True)
    return {
        "week": label,
        "start": days[0].isoformat(),
        "end": days[-1].isoformat(),
        "days": [d.isoformat() for d in days],
        "generated_at": _now(),
        "model": MODEL,
        "interests": [{"key": i.key, "name": i.name} for i in INTERESTS],
        "count": len(papers),
        "papers": papers[:shown],
    }


async def run(
    store: Store, fetch: Fetch, embedder: Embedder, settings: Settings, today: date
) -> list[str]:
    """Returns labels of the digests written (days as YYYY-MM-DD, weeks as YYYY-Www)."""
    written: list[str] = []
    seen = store.seen()
    first_run = not seen
    papers = await fetch(settings.max_results)
    new = [p for p in papers if p.id not in seen]

    if first_run:
        # Start with a week of history so the site is not empty on day one.
        by_day: dict[date, list[Paper]] = defaultdict(list)
        oldest = today - timedelta(days=settings.backfill_days)
        for paper in new:
            published = date.fromisoformat(paper.published[:10]) if paper.published else today
            if oldest <= published < today:
                by_day[published].append(paper)
        for day, group in sorted(by_day.items()):
            store.save_day(day, digest(day, score(group, embedder)))
            written.append(day.isoformat())
    elif new:
        ranked = score(new, embedder)
        if store.has_day(today):  # a second announcement batch on the same day
            ranked = sorted(
                store.load_day(today)["papers"] + ranked, key=lambda p: p["score"], reverse=True
            )
        store.save_day(today, digest(today, ranked))
        written.append(today.isoformat())

    # On the weekend, when arXiv is quiet, collect the week's best papers.
    if today.weekday() >= 5:
        label = week_label(today)
        monday = today - timedelta(days=today.weekday())
        days = [d for d in store.days() if monday <= d <= today]
        if days and not store.has_week(label):
            store.save_week(label, week_digest(store, label, days, settings.week_shown))
            written.append(label)

    if new:
        store.save_seen(seen | {p.id for p in papers})
    return written
