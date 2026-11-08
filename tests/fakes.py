"""Test doubles: a keyword embedder and a hand-written arXiv feed."""

from __future__ import annotations

import re
from collections.abc import Sequence

import numpy as np

from paper_radar.arxiv import Paper
from paper_radar.rank import Matrix

VOCAB = [
    "water",
    "leak",
    "pipe",
    "pressure",
    "meter",
    "consumption",
    "building",
    "energy",
    "time",
    "series",
    "isolation",
    "forest",
    "outlier",
    "anomaly",
    "privacy",
    "training",
    "language",
    "model",
    "image",
]


class KeywordEmbedder:
    """Counts vocabulary words: crude, but deterministic and enough to test the ranking."""

    def _embed(self, texts: Sequence[str]) -> Matrix:
        rows = []
        for text in texts:
            words = re.findall(r"[a-z]+", text.lower())
            rows.append([sum(w.startswith(v) for w in words) + 0.01 for v in VOCAB])
        return np.array(rows, dtype=np.float32)

    def queries(self, texts: Sequence[str]) -> Matrix:
        return self._embed(texts)

    def passages(self, texts: Sequence[str]) -> Matrix:
        return self._embed(texts)


def paper(pid: str, title: str, abstract: str, published: str) -> Paper:
    return Paper(
        id=pid,
        version=1,
        title=title,
        abstract=abstract,
        authors=["A. Yazar", "B. Yazar"],
        primary="cs.LG",
        categories=["cs.LG"],
        published=published,
        url=f"https://arxiv.org/abs/{pid}",
        pdf=f"https://arxiv.org/pdf/{pid}",
    )


FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <title type="html">ArXiv Query: search_query=abs:anomaly</title>
  <entry>
    <id>http://arxiv.org/abs/2611.01234v2</id>
    <updated>2026-11-06T10:00:00Z</updated>
    <published>2026-11-05T18:00:01Z</published>
    <title>Graph Neural Networks for Leak
      Localisation in Water Distribution Networks</title>
    <summary>  We detect and localise leaks
  from pressure sensors.  </summary>
    <author><name>Ayşe Yılmaz</name></author>
    <author><name>John Smith</name></author>
    <link href="http://arxiv.org/abs/2611.01234v2" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2611.01234v2" rel="related" type="application/pdf"/>
    <arxiv:primary_category term="eess.SP" scheme="http://arxiv.org/schemas/atom"/>
    <category term="eess.SP" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.LG" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/hep-th/0101001v1</id>
    <published>2001-01-01T00:00:00Z</published>
    <title>An old-style identifier</title>
    <summary>Abstract.</summary>
    <author><name>C. Author</name></author>
    <arxiv:primary_category term="hep-th" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
  <entry>
    <id>http://arxiv.org/api/errors#incorrect_id_format_for_1234</id>
    <title>Error</title>
    <summary>incorrect id format for 1234</summary>
  </entry>
</feed>
"""
