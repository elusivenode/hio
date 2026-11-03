"""T-0014 P-1: the cash evidence report classifies every eligible period of both currencies exactly
once, leaves a disposition slot for each non-agreeing class, is deterministic, and never passes or
fails. Synthetic only: the releases come from the S1b-1 synthetic world; the classes the world does not
produce are made by rewriting a comparison release's rows."""

from __future__ import annotations

import csv
import io
import json

import pytest

from hio.jobs.s1b1 import COMPARISON
from hio.jobs.s1b1_cash_evidence import (
    AGREES,
    ALIGNMENT,
    CLASSES,
    MISSING,
    NON_AGREEING,
    PRECISION,
    RESIDUAL,
    build_report,
    render_json,
    render_markdown,
)
from hio.publish.release import Release, make_release, render_csv
from tests.test_s1b1_releases import world  # noqa: F401  (a fixture)

AUD, USD = "cash.aud.overnight", "cash.usd.overnight"
AUD_CMP, USD_CMP = "cash.aud.overnight.vs_tri", "cash.usd.overnight.vs_sofr_index"


def _rows(release: Release) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(release.files["data.csv"].decode())))


def _rewrite(release: Release, edit) -> Release:
    """The same comparison release with its rows edited (a list of dicts, edited in place or returned)."""
    rows = _rows(release)
    rows = edit(rows) or rows
    columns = list(rows[0])
    core = {k: v for k, v in release.core.items() if k != "files"}
    data = render_csv(columns, ([r[c] for c in columns] for r in rows))
    return make_release(core, {"data.csv": data})


def _with(releases, out_id, edit):
    return {**releases, out_id: _rewrite(releases[out_id], edit)}


def _by_start(report, cash_id):
    return {p["period_start"]: p for p in report["currencies"][cash_id]["periods"]}


def _row(rows, classification):
    return next(r for r in rows if r["classification"] == classification)


@pytest.fixture(scope="module")
def releases(world):  # noqa: F811
    return world[6]


def test_every_eligible_period_appears_exactly_once_in_exactly_one_class(releases):
    report = build_report(releases)
    assert set(report["currencies"]) == {AUD, USD}
    for cash_id, out_id in ((AUD, AUD_CMP), (USD, USD_CMP)):
        cur = report["currencies"][cash_id]
        keys = [(p["period_start"], p["period_end"]) for p in cur["periods"]]
        cash = releases[cash_id]
        want = {(r["period_start"], r["period_end"]) for r in _rows(cash)}
        want |= {(s, e) for s, e, _ in cash.core["quality_summary"]["absent_periods"]}
        assert len(keys) == len(set(keys)) and set(keys) == want
        assert keys == sorted(keys)
        assert {p["class"] for p in cur["periods"]} <= set(CLASSES)
        assert sum(cur["counts"].values()) == len(keys)
        assert cur["comparison_rows_without_a_cash_period"] == []
        assert cur["reference_series"] == COMPARISON[out_id][1]


def test_the_synthetic_world_has_agreeing_and_missing_comparison_periods(releases):
    report = build_report(releases)
    assert report["currencies"][AUD]["counts"][AGREES] > 0
    usd = report["currencies"][USD]
    assert usd["counts"][AGREES] > 0 and usd["counts"][MISSING] > 0
    by = _by_start(report, USD)
    assert by["2026-10-09"]["class"] == MISSING
    assert by["2026-10-09"]["cause"] == "reference_missing_at_end"
    assert by["2026-10-09"]["accrual"]  # the accrual side is still reported


def test_the_report_is_deterministic(releases):
    assert render_json(build_report(releases)) == render_json(build_report(dict(reversed(releases.items()))))
    assert render_markdown(build_report(releases)) == render_markdown(build_report(releases))


def test_a_precision_difference_is_classified(releases):
    def edit(rows):
        _row(rows, "within_expected_bound")["classification"] = "precision_exceeds_declared"

    report = build_report(_with(releases, AUD_CMP, edit))
    assert report["currencies"][AUD]["counts"][PRECISION] == 1
    assert report["currencies"][AUD]["counts"][RESIDUAL] == 0


def test_a_residual_outside_the_bound_is_unexplained(releases):
    def edit(rows):
        row = _row(rows, "within_expected_bound")
        row["classification"], row["cause"] = "outside_expected_bound", "residual not explained"

    report = build_report(_with(releases, AUD_CMP, edit))
    cur = report["currencies"][AUD]
    assert cur["counts"][RESIDUAL] == 1
    assert [p["cause"] for p in cur["periods"] if p["class"] == RESIDUAL] == ["residual not explained"]


def test_a_comparison_accrual_that_is_not_the_cash_accrual_is_unexplained(releases):
    def edit(rows):
        _row(rows, "within_expected_bound")["ours"] = "1.5"

    cur = build_report(_with(releases, AUD_CMP, edit))["currencies"][AUD]
    assert cur["counts"][RESIDUAL] == 1
    assert (
        "not 1 + the cash release's r" in next(p for p in cur["periods"] if p["class"] == RESIDUAL)["cause"]
    )


def test_a_period_the_comparison_dates_differently_is_a_date_alignment_difference(releases):
    start = min(r["period_start"] for r in _rows(releases[AUD_CMP]))
    moved = {}

    def edit(rows):
        row = next(r for r in rows if r["period_start"] == start)
        moved["old"] = row["period_end"]
        row["period_end"] = "2099-01-01"

    report = build_report(_with(releases, AUD_CMP, edit))
    cur = report["currencies"][AUD]
    assert cur["counts"][ALIGNMENT] == 1
    period = _by_start(report, AUD)[start]
    assert period["class"] == ALIGNMENT and period["period_end"] == moved["old"]
    assert "2099-01-01" in period["cause"]
    assert cur["comparison_rows_without_a_cash_period"] == []  # the misdated row is consumed once


def test_a_period_with_no_comparison_row_is_a_missing_comparison(releases):
    start = min(r["period_start"] for r in _rows(releases[AUD_CMP]))
    before = build_report(releases)["currencies"][AUD]["counts"][MISSING]

    def edit(rows):
        return [r for r in rows if r["period_start"] != start]

    report = build_report(_with(releases, AUD_CMP, edit))
    period = _by_start(report, AUD)[start]
    assert (period["class"], period["cause"]) == (MISSING, "no_comparison_row")
    assert report["currencies"][AUD]["counts"][MISSING] == before + 1


def test_a_comparison_row_with_no_cash_period_is_listed_not_counted(releases):
    def edit(rows):
        return [*rows, {**rows[0], "period_start": "2099-01-01", "period_end": "2099-01-02"}]

    cur = build_report(_with(releases, AUD_CMP, edit))["currencies"][AUD]
    assert cur["comparison_rows_without_a_cash_period"] == [
        {"period_start": "2099-01-01", "period_end": "2099-01-02"}
    ]
    assert sum(cur["counts"].values()) == len(cur["periods"])


def test_every_non_agreeing_class_has_an_unwritten_disposition_slot(releases):
    report = build_report(releases)
    for cur in report["currencies"].values():
        assert [s["class"] for s in cur["dispositions"]] == list(NON_AGREEING)
        for slot in cur["dispositions"]:
            assert slot["periods"] == cur["counts"][slot["class"]]
            assert slot["required"] == (slot["periods"] > 0)
            assert slot["disposition"] is None and slot["written_by"] is None
            assert slot["evidence_refs"] == []


def test_the_report_neither_passes_nor_fails(releases):
    report = build_report(releases)
    assert "does not pass or fail" in report["statement"]
    keys: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            keys.update(node)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(report)
    assert not keys & {"pass", "passed", "fail", "failed", "verdict", "approved", "accepted"}


def test_the_json_is_canonical_and_the_markdown_has_a_template_per_class(releases):
    report = build_report(releases)
    data = render_json(report)
    assert json.loads(data) == report and data.endswith(b"\n")
    md = render_markdown(report)
    for cash_id in (AUD, USD):
        assert f"## {cash_id} against" in md
        for cls in NON_AGREEING:
            assert f"### {cash_id}: {cls} (" in md
    assert "_not yet written_" in md and "_unset_" in md
    assert report["cutoff"] in md


def test_the_comparison_must_have_been_built_from_the_supplied_cash_release(releases):
    other = {**releases, AUD: releases[USD]}
    with pytest.raises(ValueError):
        build_report(other)
    with pytest.raises(ValueError, match="needs"):
        build_report({k: v for k, v in releases.items() if k != USD_CMP})
