"""Reads the arXiv API's Atom feed."""

from __future__ import annotations

import asyncio
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import httpx

from .config import ARXIV_API, QUERY, USER_AGENT

NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


@dataclass(frozen=True)
class Paper:
    id: str  # e.g. "2611.01234", without version
    version: int
    title: str
    abstract: str
    authors: list[str]
    primary: str
    categories: list[str]
    published: str  # ISO timestamp of the first version
    url: str
    pdf: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def parse_feed(xml: str) -> list[Paper]:
    root = ET.fromstring(xml)
    papers: list[Paper] = []
    for entry in root.findall("a:entry", NS):
        raw_id = _clean(entry.findtext("a:id", default="", namespaces=NS))
        match = re.search(r"arxiv\.org/abs/(.+?)(?:v(\d+))?$", raw_id)
        if not match:
            continue  # the API reports errors as an entry without a paper id
        arxiv_id, version = match.group(1), int(match.group(2) or 1)
        primary = entry.find("arxiv:primary_category", NS)
        categories = [c.get("term", "") for c in entry.findall("a:category", NS)]
        published = _clean(entry.findtext("a:published", default="", namespaces=NS))
        papers.append(
            Paper(
                id=arxiv_id,
                version=version,
                title=_clean(entry.findtext("a:title", default="", namespaces=NS)),
                abstract=_clean(entry.findtext("a:summary", default="", namespaces=NS)),
                authors=[
                    _clean(a.findtext("a:name", default="", namespaces=NS))
                    for a in entry.findall("a:author", NS)
                ],
                primary=primary.get("term", "") if primary is not None else "",
                categories=[c for c in categories if c],
                published=datetime.fromisoformat(published.replace("Z", "+00:00")).isoformat()
                if published
                else "",
                url=f"https://arxiv.org/abs/{arxiv_id}",
                pdf=f"https://arxiv.org/pdf/{arxiv_id}",
            )
        )
    return papers


async def fetch_recent(max_results: int, retries: int = 4) -> list[Paper]:
    """Newest papers matching the query. arXiv asks for at most one request every 3 seconds."""
    # Built by hand: arXiv wants grouping as %28 %29 and quotes as %22 (already in QUERY).
    query = QUERY.replace("(", "%28").replace(")", "%29").replace(" ", "+")
    url = (
        f"{ARXIV_API}?search_query={query}&sortBy=submittedDate&sortOrder=descending"
        f"&start=0&max_results={max_results}"
    )
    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT}, timeout=httpx.Timeout(60.0), follow_redirects=True
    ) as client:
        for attempt in range(1, retries + 1):
            try:
                res = await client.get(url)
                if res.status_code == 200:
                    return parse_feed(res.text)
                problem = f"HTTP {res.status_code}"
            except httpx.TransportError as exc:
                problem = repr(exc)
            if attempt < retries:
                await asyncio.sleep(5 * attempt)
        raise RuntimeError(f"arXiv API failed: {problem}")
