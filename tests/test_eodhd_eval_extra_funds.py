"""OD-0222: EXTRA_FUNDS may be named with --symbols; the default is unchanged. Invented data only."""

import importlib
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
ev = importlib.import_module("eodhd_eval")
EXTRA = ["VGB.AU", "IGB.AU", "AGVT.AU"]


@pytest.fixture(autouse=True)
def private_tmp(tmp_path):
    tmp_path.chmod(0o700)


def fund_requests(symbols):
    return [
        (s, k, p)
        for s in symbols
        for k, p in (
            ("eod", f"/eod/{s}?fmt=json&period=d"),
            ("div", f"/div/{s}?fmt=json"),
            ("splits", f"/splits/{s}?fmt=json"),
        )
    ]


def exchange_request(exchange):
    return (f"EXCHANGE.{exchange}", "symbols", f"/exchange-symbol-list/{exchange}?fmt=json")


def test_the_default_request_list_is_unchanged():
    expected = (
        fund_requests(list(ev.ETFS))
        + [(ev.FOREX, "eod", f"/eod/{ev.FOREX}?fmt=json&period=d")]
        + [exchange_request(e) for e in ev.EXCHANGES]
    )
    assert ev.requests_for(None) == expected
    assert not any(s in EXTRA for s, _, _ in ev.requests_for(None))


def test_the_three_extra_funds_give_nine_fund_requests_and_the_au_listing_only():
    planned = ev.requests_for(EXTRA)
    assert planned == [*fund_requests(EXTRA), exchange_request("AU")]
    assert len(planned) == 10
    assert not any("EXCHANGE.US" in s for s, _, _ in planned)
    assert not any("FOREX" in r for _, _, r in planned)


def test_a_mix_works_and_unknown_or_empty_still_stops():
    planned = ev.requests_for(["SPY.US", "VGB.AU"])
    both = fund_requests(["SPY.US", "VGB.AU"])
    assert planned == [*both, exchange_request("US"), exchange_request("AU")]
    with pytest.raises(ev.Stop):
        ev.requests_for(["VGB.AU", "XYZ.AU"])
    with pytest.raises(ev.Stop):
        ev.requests_for([])


def test_fetch_writes_ten_files_and_a_manifest_naming_the_three(tmp_path):
    def get(request):
        if request.startswith("/exchange-symbol-list/"):
            return 200, json.dumps([{"Code": s.split(".")[0], "Currency": "AUD"} for s in EXTRA]).encode()
        return 200, b"[]"

    manifest = ev.fetch(
        tmp_path, "s1", gate=ev.make_gate({}), commit="c" * 40, get=get, pause=0, symbols=EXTRA
    )
    written = sorted(p.name for p in (tmp_path / "raw" / "s1").iterdir())
    assert len(written) == 11  # ten data files plus the manifest
    assert "manifest.json" in written
    assert len(manifest["files"]) == 10
    on_disk = json.loads((tmp_path / "raw" / "s1" / "manifest.json").read_text())
    assert on_disk["symbols"] == EXTRA
    assert on_disk["stopped"] is None


def test_etfs_keeps_exactly_its_seven_keys():
    assert list(ev.ETFS) == ["SPY.US", "VTI.US", "IEF.US", "BIL.US", "VAS.AU", "IVV.AU", "BGBL.AU"]
    assert not set(EXTRA) & set(ev.ETFS)
