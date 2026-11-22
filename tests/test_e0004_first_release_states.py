"""Tests for tools/e0004_first_release_states.py on invented data only."""

from __future__ import annotations

import importlib.util
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "tests" / "fixtures" / "bls" / "cpi_07162013.htm.snippet"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "tools" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tool = _load("e0004_first_release_states_under_test", "e0004_first_release_states.py")
state = _load("e0004_state_under_test", "e0004_state.py")

ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# Invented levels: 2012 is 100 throughout; 2013 is 110 (rate 0.1); 2014 Jan..May is 121, so each 2014 rate is
# exactly 0.1 as well (121 / 110 - 1): the equality rule decides every state.
def flat_levels():
    out = {}
    by_year = {2011: "100.000", 2012: "100.000", 2013: "110.000", 2014: "121.000"}
    for year, level in by_year.items():
        for month in range(1, 13):
            out[(year, month)] = Decimal(level)
    return out


def ref_months():
    return (
        [(2012, m) for m in range(1, 13)]
        + [(2013, m) for m in range(1, 13)]
        + [(2014, m) for m in range(1, 6)]
    )


def release_day(ref):
    return date(ref[0] + ref[1] // 12, ref[1] % 12 + 1, 15)


RELEASES = [release_day(r) for r in ref_months()]
MONTH_ENDS = [date(2014, 3, 31), date(2014, 4, 30), date(2014, 5, 31), date(2014, 6, 30)]


def page(ref, level, ago_level, prev_level="100.000"):
    """A release page built from the fixture shape by replacing its month labels and levels."""
    prev = (ref[0] - 1, 12) if ref[1] == 1 else (ref[0], ref[1] - 1)

    def lab(m, year):
        return f"{ABBR[m - 1]}<br />{year}"

    text = FIXTURE.read_text()
    for old, token in (
        ("Jun.<br />2012", "@YA@"),
        ("May<br />2013", "@PREV@"),
        ("Jun.<br />2013", "@REF@"),
        ("229.478", "@LYA@"),
        ("232.945", "@LPREV@"),
        ("233.504", "@LREF@"),
    ):
        text = text.replace(old, token)
    for token, value in (
        ("@YA@", lab(ref[1], ref[0] - 1)),
        ("@PREV@", lab(prev[1], prev[0])),
        ("@REF@", lab(ref[1], ref[0])),
        ("@LYA@", str(ago_level)),
        ("@LPREV@", prev_level),
        ("@LREF@", str(level)),
    ):
        text = text.replace(token, value)
    return text


def write_releases(directory, levels, *, skip=(), ago_override=None, level_override=None):
    directory.mkdir(parents=True, exist_ok=True)
    flat = flat_levels()
    for ref in ref_months():
        if ref in skip:
            continue
        level = (level_override or {}).get(ref, levels[ref])
        ago = (ago_override or {}).get(ref, flat[(ref[0] - 1, ref[1])])
        day = release_day(ref)
        (directory / f"cpi_{day:%m%d%Y}.htm").write_text(page(ref, level, ago))
    return directory


def recorded_states(flat=None):
    return state.states(MONTH_ENDS, RELEASES, flat or flat_levels())


@pytest.fixture
def releases_dir(tmp_path):
    return write_releases(tmp_path / "rel", flat_levels())


def first_levels(directory):
    return tool.first_release_series([directory])[0]


def compare(directory, recorded=None):
    return tool.compare_states(
        MONTH_ENDS, RELEASES, flat_levels(), first_levels(directory), recorded or recorded_states()
    )


def test_identical_series_reads_identical(releases_dir):
    result = compare(releases_dir)
    assert result["reading"] == "identical"
    assert result["reproduces_run"] is True
    assert result["primary"]["differing"] == 0
    assert result["equal_is_accelerating"]["differing"] == 0
    assert result["missing_first_release_months"] == []
    assert result["periods"] == 3
    assert recorded_states() == ["not"] * 3


def test_a_revised_level_that_flips_a_state_is_listed(tmp_path):
    directory = write_releases(
        tmp_path / "rel", flat_levels(), level_override={(2014, 2): Decimal("130.000")}
    )
    result = compare(directory)
    assert result["reading"] == "differences found"
    assert result["primary"]["differing_periods"] == [
        {
            "period_start": "2014-03-31",
            "period_end": "2014-04-30",
            "flat": "not",
            "first_release": "accelerating",
        }
    ]
    assert result["equal_is_accelerating"]["differing"] == 0


def test_a_revision_that_changes_only_the_equality_rule_is_caught(tmp_path):
    directory = write_releases(
        tmp_path / "rel", flat_levels(), level_override={(2014, 2): Decimal("120.000")}
    )
    result = compare(directory)
    assert result["primary"]["differing"] == 0
    assert result["equal_is_accelerating"]["differing"] == 1
    assert result["equal_is_accelerating"]["differing_periods"][0]["period_start"] == "2014-03-31"
    assert result["reading"] == "differences found"


def test_a_missing_first_release_month_is_named_and_reads_incomplete(tmp_path):
    directory = write_releases(tmp_path / "rel", flat_levels(), skip={(2012, 2)})
    result = compare(directory)
    assert result["missing_first_release_months"] == ["2012-02"]
    assert result["primary"]["differing"] == 0  # the older release gives the same rate here
    assert result["reading"] == "incomplete"


def test_october_2025_missing_from_both_is_unpublished_not_a_gap():
    # the release of 2025-11-12 has reference month 2025-10, which no series holds
    ends = [date(2025, 12, 31), date(2026, 1, 31)]
    days = [date(2025, 11, 12)]
    levels = {(2024, 10): Decimal("100.000")}
    result = tool.compare_states(ends, days, levels, dict(levels), ["unavailable"])
    assert result["unpublished_months"] == ["2025-10"]
    assert result["missing_first_release_months"] == []
    assert result["reading"] == "identical"


def test_october_2025_held_by_the_flat_file_but_not_first_release_is_a_gap():
    ends = [date(2025, 12, 31), date(2026, 1, 31)]
    days = [date(2025, 11, 12)]
    flat = {(2024, 10): Decimal("100.000"), (2025, 10): Decimal("101.000")}
    first = {(2024, 10): Decimal("100.000")}
    result = tool.compare_states(ends, days, flat, first, ["unavailable"])
    assert result["unpublished_months"] == []
    assert result["missing_first_release_months"] == ["2025-10"]
    assert result["reading"] == "incomplete"


def test_two_releases_for_one_month_refuse(tmp_path):
    first = write_releases(tmp_path / "a", flat_levels())
    second = tmp_path / "b"
    second.mkdir()
    (second / "cpi_03152014_again.htm").write_text(page((2014, 2), Decimal("121.000"), Decimal("110.000")))
    with pytest.raises(ValueError, match="2014-02"):
        tool.first_release_series([first, second])


def test_an_unparseable_release_refuses(tmp_path):
    directory = write_releases(tmp_path / "rel", flat_levels())
    (directory / "cpi_09152014.htm").write_text("<html>no table here</html>")
    with pytest.raises(ValueError, match="cpi_09152014"):
        tool.first_release_series([directory])


def test_a_reference_level_that_is_not_printed_refuses(tmp_path):
    directory = tmp_path / "rel"
    directory.mkdir()
    (directory / "cpi_03152014.htm").write_text(page((2014, 2), "-", Decimal("110.000")))
    with pytest.raises(ValueError, match="no level"):
        tool.first_release_series([directory])


def test_an_empty_directory_refuses(tmp_path):
    with pytest.raises(ValueError, match="no cpi_"):
        tool.first_release_series([tmp_path])


def test_a_states_file_that_does_not_reproduce_is_not_identical(releases_dir):
    result = compare(releases_dir, recorded=["accelerating", "not", "not"])
    assert result["reproduces_run"] is False
    assert result["reading"] == "incomplete"


def test_the_ledger_has_one_row_per_month_with_name_and_hash(releases_dir):
    levels, ledger = tool.first_release_series([releases_dir])
    assert len(ledger) == len(levels) == len(ref_months())
    row = ledger[-1]
    assert row["month"] == "2014-05"
    assert row["release"] == "cpi_06152014.htm"
    assert len(row["sha256"]) == 64
    assert row["printed"] == "121.000"


def test_year_ago_check_reports_a_difference_without_changing_levels(tmp_path):
    directory = write_releases(tmp_path / "rel", flat_levels(), ago_override={(2014, 3): Decimal("111.000")})
    levels, _ledger = tool.first_release_series([directory])
    before = dict(levels)
    rows = tool.year_ago_checks([directory], levels)
    assert rows == [
        {"release": "cpi_04152014.htm", "month": "2013-03", "year_ago": "111.000", "first": "110.000"}
    ]
    assert levels == before
    assert levels[(2013, 3)] == Decimal("110.000")


def test_states_csv_gives_month_ends_and_states(tmp_path):
    path = tmp_path / "states.csv"
    path.write_text(
        "period_start,period_end,state\n2014-03-31,2014-04-30,not\n2014-04-30,2014-05-31,accelerating\n"
    )
    assert tool.month_ends_from_states_csv(path) == (
        [date(2014, 3, 31), date(2014, 4, 30), date(2014, 5, 31)],
        ["not", "accelerating"],
    )


def test_states_csv_with_a_bad_header_or_a_gap_refuses(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("start,end,state\n2014-03-31,2014-04-30,not\n")
    with pytest.raises(ValueError, match="header"):
        tool.month_ends_from_states_csv(bad)
    gap = tmp_path / "gap.csv"
    gap.write_text("period_start,period_end,state\n2014-03-31,2014-04-30,not\n2014-05-31,2014-06-30,not\n")
    with pytest.raises(ValueError, match="chain"):
        tool.month_ends_from_states_csv(gap)


def make_raw(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    lines = ["series_id\tyear\tperiod\tvalue\tfootnote_codes"]
    for (year, month), level in sorted(flat_levels().items()):
        lines.append(f"CUUR0000SA0\t{year}\tM{month:02d}\t{level}\t")
    (raw / tool._releases.FLAT_NAME).write_text("\n".join(lines) + "\n")
    rows = ["date,url"] + [f"{d.isoformat()},https://example.invalid/{d:%m%d%Y}" for d in RELEASES]
    (raw / "release-dates.csv").write_text("\n".join(rows) + "\n")
    states = ["period_start,period_end,state"]
    for i, label in enumerate(recorded_states()):
        states.append(f"{MONTH_ENDS[i].isoformat()},{MONTH_ENDS[i + 1].isoformat()},{label}")
    (tmp_path / "states.csv").write_text("\n".join(states) + "\n")
    return raw, tmp_path / "states.csv"


def test_the_command_line_writes_both_files_and_prints_no_level(tmp_path, releases_dir, capsys):
    raw, states = make_raw(tmp_path)
    out = tmp_path / "out"
    code = tool.main(
        ["--raw", str(raw), "--releases", str(releases_dir), "--states", str(states), "--out", str(out)]
    )
    printed = capsys.readouterr().out
    assert code == 0
    assert "reading: identical" in printed
    for level in ("100.000", "110.000", "121.000"):
        assert level not in printed
    header = (out / "ledger.csv").read_text().splitlines()[0]
    assert header == "month,release,sha256,printed,flat,equal"
    assert json.loads((out / "state-comparison.json").read_text())["reading"] == "identical"


def test_the_command_line_refuses_an_output_inside_the_repository(tmp_path, releases_dir, capsys):
    raw, states = make_raw(tmp_path)
    out = REPO / "tests" / "_no_such_output_dir"
    code = tool.main(
        ["--raw", str(raw), "--releases", str(releases_dir), "--states", str(states), "--out", str(out)]
    )
    assert code == 2
    assert "refused:" in capsys.readouterr().err
    assert not out.exists()


def test_the_command_line_refuses_an_unparseable_release(tmp_path, capsys):
    raw, states = make_raw(tmp_path)
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "cpi_01012014.htm").write_text("nothing")
    code = tool.main(
        ["--raw", str(raw), "--releases", str(bad), "--states", str(states), "--out", str(tmp_path / "o")]
    )
    assert code == 2
    assert "refused:" in capsys.readouterr().err
