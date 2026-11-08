"""Files in data/: a digest per day, a digest per week, and every arXiv id seen so far."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any


def week_label(day: date) -> str:
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


class Store:
    def __init__(self, root: Path) -> None:
        self.root = root

    def _day(self, day: date) -> Path:
        return self.root / "days" / f"{day:%Y}" / f"{day:%Y-%m-%d}.json"

    def _week(self, label: str) -> Path:
        return self.root / "weeks" / label[:4] / f"{label}.json"

    @staticmethod
    def _write(path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    @staticmethod
    def _read(path: Path) -> dict[str, Any]:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return data

    def has_day(self, day: date) -> bool:
        return self._day(day).exists()

    def save_day(self, day: date, digest: dict[str, Any]) -> None:
        self._write(self._day(day), digest)

    def load_day(self, day: date) -> dict[str, Any]:
        return self._read(self._day(day))

    def days(self) -> list[date]:
        return sorted(date.fromisoformat(p.stem) for p in (self.root / "days").glob("*/*.json"))

    def has_week(self, label: str) -> bool:
        return self._week(label).exists()

    def save_week(self, label: str, digest: dict[str, Any]) -> None:
        self._write(self._week(label), digest)

    def load_week(self, label: str) -> dict[str, Any]:
        return self._read(self._week(label))

    def weeks(self) -> list[str]:
        return sorted(p.stem for p in (self.root / "weeks").glob("*/*.json"))

    def seen(self) -> set[str]:
        path = self.root / "seen.txt"
        if not path.exists():
            return set()
        return {
            line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
        }

    def save_seen(self, ids: set[str]) -> None:
        path = self.root / "seen.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(f"{i}\n" for i in sorted(ids)), encoding="utf-8")
