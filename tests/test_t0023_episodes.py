"""T-0023 step 6: the episodes, robustness and the decision rule, on invented numbers only."""

import importlib.util
import json
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
_spec = importlib.util.spec_from_file_location("t0023_episodes", REPO / "tools" / "t0023_episodes.py")
tool = importlib.util.module_from_spec(_spec)
sys.modules["t0023_episodes"] = tool
_spec.loader.exec_module(tool)

ev = tool.ev
common = tool.common
IDS = tool.SENSITIVITY_IDS


def month_ends(first, count):
    out, year, month = [first], first.year, first.month
    for _ in range(count):
        month += 1
        if month == 13:
            year, month = year + 1, 1
        nxt = date(year + (month == 12), 1 if month == 12 else month + 1, 1)
        out.append(date.fromordinal(nxt.toordinal() - 1))
    return out


def make_panel(equity=0.01, bills=0.002, treasury=0.004, cash=0.003, s=0.0, shocks=None):
    """Months from 2007-12-31 to 2022-12-31. Sleeves in AUD; bills' USD return is `bills` (s=0 by default)."""
    months = month_ends(date(2007, 12, 31), 180)
    n = len(months) - 1
    returns = np.tile([equity, bills, treasury, cash], (n, 1)).astype(np.float64)
    for (i, column), value in (shocks or {}).items():
        returns[i, column] = value
    s_col = np.full(n, s)
    return common.FrozenPanel(months, returns, (1 + returns[:, 1]) / (1 + s_col) - 1, s_col)


def every(value=0.05):
    return {sid: value for sid in IDS}


# the calendar helper itself


def test_month_ends_are_month_ends():
    months = month_ends(date(2007, 12, 31), 180)
    assert (
        months[1] == date(2008, 1, 31) and months[2] == date(2008, 2, 29) and months[-1] == date(2022, 12, 31)
    )
    assert date(2008, 12, 31) in months and date(2020, 3, 31) in months


# the preregistration's constants


def test_the_episodes_and_bars_are_the_preregistered_ones():
    declared = {
        "2008": ((date(2007, 12, 31), date(2008, 12, 31)), 12),
        "q1_2020": ((date(2019, 12, 31), date(2020, 3, 31)), 3),
        "2022": ((date(2021, 12, 31), date(2022, 12, 31)), 12),
    }
    assert declared == tool.EPISODES
    assert tool.SIZE_BAR == 0.02 and IDS == ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9")


# episode_measures, by hand


def test_episode_measures_on_constant_returns():
    result = tool.episode_measures(make_panel(), *tool.EPISODES["2008"])
    aud_cash = 0.6 * 0.01 + 0.4 * 0.003
    usd_bills = 0.6 * 0.01 + 0.4 * 0.002
    treasury = 0.6 * 0.01 + 0.4 * 0.004
    allocations = result["allocations"]
    assert allocations["aud_cash"]["compounded_return"] == pytest.approx((1 + aud_cash) ** 12 - 1)
    assert allocations["usd_bills"]["compounded_return"] == pytest.approx((1 + usd_bills) ** 12 - 1)
    assert allocations["us_treasury"]["compounded_return"] == pytest.approx((1 + treasury) ** 12 - 1)
    assert allocations["aud_cash"]["max_drawdown"] == 0.0
    effects = result["effects"]
    assert effects["cash_rate_and_currency"]["compounded_return"] == pytest.approx(
        (1 + usd_bills) ** 12 - (1 + aud_cash) ** 12
    )
    assert effects["treasury_duration"]["compounded_return"] == pytest.approx(
        (1 + treasury) ** 12 - (1 + usd_bills) ** 12
    )
    assert effects["total"]["compounded_return"] == pytest.approx((1 + treasury) ** 12 - (1 + aud_cash) ** 12)
    assert result["months"] == 12 and result["start"] == "2007-12-31" and result["end"] == "2008-12-31"
    assert result["sleeves"]["equity"]["aud"] == pytest.approx(1.01**12 - 1)
    assert result["sleeves"]["cash"] == {"aud": pytest.approx(1.003**12 - 1)}
    assert result["fx_return"] == 0.0


def test_episode_measures_drawdown_and_fx_split_by_hand():
    # Month 2 of 2008 (index 2) has equity at -10% in every allocation that holds it.
    panel = make_panel(equity=0.0, bills=0.0, treasury=0.0, cash=0.0, shocks={(2, 0): -0.10})
    result = tool.episode_measures(panel, *tool.EPISODES["2008"])
    for name in ("aud_cash", "usd_bills", "us_treasury"):
        assert result["allocations"][name]["max_drawdown"] == pytest.approx(0.06)
        assert result["allocations"][name]["compounded_return"] == pytest.approx(-0.06)
    assert result["effects"]["total"]["max_drawdown"] == pytest.approx(0.0)


def test_the_fx_return_and_the_split_of_bills_against_cash():
    panel = make_panel(bills=0.0, cash=0.0, s=0.01)
    # make_panel's bills column is AUD with s; recover USD bills 0 so AUD bills = 0.01 a month.
    panel = replace(panel, returns=panel.returns.copy())
    panel.returns[:, 1] = 0.01
    panel = replace(panel, usd_bills=np.zeros(180))
    result = tool.episode_measures(panel, *tool.EPISODES["q1_2020"])
    assert result["fx_return"] == pytest.approx(1.01**3 - 1)
    split = result["bills_against_cash"]
    assert split["rate_gap"] == pytest.approx(0.0)
    assert split["currency"] == pytest.approx(1.01**3 - 1)
    assert split["cross"] == pytest.approx(0.0)
    assert result["sleeves"]["bills"] == {"aud": pytest.approx(1.01**3 - 1), "usd": pytest.approx(0.0)}


def test_a_missing_month_stops():
    panel = make_panel()
    # Drop the month end 2008-06-30 and its return: the window then holds eleven months.
    index = panel.months.index(date(2008, 6, 30))
    months = [d for i, d in enumerate(panel.months) if i != index]
    keep = [i for i in range(panel.returns.shape[0]) if i != index]
    short = common.FrozenPanel(months, panel.returns[keep], panel.usd_bills[keep], panel.s[keep])
    with pytest.raises(ev.Stop, match="holds"):
        tool.episode_measures(short, *tool.EPISODES["2008"])


def test_a_panel_that_doesnt_reach_the_window_stops():
    panel = make_panel()
    keep = [i for i in range(panel.returns.shape[0]) if panel.months[i + 1] <= date(2022, 9, 30)]
    short = common.FrozenPanel(
        panel.months[: len(keep) + 1], panel.returns[keep], panel.usd_bills[keep], panel.s[keep]
    )
    with pytest.raises(ev.Stop, match="holds"):
        tool.episode_measures(short, *tool.EPISODES["2022"])


# robust


def test_robust_at_exactly_two_points():
    assert tool.robust(0.02, every())["robust"] is True
    assert tool.robust(-0.02, every(-0.05))["robust"] is True
    assert tool.robust(0.07 - 0.05, every())["robust"] is True  # a float difference that lands on 0.02


def test_not_robust_just_under_two_points():
    result = tool.robust(0.019999, every())
    assert result["robust"] is False and result["at_least_2_points"] is False and result["sign"] == 1


def test_a_sign_flip_under_one_sensitivity_stops_it_being_robust():
    under = every() | {"S6": -0.01}
    result = tool.robust(0.05, under)
    assert result["robust"] is False and result["changed_sign"] == ["S6"] and result["not_performed"] == []


def test_a_zero_under_a_sensitivity_counts_as_a_changed_sign():
    result = tool.robust(0.05, every() | {"S3": 0.0})
    assert result["robust"] is False and result["changed_sign"] == ["S3"]
    assert tool.robust(-0.05, every(-0.05) | {"S9": 0.0})["changed_sign"] == ["S9"]


def test_a_sensitivity_not_performed_stops_it_being_robust_and_is_listed():
    result = tool.robust(0.05, every() | {"S7": None})
    assert result["robust"] is False and result["not_performed"] == ["S7"] and result["changed_sign"] == []
    assert tool.robust(0.05, {sid: 0.05 for sid in IDS[:8]})["not_performed"] == ["S9"]


def test_a_negative_effect_is_robust_with_a_negative_sign():
    result = tool.robust(-0.03, every(-0.001))
    assert result["robust"] is True and result["sign"] == -1


# decision


def verdict(sign=None):
    """A robustness entry: robust with a sign, or not robust."""
    if sign is None:
        return {"robust": False, "sign": 1}
    return {"robust": True, "sign": sign}


def matrix(cash=(None, None, None), duration=(None, None, None), drawdown=None, total=None):
    def block(signs):
        return {
            ep: {"compounded_return": verdict(s), "max_drawdown": verdict(drawdown)}
            for ep, s in zip(tool.EPISODES, signs, strict=True)
        }

    return {
        "cash_rate_and_currency": block(cash),
        "treasury_duration": block(duration),
        "total": {
            ep: {"compounded_return": verdict(total), "max_drawdown": verdict(total)} for ep in tool.EPISODES
        },
    }


def test_opposite_robust_signs_in_two_episodes_give_the_first_row():
    result = tool.decision(matrix(cash=(1, None, -1)))
    assert result["row"] == 1 and result["text"] == tool.ROWS[1]
    assert result["effects"]["cash_rate_and_currency"]["row"] == 1
    assert result["effects"]["treasury_duration"]["row"] == 3


def test_robust_results_of_one_sign_give_the_second_row():
    result = tool.decision(matrix(duration=(-1, -1, None)))
    assert result["row"] == 2
    assert result["effects"]["treasury_duration"] == {
        "row": 2,
        "text": tool.ROWS[2],
        "robust_signs": [-1],
    }
    assert tool.decision(matrix(cash=(1, 1, 1)))["row"] == 2


def test_no_robust_result_gives_the_third_row():
    result = tool.decision(matrix())
    assert result["row"] == 3 and result["text"] == tool.ROWS[3]
    assert {f["row"] for f in result["effects"].values()} == {3}


def test_a_single_effect_in_the_first_row_decides_when_the_effects_differ():
    result = tool.decision(matrix(cash=(1, 1, 1), duration=(1, -1, None)))
    assert result["row"] == 1
    assert result["effects"]["cash_rate_and_currency"]["row"] == 2
    assert result["effects"]["treasury_duration"]["row"] == 1
    mixed = tool.decision(matrix(cash=(None, None, None), duration=(1, 1, None)))
    assert mixed["row"] == 2  # one effect robust with one sign, none with opposite signs


def test_drawdown_and_the_total_effect_cannot_change_the_decision():
    assert tool.decision(matrix(drawdown=1, total=1))["row"] == 3
    opposite = matrix()
    opposite["total"]["2008"]["compounded_return"] = verdict(1)
    opposite["total"]["2022"]["compounded_return"] = verdict(-1)
    for ep, sign in zip(tool.EPISODES, (1, None, -1), strict=True):
        opposite["cash_rate_and_currency"][ep]["max_drawdown"] = verdict(sign)
    assert tool.decision(opposite)["row"] == 3


# analyse on invented panels


def large_effect_panel(cash=0.002):
    # AUD bills at 1%/month against cash: the cash-rate effect is about 4 points over twelve months.
    return make_panel(equity=0.0, bills=0.01, treasury=0.02, cash=cash)


def test_analyse_marks_a_robust_effect_and_one_that_is_too_small():
    frozen = large_effect_panel()
    variants = {sid: tool.Variant(frozen) for sid in IDS}
    result = tool.analyse(frozen, variants)
    cash = result["robustness"]["cash_rate_and_currency"]
    assert cash["2008"]["compounded_return"]["robust"] is True
    assert cash["q1_2020"]["compounded_return"]["robust"] is False  # three months: under 2 points
    assert cash["q1_2020"]["compounded_return"]["at_least_2_points"] is False
    assert result["decision"]["row"] == 2
    assert all(s["performed"] for s in result["sensitivities"].values())


def test_analyse_with_a_sensitivity_that_flips_the_sign_or_was_not_built():
    frozen = large_effect_panel()
    flipped = large_effect_panel(cash=0.02)  # cash now beats bills, so the cash-rate effect changes sign
    variants = {sid: tool.Variant(frozen) for sid in IDS}
    variants["S4"] = tool.Variant(flipped)
    variants["S8"] = tool.Variant(None, "no H.10 file")
    result = tool.analyse(frozen, variants)
    r = result["robustness"]["cash_rate_and_currency"]["2008"]["compounded_return"]
    assert r["robust"] is False and r["changed_sign"] == ["S4"] and r["not_performed"] == ["S8"]
    assert result["sensitivities"]["S8"] == {"performed": False, "why": "no H.10 file"}
    assert result["decision"]["row"] == 3


def test_a_missing_sensitivity_is_not_performed():
    frozen = large_effect_panel()
    result = tool.analyse(frozen, {sid: tool.Variant(frozen) for sid in IDS[:8]})
    assert result["sensitivities"]["S9"]["performed"] is False
    assert result["robustness"]["cash_rate_and_currency"]["2008"]["compounded_return"]["not_performed"] == [
        "S9"
    ]


# render, run and main


WORDS = "retrospective description only: three hand-named episodes confirm nothing"


def test_the_report_has_a_table_per_episode_the_robustness_table_and_the_words():
    frozen = large_effect_panel()
    result = tool.analyse(frozen, {sid: tool.Variant(frozen) for sid in IDS})
    report = tool.render(result, "panel", "abc")
    for name in tool.EPISODES:
        assert f"## Episode `{name}`" in report
    assert "## Robustness" in report and "## Decision rule (step 7)" in report
    assert WORDS in report.lower()
    assert tool.ROWS[2] in report and tool.RECOMMENDATION_NOTE in report


def test_stdout_holds_status_and_robustness_but_no_sizes():
    frozen = large_effect_panel()
    result = tool.analyse(frozen, {sid: tool.Variant(frozen) for sid in IDS[:8]})
    lines = tool.stdout_lines(result)
    assert "S9: not performed: no such sensitivity was built" in lines
    assert "cash_rate_and_currency 2008 compounded_return: not robust, +" in lines
    assert lines[-1] == "decision: row 3"
    assert not any("%" in line or "." in line.split(":")[-1] for line in lines[-3:-1])


@pytest.fixture
def workspace(tmp_path):
    root = tmp_path / "ws"
    root.mkdir(mode=0o700)
    run_dir = root / "runs" / "r1"
    run_dir.mkdir(parents=True)
    (run_dir / "run.json").write_text(json.dumps({"panel_id": "invented", "panel_sha256": "0"}))
    return root


def fake_loader(monkeypatch, panel):
    monkeypatch.setattr(tool.common, "load_frozen", lambda root: (panel, root / "runs" / "r1"))


def test_run_writes_a_report_and_a_summary_under_a_new_directory(workspace, monkeypatch):
    frozen = large_effect_panel()
    fake_loader(monkeypatch, frozen)
    summary = tool.run(
        workspace,
        workspace,
        workspace,
        workspace,
        workspace,
        workspace,
        gate=None,
        code={"commit": "0123456789abcdef"},
        variants_of=lambda *_: {sid: tool.Variant(frozen) for sid in IDS},
    )
    out = workspace / "corroboration" / "step6" / summary["output"]
    assert out.name.endswith("-01234567")
    assert (out / "report.md").is_file()
    saved = json.loads((out / "summary.json").read_text())
    assert saved["panel_id"] == "invented" and saved["decision"]["row"] == 2
    assert WORDS in saved["words"].lower() and set(saved["episodes"]) == set(tool.EPISODES)


def test_main_prints_status_and_exits_zero_even_when_nothing_is_robust(workspace, monkeypatch, capsys):
    frozen = large_effect_panel()
    fake_loader(monkeypatch, frozen)
    monkeypatch.setattr(
        tool, "build_variants", lambda *_: {sid: tool.Variant(None, "invented") for sid in IDS}
    )
    monkeypatch.setattr(tool.ev, "make_gate", lambda: None)
    monkeypatch.setattr(tool.ev, "code_commit", lambda: {"commit": "f" * 40})
    code = tool.main(["--root", str(workspace)])
    out = capsys.readouterr().out
    assert code == 0
    assert "S1: not performed: invented" in out and "decision: row 3" in out


def test_main_exits_two_on_a_stop_and_prints_no_values(workspace, monkeypatch, capsys):
    def stop(*_args, **_kwargs):
        raise ev.Stop("a month is missing")

    monkeypatch.setattr(tool.ev, "make_gate", lambda: None)
    monkeypatch.setattr(tool.ev, "code_commit", lambda: {"commit": "f" * 40})
    monkeypatch.setattr(tool, "run", stop)
    assert tool.main(["--root", str(workspace)]) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and "stopped: a month is missing" in captured.err


# sensitivity effects, inputs and what each sensitivity can test


def varied_panel():
    shocks = {(i, c): 0.01 * ((i * (c + 3)) % 7 - 3) for i in range(180) for c in range(3)}
    return make_panel(shocks=shocks)


def test_common_fx_and_cash_cannot_change_the_treasury_duration_sign_and_only_scale_it():
    base_panel = varied_panel()
    n = base_panel.returns.shape[0]
    window, months = tool.EPISODES["2008"]
    zero = tool.episode_measures(base_panel, window, months)["effects"]["treasury_duration"]
    fx = np.array([0.03 if i % 2 else -0.04 for i in range(n)])
    cash = np.array([0.0 if i % 3 else 0.05 for i in range(n)])
    for variant in (
        common.with_changes(base_panel, s=fx),
        common.with_changes(base_panel, cash=cash),
        common.with_changes(base_panel, s=fx, cash=cash),
    ):
        got = tool.episode_measures(variant, window, months)["effects"]["treasury_duration"]
        # by hand: W_FX is the product of the 12 months of (1 + s) in the window
        kept = [
            i for i in range(n) if window[0] <= base_panel.months[i] and base_panel.months[i + 1] <= window[1]
        ]
        w_fx = float(np.prod(1 + variant.s[kept]))
        assert w_fx > 0
        assert got["compounded_return"] == pytest.approx(w_fx * zero["compounded_return"], abs=1e-12)
        assert tool.sign_of(got["compounded_return"]) == tool.sign_of(zero["compounded_return"]) != 0


def test_sensitivity_effects_hold_the_frozen_value_and_each_sensitivity_or_none():
    frozen = large_effect_panel()
    flipped = large_effect_panel(cash=0.02)
    variants = {sid: tool.Variant(frozen) for sid in IDS[:8]}
    variants["S4"] = tool.Variant(flipped)
    result = tool.analyse(frozen, variants)
    cell = result["sensitivity_effects"]["cash_rate_and_currency"]["2008"]["compounded_return"]
    assert set(cell) == {"frozen", *IDS}
    assert (
        cell["frozen"] == result["episodes"]["2008"]["effects"]["cash_rate_and_currency"]["compounded_return"]
    )
    assert cell["S1"] == cell["frozen"] and cell["S9"] is None
    assert (
        cell["S4"]
        == tool.episode_measures(flipped, *tool.EPISODES["2008"])["effects"]["cash_rate_and_currency"][
            "compounded_return"
        ]
    )
    assert set(result["sensitivity_effects"]) == set(tool.base.EFFECTS)


def test_the_report_has_margins_and_what_each_sensitivity_can_test():
    frozen = large_effect_panel()
    flipped = large_effect_panel(cash=0.012)  # the effect shrinks to about -1 point, nearer zero
    variants = {sid: tool.Variant(frozen) for sid in IDS[:8]}
    variants["S4"] = tool.Variant(flipped)
    result = tool.analyse(frozen, variants)
    report = tool.render(result, "panel", "abc")
    assert "## Margins" in report and "## What each sensitivity can test" in report
    assert tool.CAN_TEST_NOTE in report and "only S1 to S5 are a challenge" in report
    rows = tool.margin_rows(result)
    assert len(rows) == 9
    cash_2008 = next(r for r in rows if r[:2] == ["cash_rate_and_currency", "2008"])
    assert cash_2008[2] == "S4"  # the flipped cash rate is nearest zero
    cell = result["sensitivity_effects"]["cash_rate_and_currency"]["2008"]["compounded_return"]
    assert cash_2008[3] == tool.pct(cell["S4"])


def test_sensitivity_inputs_hash_each_file_and_record_a_missing_one_as_null(tmp_path):
    root, e2, e1, e3, hist, h10 = (tmp_path / n for n in ("t", "e2", "e1", "e3", "h", "h10"))
    (root / "reference" / "raw").mkdir(parents=True)
    (root / "reference" / "nav-spy.csv").write_bytes(b"spy")
    (root / "reference" / "raw" / "rba-cash-rate.html").write_bytes(b"page")
    (e3 / "raw").mkdir(parents=True)
    (e3 / "raw" / "rba_f1.csv").write_bytes(b"f1")
    hist.mkdir()
    (hist / "firmmcrid.csv").write_bytes(b"hist")
    (e1 / "raw").mkdir(parents=True)
    (e1 / "variant-summary.json").write_text(json.dumps({"release": "rel"}))
    folder = e1 / "store-variant" / "releases" / tool.e1.DATASET_ID / "rel"
    folder.mkdir(parents=True)
    (folder / "data.csv").write_bytes(b"v1")
    (e1 / "raw" / "b.xml").write_bytes(b"BB")
    (e1 / "raw" / "a.xml").write_bytes(b"AA")
    (e1 / "raw" / "c.txt").write_bytes(b"ignored")
    snap = tool.ev.snapshot_dir(e2, tool.panel_tool.SNAPSHOT)
    snap.mkdir(parents=True)
    (snap / "manifest.json").write_bytes(b"{}")

    def sha(data):
        return tool.hashlib.sha256(data).hexdigest()

    got = tool.sensitivity_inputs(root, e2, e1, e3, hist, h10)
    assert got["reference/nav-spy.csv"] == sha(b"spy")
    assert got["reference/nav-bil.csv"] is None and got["reference/nav-ief.csv"] is None
    assert got["reference/raw/rba-cash-rate.html"] == sha(b"page")
    assert got["reference/manifest.json"] is None and got["H10/FRB_h10_xml.zip"] is None
    assert got["E-0003/raw/rba_f1.csv"] == sha(b"f1") and got["RBA-F1-history/firmmcrid.csv"] == sha(b"hist")
    assert got["E-0001/variant-summary.json"] == sha((e1 / "variant-summary.json").read_bytes())
    assert got["E-0001/variant release data.csv"] == sha(b"v1")
    assert got["E-0001/raw/*.xml"] == sha(b"a.xml" + b"AA" + b"b.xml" + b"BB")
    assert got["E-0002/raw/s2/manifest.json"] == sha(b"{}")


def test_the_xml_hash_changes_when_one_files_bytes_change(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "a.xml").write_bytes(b"AA")
    (raw / "b.xml").write_bytes(b"BB")
    before = tool.xml_sha256(raw)
    (raw / "b.xml").write_bytes(b"BC")
    assert tool.xml_sha256(raw) != before
    assert tool.xml_sha256(tmp_path / "none") is None


def test_missing_workspaces_give_null_inputs_and_run_keeps_both_new_keys(workspace, monkeypatch):
    frozen = large_effect_panel()
    fake_loader(monkeypatch, frozen)
    summary = tool.run(
        workspace,
        workspace / "e2",
        workspace / "e1",
        workspace / "e3",
        workspace / "h",
        workspace / "h10",
        gate=None,
        code={"commit": "0123456789abcdef"},
        variants_of=lambda *_: {sid: tool.Variant(frozen) for sid in IDS},
    )
    out = workspace / "corroboration" / "step6" / summary["output"]
    saved = json.loads((out / "summary.json").read_text())
    assert set(saved["sensitivity_inputs"].values()) == {None}
    assert "reference/nav-spy.csv" in saved["sensitivity_inputs"]
    assert saved["sensitivity_effects"]["treasury_duration"]["2008"]["max_drawdown"]["S9"] is not None
    assert "## Margins" in (out / "report.md").read_text()


def test_stdout_still_holds_no_sizes_or_hashes():
    frozen = large_effect_panel()
    result = tool.analyse(frozen, {sid: tool.Variant(frozen) for sid in IDS})
    text = "\n".join(tool.stdout_lines(result))
    assert "sensitivity_inputs" not in text and "Margins" not in text
    for line in tool.stdout_lines(result):
        assert line.startswith(("S", "decision: row ")) or line.endswith(
            ("robust, +", "robust, -", "robust, 0")
        )
    assert "%" not in text


def test_a_last_trading_day_within_five_days_of_the_bound_is_covered_and_further_stops():
    months = [date(2021, 12, 31), date(2022, 1, 31), date(2022, 2, 28), date(2022, 3, 28)]
    panel = common.FrozenPanel(months, np.full((3, 4), 0.01), np.full(3, 0.01), np.zeros(3))
    window = (date(2021, 12, 31), date(2022, 3, 31))
    assert tool.episode_measures(panel, window, 3)["end"] == "2022-03-28"
    with pytest.raises(tool.ev.Stop, match="covered by month ends"):
        tool.episode_measures(panel, (date(2021, 12, 31), date(2022, 4, 4)), 3)
