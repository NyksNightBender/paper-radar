from paper_radar.rank import score
from tests.fakes import KeywordEmbedder, paper

WATER = paper(
    "1",
    "Leak detection in water pipe networks",
    "Pressure sensors find water leaks in pipes.",
    "2026-11-05T00:00:00+00:00",
)
METER = paper(
    "2",
    "Smart meter consumption anomalies",
    "Energy consumption of a building from meter time series.",
    "2026-11-05T00:00:00+00:00",
)
LEAKAGE = paper(
    "3",
    "Data leakage in language model training",
    "Privacy leakage when training a language model.",
    "2026-11-05T00:00:00+00:00",
)


def test_ranking_follows_meaning() -> None:
    ranked = score([LEAKAGE, METER, WATER], KeywordEmbedder())
    assert [r["id"] for r in ranked][-1] == "3"  # "leakage" in ML is not a water leak
    by_id = {r["id"]: r for r in ranked}
    assert by_id["1"]["interest"] == "water"
    assert by_id["2"]["interest"] == "meters"
    assert set(by_id["1"]["scores"]) == {"water", "meters", "methods"}
    assert all(0 <= r["score"] <= 1 for r in ranked)


def test_empty() -> None:
    assert score([], KeywordEmbedder()) == []
