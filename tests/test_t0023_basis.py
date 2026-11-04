"""T-0023 step 5: X1, G1, S8 and S9, on invented data only."""

import hashlib
import importlib.util
import json
import sys
import zipfile
from datetime import date, timedelta
from decimal import Decimal as D
from itertools import pairwise
from pathlib import Path

import numpy as np
import pytest

from hio.library.vehicle_return import VehicleDay, VehiclePeriod, vehicle_series

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
_spec = importlib.util.spec_from_file_location("t0023_basis", REPO / "tools" / "t0023_basis.py")
tool = importlib.util.module_from_spec(_spec)
sys.modules["t0023_basis"] = tool
_spec.loader.exec_module(tool)

ev = tool.ev
D1, D2, D3 = date(2020, 1, 1), date(2020, 1, 2), date(2020, 1, 3)


def near(a, b, tol="1e-15"):
    assert abs(D(a) - D(b)) < D(tol), (a, b)


# X1 and the direction of both FX sources


def test_both_sources_quote_usd_per_aud_so_the_ratio_is_direct():
    assert tool.H10_QUOTE == tool.EODHD_QUOTE == "USD per AUD"
    months = [D1, D2]
    same = tool.x1_gaps([D("0.65"), D("0.66")], [D("0.65"), D("0.66")])
    inverted = tool.x1_gaps([D("0.65"), D("0.66")], [1 / D("0.65"), 1 / D("0.66")])
    assert same == [0, 0] and all(g > D("0.5") for g in inverted) and len(months) == 2


def test_x1_counts_by_band_by_hand():
    gaps = tool.x1_gaps([D(100)] * 4, [D(100), D("100.4"), D("100.9"), D("101.5")])
    assert tool.x1_counts(gaps) == {"month_ends": 4, "within_0.005": 2, "within_0.01": 3, "within_0.02": 4}


def test_a_fall_in_the_audusd_quote_gives_a_positive_s_for_an_aud_holder_of_usd():
    s = tool.fx_returns([D("0.70"), D("0.65")])
    assert abs(s[0] - (0.70 / 0.65 - 1)) < 1e-12 and s[0] > 0


def test_the_month_end_rate_is_the_latest_within_the_stale_limit_and_older_stops():
    rates = {date(2020, 1, 29): D("0.7"), date(2020, 2, 3): D("0.8")}
    assert tool.month_end_rates([date(2020, 1, 31)], rates) == [D("0.7")]
    with pytest.raises(ev.Stop, match="days old"):
        tool.month_end_rates([date(2020, 2, 29)], rates)
    with pytest.raises(ev.Stop, match=r"no H\.10 rate"):
        tool.month_end_rates([date(2020, 1, 1)], rates)


def test_s9_takes_the_next_published_date_after_the_one_chosen():
    rates = {date(2020, 1, 30): D("0.7"), date(2020, 2, 3): D("0.8"), date(2020, 2, 4): D("0.9")}
    assert tool.next_published_rates([date(2020, 1, 31), date(2020, 1, 30)], rates) == [D("0.8"), D("0.8")]


def test_s9_stops_when_nothing_is_published_after_the_chosen_date_or_the_choice_is_stale():
    rates = {date(2020, 1, 30): D("0.7")}
    with pytest.raises(ev.Stop, match=r"no H\.10 date after"):
        tool.next_published_rates([date(2020, 1, 31)], rates)
    with pytest.raises(ev.Stop, match="days old"):
        tool.next_published_rates([date(2020, 3, 1)], {**rates, date(2020, 4, 1): D("0.8")})


def test_eodhd_rates_refuse_conflicts_and_impossible_values():
    with pytest.raises(ev.Stop, match="conflicting"):
        tool.eodhd_rates(
            [{"date": "2020-01-01", "close": D("0.7")}, {"date": "2020-01-01", "close": D("0.8")}]
        )
    with pytest.raises(ev.Stop, match="impossible"):
        tool.eodhd_rates([{"date": "2020-01-01", "close": D(0)}])


# G1: payment-date reinvestment, by hand


def closes(*values, start=D1):
    return [(start + timedelta(days=i), D(v)) for i, v in enumerate(values)]


def test_three_days_by_hand_the_cash_waits_earns_nothing_and_buys_at_the_payment_close():
    # close 100, ex-date day 2 at 98 with 2 paid on day 3, then 99. One unit's worth: 100 of wealth.
    periods, counts = tool.payment_date_periods(closes(100, 98, 99), [tool.Distribution(D2, D3, D(2))])
    assert counts == {}
    ex, pay = periods
    assert (ex.start, ex.end, pay.start, pay.end) == (D1, D2, D2, D3)
    near(ex.total_return, "-0.02")  # the drop stays; no income yet
    assert ex.income_return == 0
    # 1 unit held at 100 earns 2 cash on 0.01 units -> 0.02; bought at 99 on day 3.
    # wealth day 2 = 0.98, day 3 = 0.01 * 99 + 0.02 = 1.01
    near(pay.total_return, D("1.01") / D("0.98") - 1)
    near(pay.income_return, D(2) / D(98))
    near(pay.price_return, D(99) / D(98) - 1)
    near((1 + ex.total_return) * (1 + pay.total_return), "1.01")


def test_the_ex_date_convention_differs_by_the_price_move_during_the_wait():
    bars = [VehicleDay(D1, D(100)), VehicleDay(D2, D(98), D(2)), VehicleDay(D3, D(99))]
    chained = np.prod([float(1 + p.total_return) for p in vehicle_series(bars)])
    periods, _ = tool.payment_date_periods(closes(100, 98, 99), [tool.Distribution(D2, D3, D(2))])
    mine = np.prod([float(1 + p.total_return) for p in periods])
    assert abs(chained - 1.0102040816) < 1e-9 and abs(mine - 1.01) < 1e-12


def test_a_payment_on_a_non_trading_day_buys_at_the_next_close():
    data = [(D1, D(100)), (D2, D(98)), (date(2020, 1, 6), D(99))]  # 3rd to 5th aren't trading days
    periods, counts = tool.payment_date_periods(data, [tool.Distribution(D2, date(2020, 1, 4), D(2))])
    assert counts == {}
    near(periods[1].income_return, D(2) / D(98))


def test_no_payment_date_stays_on_the_ex_date_and_is_counted():
    records = [tool.Distribution(D2, None, D(2))]
    periods, counts = tool.payment_date_periods(closes(100, 98, 99), records)
    expected = vehicle_series([VehicleDay(D1, D(100)), VehicleDay(D2, D(98), D(2)), VehicleDay(D3, D(99))])
    assert counts == {"no_payment_date_left_on_ex_date": 1}
    for mine, theirs in zip(periods, expected, strict=True):
        near(mine.total_return, theirs.total_return)


def test_payment_on_the_ex_date_equals_the_ex_date_convention_and_before_it_is_left_there():
    expected = vehicle_series([VehicleDay(D1, D(100)), VehicleDay(D2, D(98), D(2)), VehicleDay(D3, D(99))])
    for paid, key in ((D2, None), (D1, "payment_before_ex_left_on_ex_date")):
        periods, counts = tool.payment_date_periods(closes(100, 98, 99), [tool.Distribution(D2, paid, D(2))])
        assert counts == ({key: 1} if key else {})
        for mine, theirs in zip(periods, expected, strict=True):
            near(mine.total_return, theirs.total_return)


def test_a_payment_after_the_last_close_is_counted_and_never_received():
    periods, counts = tool.payment_date_periods(
        closes(100, 98, 99), [tool.Distribution(D2, date(2020, 2, 1), D(2))]
    )
    assert counts == {"payment_after_the_last_close": 1}
    near((1 + periods[0].total_return) * (1 + periods[1].total_return), D("0.99"))


def test_records_outside_the_closes_are_counted_and_left_out():
    records = [tool.Distribution(D1, D2, D(2)), tool.Distribution(date(2020, 2, 1), None, D(2))]
    periods, counts = tool.payment_date_periods(closes(100, 98, 99), records)
    assert counts == {"on_or_before_the_first_close": 1, "after_the_last_close": 1}
    near((1 + periods[0].total_return) * (1 + periods[1].total_return), D("0.99"))


def test_an_ex_date_on_a_non_trading_day_moves_to_the_next_trading_day():
    data = [(D1, D(100)), (D2, D(98)), (date(2020, 1, 6), D(99))]
    periods, _ = tool.payment_date_periods(data, [tool.Distribution(date(2020, 1, 4), None, D(2))])
    near(periods[1].income_return, D(2) / D(98))
    assert periods[0].income_return == 0


def test_cash_from_two_records_counts_units_at_each_ex_eve():
    # Day 2 ex of 1 (paid day 3), day 3 ex of 1 (paid day 4). The second one's cash is 1 per unit held at the
    # close before its ex-date (0.01 units), not per unit after day 3's purchase.
    data = closes(100, 100, 100, 100)
    records = [tool.Distribution(D2, D3, D(1)), tool.Distribution(D3, date(2020, 1, 4), D(1))]
    periods, _ = tool.payment_date_periods(data, records)
    # day 2: no income. day 3: cash 0.01 on wealth 1 -> 1%, units 0.01 -> 0.0101. day 4: cash 0.01 on 1.01.
    near(periods[0].total_return, "0")
    near(periods[1].total_return, "0.01")
    near(periods[2].total_return, D(1) / D(101))


# G1: gaps and the preregistered verdict


def row(symbol, ex, pay):
    return {"symbol": symbol, "gap_ex": ex, "gap_pay": pay}


def rows(spy=((0.4, 0.2),), ief=((0.0, 0.1),), bil=((0.0, -0.1),)):
    return (
        [row("SPY.US", *g) for g in spy] + [row("IEF.US", *g) for g in ief] + [row("BIL.US", *g) for g in bil]
    )


def test_supported_needs_every_spy_gap_to_halve_and_bond_gaps_within_a_tenth():
    assert tool.g1_verdict(rows()) == "supported"  # exactly half, exactly 0.10
    assert tool.g1_verdict(rows(spy=((0.4, 0.2), (-0.4, 0.21)))) == "unexplained"
    assert tool.g1_verdict(rows(spy=((0.4, -0.2), (0.4, 0.1)))) == "supported"
    assert tool.g1_verdict(rows(ief=((0.0, 0.11),))) == "unexplained"
    assert tool.g1_verdict(rows(bil=((0.0, -0.11),))) == "unexplained"


def test_a_gap_that_grows_in_the_other_direction_is_not_halved():
    assert tool.g1_verdict(rows(spy=((0.2, -0.3),))) == "unexplained"


def test_a_missing_fund_or_row_out_of_range_is_not_performed_never_a_verdict():
    assert tool.g1_verdict(rows(bil=())).startswith("not performed: no issuer rows for BIL.US")
    assert tool.g1_verdict(rows(spy=((0.4, None),))).startswith("not performed")


def test_the_bars_are_the_preregistered_constants():
    assert tool.SPY_FACTOR == 0.5 and tool.BOND_TOLERANCE_PCT == 0.10


def test_each_gap_is_reported_under_both_conventions_by_hand():
    ex = [VehiclePeriod(D1, D2, D(0), D(0), D("0.10"))]
    pay = [VehiclePeriod(D1, D2, D(0), D(0), D("0.05"))]
    check = tool.ic.Check("SPY.US", "annualised", D1, D2, 1, 8.0)
    other = tool.ic.Check("VTI.US", "annualised", D1, D2, 1, 8.0)
    out = tool.compare_gaps([check, other], {"SPY.US": ex}, {"SPY.US": pay})
    assert len(out) == 1
    assert abs(out[0]["gap_ex"] - 2.0) < 1e-9 and abs(out[0]["gap_pay"] + 3.0) < 1e-9


def test_a_split_stops_g1_for_that_fund_and_says_so():
    data = {s: ([], []) for s in tool.FUNDS} | {"BIL.US": ([], [{"date": "2020-01-02", "split": "2/1"}])}
    out = tool.g1([], {s: [] for s in tool.FUNDS}, data)
    assert out["verdict"].startswith("not performed: BIL.US has split records")


def test_records_without_an_unadjusted_value_are_counted_and_left_out():
    records, missing = tool.fund_records(
        [
            {"date": "2020-01-02", "paymentDate": "2020-01-06", "unadjustedValue": D("1.5")},
            {"date": "2020-01-03", "paymentDate": None, "unadjustedValue": D("1")},
            {"date": "2020-01-04", "unadjustedValue": None},
        ]
    )
    assert missing == 1
    assert records == [
        tool.Distribution(D2, date(2020, 1, 6), D("1.5")),
        tool.Distribution(D3, None, D(1)),
    ]


# The whole run, in a private workspace of invented files

MONTHS = [date(2019, 12, 31), date(2020, 1, 31), date(2020, 2, 29), date(2020, 3, 31)]
H10_ON = [0.70, 0.69, 0.70, 0.71]
H10_NEXT = [0.69, 0.70, 0.69, 0.70]
EODHD_ON = [0.70, 0.70, 0.70, 0.70]


def write(path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def private(path):
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.chmod(0o700)
    return path


def build_workspace(tmp_path):
    root, e0002, h10 = (private(tmp_path / n) for n in ("t0023", "e0002", "h10"))
    for part in ("raw", "reference", "reports", "runs"):
        private(e0002 / part)
    s = [float(a / b - 1) for a, b in pairwise(map(D.from_float, H10_ON))]
    header = "period_start,period_end,equity,bills,treasury,cash,usd_bills,fx_return\n"
    body = "".join(
        f"{a},{b},0.01,0.0,0.01,0.001,0.001,{x!r}\n" for (a, b), x in zip(pairwise(MONTHS), s, strict=True)
    )
    run_dir = private(root / "runs" / "20201231T000000Z-abcdef12")
    panel = (header + body).encode()
    write(run_dir / "panel.csv", panel)
    record = {"panel_id": "invented", "panel_sha256": hashlib.sha256(panel).hexdigest()}
    write(run_dir / "run.json", json.dumps(record).encode())

    obs = "".join(
        f'<k:Obs TIME_PERIOD="{d}" OBS_VALUE="{v}"/>'
        for m, a, b in zip(MONTHS, H10_ON, H10_NEXT, strict=True)
        for d, v in ((m, a), (m + timedelta(days=1), b))
    )
    xml = f'<m xmlns:k="urn:k"><k:Series SERIES_NAME="{tool.aud_tool.H10_SERIES}">{obs}</k:Series></m>'
    zip_path = h10 / "FRB_h10_xml.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("H10_data.xml", xml)
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    write(h10 / "manifest.json", json.dumps({"sha256": digest}).encode())

    files = []

    def put(symbol, kind, rows):
        path = f"raw/s2/{symbol}.{kind}.json"
        sha = write(e0002 / path, json.dumps(rows).encode())
        files.append({"path": path, "sha256": sha, "symbol": symbol, "kind": kind})

    put(ev.FOREX, "eod", [{"date": m.isoformat(), "close": v} for m, v in zip(MONTHS, EODHD_ON, strict=True)])
    eod = [{"date": d.isoformat(), "close": float(c)} for d, c in closes(100, 98, 99, 99, 99)]
    for symbol in tool.FUNDS:
        put(symbol, "eod", eod)
        put(
            symbol,
            "div",
            [{"date": "2020-01-02", "paymentDate": "2020-01-04", "unadjustedValue": 2.0, "currency": "USD"}],
        )
        put(symbol, "splits", [])
    write(e0002 / "raw" / "s2" / "manifest.json", json.dumps({"stopped": None, "files": files}).encode())
    checks = "symbol,kind,start,end,years,percent\n" + "".join(
        f"{s},annualised,2020-01-01,2020-01-05,1,1.0\n" for s in tool.FUNDS
    )
    write(e0002 / "reference" / tool.ic.REFERENCE, checks.encode())
    return root, e0002, h10


class Gate:
    def __init__(self):
        self.asked = []

    def authorise(self, operation, sources):
        self.asked.append((operation.name, tuple(sources)))


def classify(panel):
    return {"effect": {"metric": {"class": "positive" if panel.s[0] > 0 else "zero"}}}


def test_a_run_reports_counts_and_classes_and_writes_values_only_to_the_report(tmp_path):
    root, e0002, h10 = build_workspace(tmp_path)
    gate = Gate()
    out = tool.run(
        root, e0002, h10, root, gate=gate, commit="abcdef12" * 5, panel_id="invented", classify=classify
    )
    assert {s for _, (s,) in gate.asked} == {tool.aud_tool.H10_SOURCE, ev.SOURCE_ID}
    assert out["months"] == 3 and out["panel_months_with_s_unlike_h10"] == 0
    assert out["X1"]["month_ends"] == 4 and out["X1"]["within_0.02"] == 4
    assert out["X1"]["within_0.005"] == 2  # the two month ends at 0.70 agree; 0.69 and 0.71 are 1.4% off
    assert out["X1"]["within_0.01"] == 2
    changes = ["effect.metric: positive -> zero"]
    assert out["S8"] == {"performed": True, "passes": False, "class_changes": changes}
    assert out["S9"]["passes"] is False  # the first month's next-day rate falls, so s turns negative
    assert out["G1"]["verdict"] in {"supported", "unexplained"}
    assert out["G1"]["issuer_rows"] == {"SPY.US": 1, "IEF.US": 1, "BIL.US": 1}
    (folder,) = (root / "corroboration" / "t0023_basis").iterdir()
    report = (folder / "report.md").read_text()
    assert "Payment-date %" in report and "X1" in report
    assert json.loads((folder / "summary.json").read_text()) == json.loads(json.dumps(out))
    assert "gap" not in json.dumps(out).lower() and "0.69" not in json.dumps(out)


def test_a_sensitivity_that_changes_no_class_passes(tmp_path):
    root, e0002, h10 = build_workspace(tmp_path)
    out = tool.run(
        root,
        e0002,
        h10,
        root,
        gate=Gate(),
        commit="a" * 40,
        panel_id="invented",
        classify=lambda _: {"e": {"m": {"class": "same"}}},
    )
    assert out["S8"]["passes"] is True and out["S9"]["class_changes"] == []


def test_a_tampered_h10_archive_stops(tmp_path):
    root, e0002, h10 = build_workspace(tmp_path)
    (h10 / "manifest.json").write_text(json.dumps({"sha256": "0" * 64}))
    with pytest.raises(ev.Stop, match="doesn't match its manifest"):
        tool.run(root, e0002, h10, root, gate=Gate(), commit="a" * 40, panel_id="invented", classify=classify)


def test_main_exits_2_on_a_stop_and_prints_nothing_to_stdout(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(tool.ev, "code_commit", lambda: {"commit": "a" * 40})
    argv = ["--root", str(tmp_path / "absent"), "--e0002", str(tmp_path), "--h10", str(tmp_path)]
    assert tool.main(argv) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and "stopped: Stop" in captured.err
