"""Tests for tools/e0004_state.py. Invented data only."""

from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import e0004_state as st

HEADER = "series_id        \tyear\tperiod\tvalue\tfootnote_codes"


def write_flat(tmp_path, rows, header=HEADER):
    p = tmp_path / "flat.txt"
    p.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
    return p


def row(series, year, period, value):
    return f"{series:<18}\t{year}\t{period}\t   {value}\t"


def test_load_cpi_filters_and_strips(tmp_path):
    p = write_flat(
        tmp_path,
        [
            row("CUUR0000SA0", 2025, "M01", "100.500"),
            row("CUUR0000SA0", 2025, "M13", "101.000"),
            row("CUUR0000SA0", 2025, "M10", "-"),
            row("CUUR0000SA0", 2025, "M11", "102.250"),
            row("CUSR0000SA0", 2025, "M01", "999.000"),
        ],
    )
    assert st.load_cpi(p) == {(2025, 1): Decimal("100.500"), (2025, 11): Decimal("102.250")}


def test_load_cpi_refuses_missing_header(tmp_path):
    p = write_flat(tmp_path, [row("CUUR0000SA0", 2025, "M01", "1.0")], header="a\tb\tc")
    with pytest.raises(ValueError):
        st.load_cpi(p)


def test_load_cpi_refuses_repeat(tmp_path):
    p = write_flat(tmp_path, [row("CUUR0000SA0", 2025, "M01", "1.0"), row("CUUR0000SA0", 2025, "M01", "1.1")])
    with pytest.raises(ValueError):
        st.load_cpi(p)


def test_load_releases_sorted_unique(tmp_path):
    p = tmp_path / "r.csv"
    p.write_text("date,url\n2025-02-12,u\n2025-01-15,v\n2025-02-12,w\n", encoding="utf-8")
    assert st.load_releases(p) == [date(2025, 1, 15), date(2025, 2, 12)]


def test_load_releases_refuses_bad_header(tmp_path):
    p = tmp_path / "r.csv"
    p.write_text("when,url\n2025-01-15,v\n", encoding="utf-8")
    with pytest.raises(ValueError):
        st.load_releases(p)


def test_reference_month():
    assert st.reference_month(date(2026, 1, 13)) == (2025, 12)
    assert st.reference_month(date(2025, 10, 24)) == (2025, 9)


def test_yoy_unrounded():
    cpi = {(2024, 3): Decimal("300.001"), (2025, 3): Decimal("309.123")}
    assert st.yoy(cpi, (2025, 3)) == Decimal("309.123") / Decimal("300.001") - 1
    assert len(str(st.yoy(cpi, (2025, 3)))) > 10
    assert st.yoy(cpi, (2024, 3)) is None
    assert st.yoy(cpi, (2025, 4)) is None


def make_cpi():
    cpi = {(2024, 9): Decimal("100"), (2024, 10): Decimal("100"), (2024, 11): Decimal("100")}
    cpi[(2025, 9)] = Decimal("103")
    cpi[(2025, 11)] = Decimal("105")  # October 2025 never published
    return cpi


RELS = [date(2025, 10, 24), date(2025, 11, 13), date(2025, 12, 10)]


def test_latest_rate_on_asof_day_counts():
    got = st.latest_rate(date(2025, 10, 24), RELS, make_cpi())
    assert got == (date(2025, 10, 24), (2025, 9), Decimal("0.03"))


def test_latest_rate_before_any_release():
    assert st.latest_rate(date(2025, 10, 23), RELS, make_cpi()) is None


def test_latest_rate_skips_back_over_missing_october():
    rels = [date(2025, 10, 24), date(2025, 11, 25)]  # 2025-11-25 refers to October: no level
    got = st.latest_rate(date(2025, 11, 30), rels, make_cpi())
    assert got == (date(2025, 10, 24), (2025, 9), Decimal("0.03"))


def month_end(y, m):
    nxt = date(y + (m == 12), m % 12 + 1, 1)
    return date.fromordinal(nxt.toordinal() - 1)


def monthly_ends(n, start=(2024, 1)):
    out, y, m = [], *start
    for _ in range(n):
        out.append(month_end(y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def series(rates):
    """CPI and releases so month k (from 2024-01) has yoy rates[k]; base year all 100."""
    cpi, rels = {}, []
    for m in range(1, 13):
        cpi[(2023, m)] = Decimal("100")
    for k, r in enumerate(rates):
        y, m = 2024 + k // 12, k % 12 + 1
        if y == 2024:
            cpi[(2024, m)] = Decimal("100") * (1 + Decimal(r))
        else:
            cpi[(y, m)] = cpi[(y - 1, m)] * (1 + Decimal(r))
        ny, nm = (y + (m == 12), m % 12 + 1)
        rels.append(date(ny, nm, 15))
    return cpi, rels


def test_states_accelerating_equal_and_early_unavailable():
    # 2024 yoy rates (vs 2023 base) are all 0.02; 2025 rates: first six 0.03, then 0.02 (equal -> not)
    rates = ["0.02"] * 12
    # 2025: level = 2024 level * (1+g) so yoy is g
    cpi, rels = series(rates + ["0.03"] * 6 + ["0.02"] * 6)
    ends = monthly_ends(25)  # 2024-01 .. 2025-12 month ends (25 -> through 2026-01)
    out = st.states(ends, rels, cpi)
    assert len(out) == 24
    assert out[:12] == ["unavailable"] * 12
    # i=12 is 2025-01-31: the rate a year earlier needs 2022 levels, so it is None -> unavailable
    assert out[12] == "unavailable"
    # i=13 is 2025-02-28: latest rate 0.03 (2025-01) vs 0.02 a year earlier
    assert out[13] == "accelerating"
    # i=19 is 2025-08-31: latest rate 2025-07 (0.02) vs 2024-08-31 latest 2024-07 (0.02): equal -> not
    assert out[19] == "not"


def test_states_gap_in_month_ends_unavailable():
    cpi, rels = series(["0.02"] * 12 + ["0.03"] * 12)
    ends = monthly_ends(26)
    whole = st.states(ends, rels, cpi)
    assert whole[14] == "accelerating"
    del ends[14]  # 2025-03 is missing: period 14 now starts 2025-04 against 2024-03
    out = st.states(ends, rels, cpi)
    assert out[14] == "unavailable"
