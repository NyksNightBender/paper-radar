import asyncio
from datetime import date
from pathlib import Path

from paper_radar import readme, site
from paper_radar.arxiv import Paper
from paper_radar.config import Settings
from paper_radar.pipeline import Fetch, run
from paper_radar.store import Store
from tests.fakes import KeywordEmbedder, paper

OLD = [
    paper(
        "2611.00001",
        "Leak detection in water pipes",
        "Water leaks from pressure.",
        "2026-11-03T15:00:00+00:00",
    ),
    paper(
        "2611.00002",
        "Isolation forest for time series",
        "Outlier scores for series.",
        "2026-11-04T15:00:00+00:00",
    ),
    paper(
        "2611.00003",
        "Smart meter anomalies",
        "Building energy consumption.",
        "2026-11-04T16:00:00+00:00",
    ),
    paper("2610.09999", "Too old for the backfill", "Water.", "2026-10-20T15:00:00+00:00"),
]
NEW = [
    paper(
        "2611.00004",
        "Burst detection in water networks",
        "Pipe pressure and water.",
        "2026-11-05T15:00:00+00:00",
    )
]


def source(papers: list[Paper]) -> Fetch:
    async def fetch(_: int) -> list[Paper]:
        return papers

    return fetch


def test_runs(tmp_path: Path) -> None:
    store = Store(tmp_path / "data")
    s, emb = Settings(), KeywordEmbedder()

    # First run (a Friday): a week of history, grouped by publication date.
    first = asyncio.run(run(store, source(OLD), emb, s, date(2026, 11, 6)))
    assert first == ["2026-11-03", "2026-11-04"]
    assert store.load_day(date(2026, 11, 4))["count"] == 2
    assert "2610.09999" in store.seen()  # too old to show, but not "new" tomorrow

    # Same papers again: nothing to write.
    assert asyncio.run(run(store, source(OLD), emb, s, date(2026, 11, 6))) == []

    # Next announcement: today's digest.
    second = asyncio.run(run(store, source(NEW + OLD), emb, s, date(2026, 11, 6)))
    assert second == ["2026-11-06"]
    assert store.load_day(date(2026, 11, 6))["papers"][0]["id"] == "2611.00004"

    # Saturday: arXiv is quiet, the week's best papers are collected.
    sat = asyncio.run(run(store, source(NEW + OLD), emb, s, date(2026, 11, 7)))
    assert sat == ["2026-W45"]
    week = store.load_week("2026-W45")
    assert week["count"] == 4 and week["papers"][0]["date"]

    out = tmp_path / "_site"
    site.build(store, out)
    index = (out / "index.html").read_text(encoding="utf-8")
    assert "Burst detection in water networks" in index and "Water networks" in index
    assert (out / "weeks" / "2026-W45.html").exists() and (out / "feed.xml").exists()
    assert "Week of 2 Nov" in (out / "archive.html").read_text(encoding="utf-8")

    md = readme.render(store.load_day(date(2026, 11, 6)))
    assert "[Burst detection in water networks](https://arxiv.org/abs/2611.00004)" in md
