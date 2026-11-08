"""What the radar looks for, and where."""

from __future__ import annotations

from dataclasses import dataclass

REPO_URL = "https://github.com/NyksNightBender/paper-radar"
SITE_URL = "https://nyksnightbender.github.io/paper-radar/"
ARXIV_API = "https://export.arxiv.org/api/query"
USER_AGENT = f"paper-radar/1.0 (+{REPO_URL})"
MODEL = "BAAI/bge-small-en-v1.5"

# A broad keyword net over the categories where anomaly-detection work appears. The embedding
# model then decides what is actually close to the research topic.
QUERY = (
    "(abs:anomaly OR abs:anomalies OR abs:anomalous OR abs:outlier OR abs:outliers OR abs:leak "
    "OR abs:leakage OR abs:%22fault detection%22 OR abs:%22change point%22 "
    "OR abs:%22novelty detection%22) AND (cat:cs.LG OR cat:stat.ML OR cat:cs.AI OR cat:eess.SP "
    "OR cat:eess.SY OR cat:cs.CE OR cat:cs.DB OR cat:stat.AP OR cat:physics.data-an)"
)


@dataclass(frozen=True)
class Interest:
    key: str
    name: str
    text: str


# The research topic, split into the three directions it touches.
INTERESTS = (
    Interest(
        "water",
        "Water networks",
        "Leak and burst detection in water distribution networks from pressure and flow "
        "sensors; anomaly detection for urban water systems and water utilities.",
    ),
    Interest(
        "meters",
        "Meters and consumption",
        "Detecting abnormal water or energy consumption in buildings from smart meter time "
        "series; consumption monitoring and early warning.",
    ),
    Interest(
        "methods",
        "Time-series anomaly detection",
        "Unsupervised anomaly detection for univariate and multivariate time series: isolation "
        "forest, local outlier factor, robust statistical thresholds, benchmarks and evaluation "
        "with precision, recall and detection delay.",
    ),
)


@dataclass(frozen=True)
class Settings:
    max_results: int = 200  # newest matching papers fetched per run
    shown: int = 10  # papers highlighted per digest
    week_shown: int = 10
    backfill_days: int = 7  # on the very first run, digests for the past week
