"""T-0020 X-5: the parser and bars, on invented XML and invented yields only."""

import importlib.util
from datetime import date, timedelta
from decimal import Decimal as D
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("e0001_run", REPO / "tools" / "e0001_run.py")
tool = importlib.util.module_from_spec(_spec)
import sys  # noqa: E402

sys.modules["e0001_run"] = tool
_spec.loader.exec_module(tool)

HEAD = (
    '<feed xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices" '
    'xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata" '
    'xmlns="http://www.w3.org/2005/Atom">'
)
NAMES = ["BC_6MONTH", "BC_1YEAR", "BC_2YEAR", "BC_3YEAR", "BC_5YEAR", "BC_7YEAR", "BC_10YEAR"]


def entry(day: str, **values) -> str:
    cells = "".join(f"<d:{n}>{values.get(n, '4.00')}</d:{n}>" for n in NAMES if values.get(n, "") != "drop")
    return (
        f"<entry><content><m:properties><d:NEW_DATE>{day}T00:00:00</d:NEW_DATE>{cells}"
        "</m:properties></content></entry>"
    )


def feed(*entries: str) -> bytes:
    return (HEAD + "".join(entries) + "</feed>").encode()


def row(day: date, level: str = "4", **over) -> "tool.Row":
    knots = dict.fromkeys(tool.FIELDS.values(), D(level))
    knots.update({D(k[1:]): v for k, v in over.items()})  # "_10" is the 10-year knot
    return tool.Row(day, knots)


def test_a_row_parses_with_exact_decimals():
    rows = tool.parse_feed(feed(entry("2026-01-05", BC_10YEAR="4.17")))
    assert rows[0].day == date(2026, 1, 5)
    assert rows[0].knots[D(10)] == D("4.17")


@pytest.mark.parametrize("blank", ["", "N/A"])
def test_blank_or_na_is_absent(blank):
    assert tool.parse_feed(feed(entry("2026-01-05", BC_7YEAR=blank)))[0].knots[D(7)] is None


def test_a_null_cell_and_a_missing_cell_are_absent():
    body = feed(
        "<entry><content><m:properties><d:NEW_DATE>2026-01-05T00:00:00</d:NEW_DATE>"
        '<d:BC_7YEAR m:null="true"/></m:properties></content></entry>'
    )
    knots = tool.parse_feed(body)[0].knots
    assert knots[D(7)] is None and knots[D(10)] is None


def test_a_non_numeric_value_stops():
    with pytest.raises(tool.Stop, match="non-numeric"):
        tool.parse_feed(feed(entry("2026-01-05", BC_7YEAR="abc")))


@pytest.mark.parametrize("value", ["25.01", "-5.01", "NaN"])
def test_out_of_range_stops(value):
    with pytest.raises(tool.Stop, match="out of range"):
        tool.parse_feed(feed(entry("2026-01-05", BC_7YEAR=value)))


def test_identical_duplicates_keep_one_and_are_counted():
    rows, duplicates = tool.dedupe([row(date(2026, 1, 5)), row(date(2026, 1, 5))])
    assert len(rows) == 1 and duplicates == 1


def test_conflicting_duplicates_stop():
    with pytest.raises(tool.Stop, match="conflicting"):
        tool.dedupe([row(date(2026, 1, 5)), row(date(2026, 1, 5), "5")])


def flat_rows(days: int = 20) -> list:
    start = date(2026, 1, 5)
    return [row(start + timedelta(days=i)) for i in range(days)]


def test_a_flat_curve_passes_every_real_data_bar_and_d_is_zero():
    report = tool.diagnostics(tool.build(flat_rows()))
    assert all(report["bars"].values())
    assert report["counts"]["covered"] == report["counts"]["periods"] == 19
    assert D(report["values"]["d_abs_max_bp"]) < D("1e-5")


def test_a_date_missing_the_ten_year_is_spanned_and_counted():
    rows = flat_rows(5)
    rows[2] = row(rows[2].day, **{"_10": None})
    result = tool.build(rows)
    assert result.counts["excluded_missing_tenor"] == 1
    assert [(p.start, p.end) for p in result.periods][1] == (rows[1].day, rows[3].day)


def test_a_missing_short_knot_keeps_the_return_and_is_uncovered():
    rows = flat_rows(5)
    rows[2] = row(rows[2].day, **{"_2": None})
    result = tool.build(rows)
    assert len(result.periods) == 4
    assert result.counts["periods_uncovered"] == 2
    assert result.counts["dates_missing_knot"] == 1


def test_low_coverage_fails_b9():
    rows = [row(r.day, **{"_2": None}) if i % 2 else r for i, r in enumerate(flat_rows(21))]
    with pytest.raises(tool.Stop, match="no period is covered"):
        tool.diagnostics(tool.build(rows))


def test_a_gap_over_a_coupon_period_refuses_that_period_and_is_counted():
    rows = [row(date(2026, 1, 5)), row(date(2026, 1, 6)), row(date(2026, 9, 1)), row(date(2026, 9, 2))]
    result = tool.build(rows)
    assert result.counts["refused_period_too_long"] == 1
    assert len(result.periods) == 2


def test_the_verdict_never_says_validated():
    first = {"accounted": True, "report": {"bars": dict.fromkeys(("B2", "B3", "B6", "B7", "B8", "B9"), True)}}
    assert tool.outcome(first, True)["verdict"] == "construction diagnostics completed; UNREFERENCED"
    assert tool.outcome(first, False)["verdict"].startswith("implementation rejected")
    assert "validated" not in tool.outcome(first, True)["verdict"]
    first["report"]["bars"]["B7"] = False
    assert tool.outcome(first, True)["verdict"] == "approximation not adequate for this purpose"
    first["report"]["bars"]["B9"] = False
    assert tool.outcome(first, True)["verdict"].startswith("approximation inconclusive")
