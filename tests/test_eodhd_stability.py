"""OD-0194: the EODHD stability tool and the fetch --symbols filter, on invented snapshots only."""

import copy
import importlib
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
ev = importlib.import_module("eodhd_eval")
st = importlib.import_module("eodhd_stability")
SYMBOLS = ["SPY.US", "IEF.US", "BIL.US"]


@pytest.fixture(autouse=True)
def private_tmp(tmp_path):
    tmp_path.chmod(0o700)


def days_from(start, count):
    out, day = [], start
    while len(out) < count:
        if day.weekday() < 5:
            out.append(day)
        day += timedelta(days=1)
    return out


DAYS = days_from(date(2026, 1, 5), 60)


def base_data():
    eod = [
        {"date": d.isoformat(), "close": 100 + 0.1 * i, "adjusted_close": 100 + 0.1 * i}
        for i, d in enumerate(DAYS)
    ]
    div = [
        {
            "date": DAYS[20].isoformat(),
            "unadjustedValue": 0.5,
            "currency": "USD",
            "paymentDate": DAYS[25].isoformat(),
        },
        {
            "date": DAYS[40].isoformat(),
            "unadjustedValue": 0.6,
            "currency": "USD",
            "paymentDate": DAYS[45].isoformat(),
        },
    ]
    splits = [{"date": DAYS[10].isoformat(), "split": "2/1"}]
    return {"eod": eod, "div": div, "splits": splits}


def take(root, name, data, symbols=SYMBOLS):
    """A snapshot in eodhd_eval's own layout, through its own fetch."""

    def get(request):
        path = request.split("?")[0].split("/")
        kind, symbol = path[1], path[2]
        if kind == "exchange-symbol-list":
            return 200, json.dumps([{"Code": s.split(".")[0], "Currency": "USD"} for s in symbols]).encode()
        return 200, json.dumps(data[symbol][kind]).encode()

    ev.fetch(root, name, gate=ev.make_gate({}), commit="c" * 40, get=get, pause=0, symbols=symbols)


def world(tmp_path, change=None):
    first = {s: base_data() for s in SYMBOLS}
    second = copy.deepcopy(first)
    if change:
        change(second)
    take(tmp_path, "s2", first)
    take(tmp_path, "s3", second)
    return tmp_path


def spy(results):
    return results["SPY.US"]


# --- counts


def test_identical_snapshots_are_stable_with_zero_impact(tmp_path):
    results = st.compare(world(tmp_path), "s2", "s3", SYMBOLS)
    for r in results.values():
        assert all(v == 0 for part in ("closes", "distributions", "splits") for v in r[part].values())
        assert r["missing_weekdays"] == {"first": 0, "second": 0}
        assert r["new_after"] == 0
        assert r["return_impact"] == {"compounded_difference": "0", "largest_period_difference": "0"}
    assert st.reading(results) == "stable"


def test_a_changed_close_has_a_nonzero_impact(tmp_path):
    def change(d):
        d["SPY.US"]["eod"][-1]["close"] = (
            120.0  # (a middle close would cancel in the compounded price return)
        )

    results = st.compare(world(tmp_path, change), "s2", "s3", SYMBOLS)
    r = spy(results)
    assert r["closes"] == {"changed": 1, "removed": 0, "added_inside": 0}
    assert float(r["return_impact"]["largest_period_difference"]) > 0.1
    assert float(r["return_impact"]["compounded_difference"]) != 0
    assert results["IEF.US"]["return_impact"]["compounded_difference"] == "0"
    assert st.reading(results) == "revisions not explained"


def test_removed_and_added_inside_closes(tmp_path):
    def change(d):
        rows = d["SPY.US"]["eod"]
        del rows[30]  # removed from the second
        d["SPY.US"]["eod"] = rows

    root = world(tmp_path, change)
    r = spy(st.compare(root, "s2", "s3", SYMBOLS))
    assert r["closes"] == {"changed": 0, "removed": 1, "added_inside": 0}
    assert r["missing_weekdays"] == {"first": 0, "second": 1}
    # reversed: the removal is an addition
    r = spy(st.compare(root, "s3", "s2", SYMBOLS))
    assert r["closes"] == {"changed": 0, "removed": 0, "added_inside": 1}
    assert r["missing_weekdays"] == {"first": 1, "second": 0}


def test_dates_after_the_first_snapshot_are_new_not_compared(tmp_path):
    def change(d):
        for symbol in SYMBOLS:
            d[symbol]["eod"].extend(
                [
                    {"date": x.isoformat(), "close": 110.0, "adjusted_close": 110.0}
                    for x in days_from(DAYS[-1] + timedelta(1), 3)
                ]
            )

    r = spy(st.compare(world(tmp_path, change), "s2", "s3", SYMBOLS))
    assert r["new_after"] == 3
    assert r["closes"] == {"changed": 0, "removed": 0, "added_inside": 0}
    assert r["return_impact"]["compounded_difference"] == "0"  # new data is outside the common span


def test_distribution_changed_removed_added_and_payment_date(tmp_path):
    def change(d):
        divs = d["SPY.US"]["div"]
        divs[0]["unadjustedValue"] = 0.55  # amount changed
        divs[1]["paymentDate"] = DAYS[50].isoformat()  # payment date moved
        divs.append(
            {"date": DAYS[50].isoformat(), "unadjustedValue": 0.2, "currency": "USD", "paymentDate": None}
        )
        d["IEF.US"]["div"].pop()  # removed

    results = st.compare(world(tmp_path, change), "s2", "s3", SYMBOLS)
    assert spy(results)["distributions"] == {
        "changed": 1,
        "removed": 0,
        "added": 1,
        "payment_date_changed": 1,
    }
    assert results["IEF.US"]["distributions"] == {
        "changed": 0,
        "removed": 1,
        "added": 0,
        "payment_date_changed": 0,
    }


def test_splits_changed_removed_added(tmp_path):
    def change(d):
        d["SPY.US"]["splits"][0]["split"] = "3/1"
        d["IEF.US"]["splits"].clear()
        d["BIL.US"]["splits"].append({"date": DAYS[30].isoformat(), "split": "2/1"})

    results = st.compare(world(tmp_path, change), "s2", "s3", SYMBOLS)
    assert spy(results)["splits"] == {"changed": 1, "removed": 0, "added": 0}
    assert results["IEF.US"]["splits"] == {"changed": 0, "removed": 1, "added": 0}
    assert results["BIL.US"]["splits"] == {"changed": 0, "removed": 0, "added": 1}


# --- the reading


def zero():
    return {
        "closes": {"changed": 0, "removed": 0, "added_inside": 0},
        "distributions": {"changed": 0, "removed": 0, "added": 0, "payment_date_changed": 0},
        "splits": {"changed": 0, "removed": 0, "added": 0},
        "return_impact": {"compounded_difference": "0", "largest_period_difference": "0"},
    }


def test_the_reading_has_three_outcomes():
    assert st.reading({"A": zero()}) == "stable"
    small = zero()
    small["splits"]["added"] = 1
    small["return_impact"]["compounded_difference"] = "-0.00009"
    assert st.reading({"A": zero(), "B": small}) == "changes found"
    big = copy.deepcopy(small)
    big["return_impact"]["compounded_difference"] = "-0.0001"
    assert st.reading({"A": big}) == "revisions not explained"


# --- main


def test_main_writes_private_reports_and_prints_no_values(tmp_path, capsys):
    def change(d):
        d["SPY.US"]["eod"][-1]["close"] = 123.456789

    root = world(tmp_path, change)
    assert st.main(["--root", str(root), "--first", "s2", "--second", "s3"]) == 0
    printed = capsys.readouterr().out
    assert "123.456789" not in printed
    assert "revisions not explained" in printed
    (out,) = (root / "reports").glob("stability-*")
    assert json.loads((out / "stability.json").read_text())["reading"] == "revisions not explained"
    lines = (out / "changes.csv").read_text().splitlines()
    assert lines[0] == "symbol,kind,date,first,second"
    assert any(line.startswith("SPY.US,close_changed,") and "123.456789" in line for line in lines)
    assert [p for p in out.iterdir() if p.stat().st_mode & 0o077] == []


def test_main_exits_2_on_stop(tmp_path, capsys):
    assert st.main(["--root", str(tmp_path), "--first", "s2", "--second", "s3", "--symbols", "XYZ.US"]) == 2
    assert capsys.readouterr().err.startswith("stopped:")


# --- the fetch filter

DEFAULT_REQUESTS = ev.requests_for()


def test_the_default_request_list_is_unchanged():
    assert ev.requests_for(None) == DEFAULT_REQUESTS
    assert [(s, k) for s, k, _ in DEFAULT_REQUESTS[:3]] == [("SPY.US", k) for k in ("eod", "div", "splits")]
    assert len(DEFAULT_REQUESTS) == 3 * 7 + 1 + 2
    assert DEFAULT_REQUESTS[-3] == (ev.FOREX, "eod", f"/eod/{ev.FOREX}?fmt=json&period=d")
    assert [r[0] for r in DEFAULT_REQUESTS[-2:]] == ["EXCHANGE.US", "EXCHANGE.AU"]


def test_the_filter_lists_ten_requests_for_three_us_funds():
    planned = ev.requests_for(SYMBOLS)
    assert len(planned) == 10
    assert [(s, k) for s, k, _ in planned[:-1]] == [(s, k) for s in SYMBOLS for k in ("eod", "div", "splits")]
    assert planned[-1] == ("EXCHANGE.US", "symbols", "/exchange-symbol-list/US?fmt=json")
    assert not any("FOREX" in r for _, _, r in planned)
    assert not any("AU" in s for s, _, _ in planned)


def test_the_filter_refuses_an_unknown_fund():
    with pytest.raises(ev.Stop):
        ev.requests_for(["SPY.US", "NOPE.US"])


def test_the_manifest_records_the_symbols_only_when_filtered(tmp_path):
    root = world(tmp_path)
    manifest = json.loads((root / "raw" / "s2" / "manifest.json").read_text())
    assert manifest["symbols"] == SYMBOLS
    assert len(manifest["files"]) == 10
    other = tmp_path / "other"
    other.mkdir(mode=0o700)
    full = ev.fetch(other, "s1", gate=ev.make_gate({}), commit="c" * 40, get=lambda _r: (200, b"[]"), pause=0)
    assert "symbols" not in full
