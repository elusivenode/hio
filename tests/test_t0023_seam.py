"""t0023_seam on invented numbers only: each bar at and just outside it, the page parser, the target step
function, and S6 and S7 changing only what they name."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import sys
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal as D
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import e0003_aud_cash as base  # noqa: E402
import e0003_extended as ext  # noqa: E402
import eodhd_eval as ev  # noqa: E402
import t0023_common as common  # noqa: E402
import t0023_seam as t  # noqa: E402


def days(start: date, count: int) -> list[date]:
    return [start + timedelta(days=i) for i in range(count)]


def month_ends(year: int, month: int, count: int) -> list[date]:
    out = []
    for _ in range(count):
        following = date(year + month // 12, month % 12 + 1, 1)
        out.append(following - timedelta(days=1))
        year, month = following.year, following.month
    return out


def tri_from(aonia: dict[date, D], scale: D = D(2)) -> dict[date, D]:
    return {d: v * scale for d, v in ext.accrue(aonia).items()}


def flat(rate: str, start: date, count: int) -> dict[date, D]:
    return {d: D(rate) for d in days(start, count)}


# ---- the page and the step function --------------------------------------------------------------------

PAGE = """
<html><body><table>
<tr><th>Effective date</th><th>Change</th><th>Cash rate target</th></tr>
<tr><td>5&nbsp;Jan 2011</td><td>+0.25</td><td>4.75&nbsp;%</td></tr>
<tr><td>1 Jan 2010</td><td>+0.25</td><td>4.50</td></tr>
<tr><td>3 Apr 1995</td><td></td><td>4.00&ndash;4.25</td></tr>
<tr><td>Note: figures are rounded</td></tr>
</table></body></html>
"""
WINDOW = date(2007, 5, 1)


def test_page_parser_reads_rows_and_counts_the_unreadable() -> None:
    steps, unreadable = t.parse_target_page(PAGE, WINDOW)
    assert steps == {date(2011, 1, 5): D("4.75"), date(2010, 1, 1): D("4.50")}
    assert len(unreadable) == 1
    assert "4.00" in unreadable[0]


def test_page_parser_stops_on_an_unreadable_row_inside_the_window() -> None:
    page = PAGE.replace(
        "<td>1 Jan 2010</td><td>+0.25</td><td>4.50</td>", "<td>1 Jan 2010</td><td></td><td>n/a</td>"
    )
    with pytest.raises(ev.Stop):
        t.parse_target_page(page, WINDOW)
    # the same row, dated just before the window, is only counted
    page = PAGE.replace("1 Jan 2010", "30 Apr 2007").replace("<td>4.50</td>", "<td>text</td>")
    steps, unreadable = t.parse_target_page(page, WINDOW)
    assert len(unreadable) == 2
    assert list(steps) == [date(2011, 1, 5)]


def test_page_parser_stops_on_conflicts_and_empty_pages() -> None:
    twice = PAGE.replace("3 Apr 1995", "5 Jan 2011").replace("4.00&ndash;4.25", "4.50")
    with pytest.raises(ev.Stop):
        t.parse_target_page(twice, WINDOW)
    with pytest.raises(ev.Stop):
        t.parse_target_page("<table><tr><th>Effective date</th></tr></table>", WINDOW)


def test_target_applies_from_its_effective_date_until_the_next() -> None:
    steps = {date(2010, 1, 1): D("4.5"), date(2011, 1, 5): D("4.75")}
    assert t.target_on(steps, date(2009, 12, 31)) is None
    assert t.target_on(steps, date(2010, 1, 1)) == D("4.5")
    assert t.target_on(steps, date(2011, 1, 4)) == D("4.5")
    assert t.target_on(steps, date(2011, 1, 5)) == D("4.75")
    assert t.target_on(steps, date(2030, 1, 1)) == D("4.75")


# ---- M1 and M2 -----------------------------------------------------------------------------------------


def test_m1_bar_at_and_just_outside(monkeypatch: pytest.MonkeyPatch) -> None:
    for within, passes in ((95, True), (94, False)):
        monkeypatch.setattr(ext, "seam_check", lambda *_a, w=within: {"months": 100, "within_1bp": w})
        assert t.check_m1([], {}, {})["passes"] is passes


def test_m1_on_a_real_accrual_with_one_and_two_bad_month_ends() -> None:
    aonia = flat("4.5", date(2011, 1, 3), 1300)
    months = month_ends(2011, 1, 41)
    tri = tri_from({d: v for d, v in aonia.items() if d >= t.TRI_START})
    assert t.check_m1(months, aonia, tri) == {
        "performed": True,
        "months": 40,
        "within_1bp": 40,
        "passes": True,
    }
    one = {**tri, months[10]: tri[months[10]] * D("1.0002")}  # moves the two months that touch it
    assert t.check_m1(months, aonia, one)["within_1bp"] == 38
    assert t.check_m1(months, aonia, one)["passes"] is True
    two = {**one, months[20]: tri[months[20]] * D("1.0002")}
    assert t.check_m1(months, aonia, two)["within_1bp"] == 36
    assert t.check_m1(months, aonia, two)["passes"] is False


def test_m1_not_performed_without_months() -> None:
    result = t.check_m1(
        [date(2010, 1, 31)], flat("4", date(2011, 1, 4), 10), tri_from(flat("4", date(2011, 1, 4), 10))
    )
    assert result["performed"] is False
    assert result["passes"] is False


def test_m2_drift_just_inside_and_outside_the_bar() -> None:
    aonia = flat("4.5", date(2011, 1, 4), 400)
    months = month_ends(2011, 1, 12)
    tri = tri_from(aonia)
    assert t.check_m2(months, aonia, tri)["passes"] is True
    for factor, passes in ((D("1.001"), True), (D("1.00101"), False)):
        drifted = {**tri, months[-1]: tri[months[-1]] * factor}
        assert t.check_m2(months, aonia, drifted)["passes"] is passes
    assert t.check_m2([date(2010, 1, 31)], aonia, tri)["performed"] is False


# ---- R1, R2, R3 ----------------------------------------------------------------------------------------

STEPS = {date(2007, 1, 1): D("5.0")}


def history_by_year(per_year: int = 20) -> dict[date, D]:
    return {d: D("5.0") for y in t.R1_YEARS for d in days(date(y, 6, 1), per_year)}


def test_r1_bar_per_year_at_and_just_outside() -> None:
    history = history_by_year()
    day = date(2008, 6, 1)
    history[day] = D("5.05")  # exactly 5 bp: within
    history[day + timedelta(days=1)] = D("5.06")  # one outside: 19 of 20 is 95%
    result = t.check_r1(history, STEPS, date(2007, 4, 30))
    assert result["years"]["2008"] == {"days": 20, "within_5bp": 19, "passes": True}
    assert result["passes"] is True
    history[day + timedelta(days=2)] = D("4.94")  # a second outside: 90%
    result = t.check_r1(history, STEPS, date(2007, 4, 30))
    assert result["years"]["2008"]["passes"] is False
    assert result["years"]["2009"]["passes"] is True
    assert result["passes"] is False


def test_r1_starts_at_the_panels_first_month_and_ignores_2011() -> None:
    history = history_by_year()
    history[date(2007, 4, 1)] = D("9")  # before the panel's first month
    history[date(2011, 1, 4)] = D("9")  # not pre-2011
    assert t.check_r1(history, STEPS, date(2007, 4, 30))["passes"] is True


def test_r1_year_without_days_is_not_performed_and_no_target_stops() -> None:
    history = {d: v for d, v in history_by_year().items() if d.year != 2009}
    result = t.check_r1(history, STEPS, date(2007, 4, 30))
    assert result["years"]["2009"]["performed"] is False
    assert result["passes"] is False
    with pytest.raises(ev.Stop):
        t.check_r1(history_by_year(), {date(2008, 1, 1): D("5")}, date(2007, 4, 30))


def r2_inputs(bad_months: list[date]) -> tuple[list[date], dict[date, D]]:
    months = month_ends(2007, 8, 41)
    history = flat("5.0", date(2007, 8, 1), 1250)
    for month in bad_months:
        for d in days(month.replace(day=1), month.day):
            history[d] = D("5.5")
    return months, {d: v for d, v in history.items() if d < t.TRI_START}


def test_r2_bar_at_and_just_outside() -> None:
    steps = {date(2007, 1, 1): D("5.0")}
    months, history = r2_inputs([])
    assert t.check_r2(months, history, steps) == {
        "performed": True,
        "months": 40,
        "within_1bp": 40,
        "passes": True,
    }
    months, history = r2_inputs([date(2009, 3, 31), date(2009, 8, 31)])
    at = t.check_r2(months, history, steps)
    assert at["within_1bp"] == 38  # 95% exactly
    assert at["passes"] is True
    months, history = r2_inputs([date(2009, 3, 31), date(2009, 8, 31), date(2009, 11, 30)])
    outside = t.check_r2(months, history, steps)
    assert outside["within_1bp"] == 37
    assert outside["passes"] is False


def test_r2_not_performed_without_pre_2011_rates() -> None:
    assert t.check_r2(month_ends(2007, 8, 5), {date(2011, 2, 1): D(4)}, STEPS)["performed"] is False


def test_r3_every_published_day_must_equal() -> None:
    steps = {date(2010, 1, 1): D("4.5"), date(2011, 1, 5): D("4.75")}
    published = {d: t.target_on(steps, d) for d in days(date(2011, 1, 4), 5)}
    published[date(2010, 12, 1)] = D("99")  # before 2011: ignored
    assert t.check_r3(steps, published) == {"performed": True, "days": 5, "equal": 5, "passes": True}
    published[date(2011, 1, 6)] = D("4.5")
    result = t.check_r3(steps, published)
    assert (result["equal"], result["passes"]) == (4, False)
    assert t.check_r3(steps, {date(2010, 12, 1): D(1)})["performed"] is False


# ---- S6 and S7 -----------------------------------------------------------------------------------------

MONTHS = month_ends(2010, 9, 7)  # 2010-09-30 to 2011-03-31, six returns


def sensitivity_inputs() -> tuple[common.FrozenPanel, dict[date, D], dict[date, D], dict[date, D]]:
    history = flat("5.0", date(2010, 9, 1), 122)
    aonia = flat("5.0", t.TRI_START, 90)
    tri = tri_from(flat("4.0", t.TRI_START, 90))
    rng = np.random.default_rng(1)
    usd = rng.normal(0.005, 0.01, size=(6, 3))
    fx = rng.normal(0, 0.01, size=6)
    columns = [(1 + usd[:, i]) * (1 + fx) - 1 for i in range(3)]
    shell = common.FrozenPanel(MONTHS, np.column_stack([*columns, np.zeros(6)]), usd[:, 1], fx)
    cash = t.build_cash(shell, t.pre_2011(history, MONTHS[0]), tri)
    return replace(shell, returns=np.column_stack([*columns, cash])), history, aonia, tri


def test_s6_changes_only_pre_2011_cash() -> None:
    panel, history, _, tri = sensitivity_inputs()
    steps = {date(2010, 1, 1): D("4.5")}
    changed = t.s6_panel(panel, history, steps, tri)
    np.testing.assert_allclose(changed.returns[:, :3], panel.returns[:, :3], atol=1e-12)
    np.testing.assert_array_equal(changed.usd_bills, panel.usd_bills)
    np.testing.assert_array_equal(changed.s, panel.s)
    assert changed.months == panel.months
    old, new = panel.returns[:, 3], changed.returns[:, 3]
    assert np.all(np.abs(new[:3] - old[:3]) > 1e-5)
    np.testing.assert_allclose(new[4:], old[4:], atol=1e-12)  # TRI months, after the seam month
    assert np.all(new[:3] < old[:3])  # 4.5 is below 5.0


def test_s6_with_the_target_equal_to_the_rates_changes_nothing() -> None:
    panel, history, _, tri = sensitivity_inputs()
    same = t.s6_panel(panel, history, {date(2010, 1, 1): D("5.0")}, tri)
    np.testing.assert_allclose(same.returns, panel.returns, atol=1e-12)
    assert t.baseline_rebuilds(panel, history, tri) is True
    assert t.baseline_rebuilds(panel, {d: v + 1 for d, v in history.items()}, tri) is False


def test_s7_changes_only_cash_and_uses_the_overnight_rate_after_2011() -> None:
    panel, history, aonia, _ = sensitivity_inputs()
    changed = t.s7_panel(panel, history, aonia)
    np.testing.assert_allclose(changed.returns[:, :3], panel.returns[:, :3], atol=1e-12)
    np.testing.assert_array_equal(changed.usd_bills, panel.usd_bills)
    np.testing.assert_array_equal(changed.s, panel.s)
    np.testing.assert_allclose(changed.returns[:3, 3], panel.returns[:3, 3], atol=1e-15)  # before the TRI
    expected = (1 + 0.05 / 365) ** 28 - 1  # 2011-01-31 to 2011-02-28 at 5.0%, no TRI at 4.0%
    assert changed.returns[4, 3] == pytest.approx(expected, rel=1e-9)
    assert abs(panel.returns[4, 3] - expected) > 1e-5


def test_s7_ignores_f1_rates_before_2011() -> None:
    panel, history, aonia, _ = sensitivity_inputs()
    early = {**aonia, date(2010, 10, 5): D("20")}
    a, b = t.s7_panel(panel, history, aonia), t.s7_panel(panel, history, early)
    np.testing.assert_array_equal(a.returns, b.returns)


def test_sensitivity_bar_is_no_change_of_class(monkeypatch: pytest.MonkeyPatch) -> None:
    panel, *_ = sensitivity_inputs()
    frozen = {"e": {"m": {"class": "a"}}}
    monkeypatch.setattr(common, "classes_of", lambda _p: {"e": {"m": {"class": "a"}}})
    assert t.sensitivity(frozen, panel, True, "")["passes"] is True
    monkeypatch.setattr(common, "classes_of", lambda _p: {"e": {"m": {"class": "b"}}})
    result = t.sensitivity(frozen, panel, True, "")
    assert result["passes"] is False
    assert result["class_changes"] == ["e.m: a -> b"]
    skipped = t.sensitivity(frozen, panel, False, "why")
    assert skipped == {"performed": False, "why": "why", "passes": False}


# ---- the whole run -------------------------------------------------------------------------------------


def workspace(tmp_path: Path, *, break_manifest: bool = False) -> tuple[Path, Path, Path, Path, str]:
    root, e0003, history_root = tmp_path / "ws", tmp_path / "e3", tmp_path / "hist"
    for folder in (root, e0003, history_root):
        folder.mkdir(mode=0o700)
        os.chmod(folder, 0o700)
    panel, history, aonia, tri = sensitivity_inputs()
    steps_page = (
        "<table><tr><th>Effective date</th><th>Change</th><th>Cash rate target</th></tr>"
        "<tr><td>5 Jan 2011</td><td>+0.25</td><td>4.75</td></tr>"
        "<tr><td>1 Jan 2010</td><td>+0.25</td><td>4.50</td></tr>"
        "<tr><td>3 Apr 1995</td><td></td><td>4.00 to 4.25</td></tr></table>"
    )
    steps = {date(2010, 1, 1): D("4.50"), date(2011, 1, 5): D("4.75")}
    first = panel.months[0]
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["period_start", "period_end", *base.SLEEVES, "usd_bills", "fx_return"])
    for i, (a, b) in enumerate(zip(panel.months, panel.months[1:], strict=False)):
        writer.writerow([a.isoformat(), b.isoformat(), *panel.returns[i], panel.usd_bills[i], panel.s[i]])
    text = buffer.getvalue().encode()
    run_dir = root / "runs" / "r1"
    run_dir.mkdir(parents=True)
    (run_dir / "panel.csv").write_bytes(text)
    record = {"panel_id": "p" * 8, "panel_sha256": hashlib.sha256(text).hexdigest()}
    (run_dir / "run.json").write_text(json.dumps(record))
    del first
    (root / "reference" / "raw").mkdir(parents=True, mode=0o700)
    os.chmod(root / "reference", 0o700)
    os.chmod(root / "reference" / "raw", 0o700)
    os.chmod(root / "runs", 0o700)
    os.chmod(run_dir, 0o700)
    (root / "reference" / "raw" / "rba-cash-rate.html").write_text(steps_page)
    f1 = ["Title,a,b,c", "Series ID,FIRMMCRTD,FIRMMCRID,FIRMMCTRI"]
    for d in sorted(tri):
        f1.append(f"{d.strftime('%d-%b-%Y')},{t.target_on(steps, d)},{aonia[d]},{tri[d]}")
    body = ("\n".join(f1) + "\n").encode()
    (e0003 / "raw").mkdir(mode=0o700)
    (e0003 / "raw" / "rba_f1.csv").write_bytes(body)
    receipt = "0" * 64 if break_manifest else hashlib.sha256(body).hexdigest()
    (e0003 / "raw" / "manifest.json").write_text(json.dumps({"receipt_id": receipt}))
    hist_csv = "date,rate_pct\n" + "".join(f"{d.isoformat()},{v}\n" for d, v in sorted(history.items()))
    (history_root / "firmmcrid.csv").write_text(hist_csv)
    digest = hashlib.sha256(hist_csv.encode()).hexdigest()
    (history_root / "extract-manifest.json").write_text(json.dumps({"sha256": digest}))
    return root, e0003, history_root, root / "reference", record["panel_id"]


def run_all(paths: tuple[Path, Path, Path, Path, str], monkeypatch: pytest.MonkeyPatch) -> dict:
    root, e0003, history_root, reference, panel_id = paths
    monkeypatch.setattr(common, "classes_of", lambda _p: {"e": {"m": {"class": "a"}}})
    summary, _ = t.run(root, e0003, history_root, reference, gate=ev.make_gate({}), panel_id=panel_id)
    return summary


def test_run_end_to_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    summary = run_all(workspace(tmp_path), monkeypatch)
    assert summary["page"] == {"steps": 2, "unreadable": 1}
    assert summary["baseline_rebuilt"] is True
    # the fixture's TRI accrues 4.0% while FIRMMCRID says 5.0%: a failed bar is a result, not an error
    assert summary["checks"]["M1"] == {"performed": True, "months": 2, "within_1bp": 0, "passes": False}
    assert summary["checks"]["M2"]["passes"] is False
    assert summary["checks"]["R3"]["passes"] is True
    assert summary["checks"]["R1"]["years"]["2008"]["performed"] is False  # no 2008 days here
    assert summary["sensitivities"]["S6"]["performed"] is True
    assert summary["sensitivities"]["S7"]["passes"] is True
    line = t.stdout_line(summary)
    assert "R1.2008" in line["not_performed"]
    text = t.render(summary)
    for sentence in (
        "M1 and M2 test the method only",
        "R1 and R2 test consistency with the RBA's own target, not the rates' accuracy against a third party",
        "A benchmark accrual isn't an investable deposit return",
        "not performed",
    ):
        assert sentence in text


def test_run_stops_when_the_receipt_doesnt_match_its_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(ev.Stop):
        run_all(workspace(tmp_path, break_manifest=True), monkeypatch)


def test_main_exits_2_on_a_stop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setattr(ev, "code_commit", lambda: {"commit": "a" * 40, "lock_sha256": "l" * 64})
    code = t.main(["--root", str(tmp_path / "nowhere"), "--e0003", str(tmp_path), "--history", str(tmp_path)])
    assert code == 2
    assert capsys.readouterr().out == ""
