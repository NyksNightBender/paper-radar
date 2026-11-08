from paper_radar.arxiv import parse_feed
from tests.fakes import FEED


def test_parse_feed() -> None:
    papers = parse_feed(FEED)
    assert [p.id for p in papers] == ["2611.01234", "hep-th/0101001"]  # the error entry is skipped
    first = papers[0]
    assert first.version == 2
    assert (
        first.title == "Graph Neural Networks for Leak Localisation in Water Distribution Networks"
    )
    assert first.abstract == "We detect and localise leaks from pressure sensors."
    assert first.authors == ["Ayşe Yılmaz", "John Smith"]
    assert first.primary == "eess.SP" and first.categories == ["eess.SP", "cs.LG"]
    assert first.published == "2026-11-05T18:00:01+00:00"
    assert first.url == "https://arxiv.org/abs/2611.01234"
    assert first.pdf == "https://arxiv.org/pdf/2611.01234"
