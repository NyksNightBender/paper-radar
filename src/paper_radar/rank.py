"""Scores papers against the research interests with sentence embeddings."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

import numpy as np
import numpy.typing as npt

from .arxiv import Paper
from .config import INTERESTS, MODEL, Interest

Matrix = npt.NDArray[np.float32]


class Embedder(Protocol):
    def queries(self, texts: Sequence[str]) -> Matrix: ...
    def passages(self, texts: Sequence[str]) -> Matrix: ...


class FastEmbedder:
    """BGE-small through fastembed (ONNX, CPU). Queries get BGE's retrieval instruction."""

    def __init__(self, cache_dir: str | None = None) -> None:
        from fastembed import TextEmbedding

        self._model: Any = TextEmbedding(MODEL, cache_dir=cache_dir)

    def queries(self, texts: Sequence[str]) -> Matrix:
        return np.array(list(self._model.query_embed(list(texts))), dtype=np.float32)

    def passages(self, texts: Sequence[str]) -> Matrix:
        return np.array(list(self._model.passage_embed(list(texts))), dtype=np.float32)


def _normalise(m: Matrix) -> Matrix:
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    return m / np.clip(norms, 1e-12, None)


def score(
    papers: Sequence[Paper], embedder: Embedder, interests: Sequence[Interest] = INTERESTS
) -> list[dict[str, Any]]:
    """Each paper with its cosine similarity to every interest; best first."""
    if not papers:
        return []
    q = _normalise(embedder.queries([i.text for i in interests]))
    p = _normalise(embedder.passages([f"{x.title}. {x.abstract}" for x in papers]))
    sims = p @ q.T  # papers x interests
    ranked: list[dict[str, Any]] = []
    for paper, row in zip(papers, sims, strict=True):
        best = int(np.argmax(row))
        ranked.append(
            {
                **paper.as_dict(),
                "score": round(float(row[best]), 4),
                "interest": interests[best].key,
                "scores": {i.key: round(float(v), 4) for i, v in zip(interests, row, strict=True)},
            }
        )
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked
