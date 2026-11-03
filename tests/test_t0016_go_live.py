"""T-0016 (OD-0143): the go-live configuration is exactly what the owner approved."""

from __future__ import annotations

from pathlib import Path

from hio.jobs.s1b1_capture import LIVE_AUTHORISATION, _default_urls
from hio.sources.datasets import APPROVED_URLS, PUBLICATIONS

REPO = Path(__file__).resolve().parent.parent

# Repeated on purpose, from docs/evidence/S1B1-go-live-package.md at 3cee431.
THE_FOUR = {
    "rba.f1": "https://www.rba.gov.au/statistics/tables/csv/f1-data.csv",
    "rba.expert_judgement": "https://www.rba.gov.au/statistics/tables/csv/f1-use-of-expert-judgement.csv",
    "nyfed.sofr": "https://markets.newyorkfed.org/api/rates/secured/sofr/last/30.json",
    "nyfed.sofr_index": "https://markets.newyorkfed.org/api/rates/secured/sofrai/last/30.json",
}


def test_the_authorisation_names_the_recorded_owner_decision():
    assert LIVE_AUTHORISATION == "OD-0143"
    assert list((REPO / "docs" / "decisions" / "owner").glob(f"{LIVE_AUTHORISATION}-*.md"))


def test_exactly_the_four_approved_urls_are_configured():
    assert dict(APPROVED_URLS) == THE_FOUR
    assert _default_urls() == THE_FOUR
    assert set(PUBLICATIONS) == set(THE_FOUR)


def test_the_approved_urls_appear_in_the_adopted_package():
    package = (REPO / "docs" / "evidence" / "S1B1-go-live-package.md").read_text()
    for url in THE_FOUR.values():
        assert f"`{url}`" in package


def test_the_five_datasets_are_served_by_the_four_publications():
    served = {d.source_id for p in PUBLICATIONS.values() for d in p.datasets}
    assert served == {
        "rba.cash_rate",
        "rba.cash_rate_tri",
        "rba.expert_judgement",
        "nyfed.sofr",
        "nyfed.sofr_index",
    }
