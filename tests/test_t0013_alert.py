"""T-0013 A-2: the no-attempt-write alert is a weekend-aware dead-man. The tests read monitoring.tf as
text (nothing is planned or applied) and evaluate the quiet-window expression at its edges."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TF = REPO / "infra" / "tofu"


def _code(source: str) -> str:
    return "\n".join(re.sub(r"\s*#.*$", "", line) for line in source.splitlines())


MONITORING = _code((TF / "monitoring.tf").read_text())
QUERY = re.search(r"<<-QUERY\n(.*?)\n\s*QUERY", MONITORING, re.S).group(1)
ALERT = re.search(
    r'resource "azurerm_monitor_scheduled_query_rules_alert_v2" "no_attempt_write" \{.*?\n\}(?:\n|$)',
    MONITORING,
    re.S,
).group(0)
README = " ".join((TF / "README.md").read_text().split())


def _suppressed_when_true() -> str:
    """The expression inside `where not(...)`: true means the evaluation returns a row (may breach)."""
    return re.search(r"^\s*\| where not\((.*)\)$", QUERY, re.M).group(1)


def _returns_a_row(when: datetime) -> bool:
    """Evaluate the query's own quiet-window expression at an instant (UTC), KQL dayofweek: Sunday 0."""
    expression = _suppressed_when_true()
    day = when.isoweekday() % 7
    return not eval(expression, {"__builtins__": {}}, {"DayOfWeek": day, "HourOfDay": when.hour})


def _utc(day: int, hour: int, minute: int = 0) -> datetime:
    """A moment in October-November 2026, with `day` counted from 1 October (day 32 is 1 November)."""
    return datetime(2026, 10, 1, tzinfo=UTC) + timedelta(days=day - 1, hours=hour, minutes=minute)


def test_the_query_uses_dayofweek_and_hourofday_on_now():
    assert "dayofweek(now())" in QUERY and "hourofday(now())" in QUERY
    assert "ago(" in QUERY  # the look-back window is still the variable
    assert "ago(${var.missing_write_window_hours}h)" in QUERY


def test_the_raw_write_count_is_kept():
    assert "summarize WriteCount = count()" in QUERY
    # The quiet window filters after the count, so the count itself is untouched.
    assert QUERY.index("summarize WriteCount = count()") < QUERY.index("dayofweek(now())")
    assert 'metric_measure_column   = "WriteCount"' in ALERT
    assert 'operator                = "LessThan"' in ALERT and "threshold               = 1" in ALERT
    assert "iff(" not in QUERY and "case(" not in QUERY  # the count is never rewritten


def test_the_quiet_window_runs_saturday_midnight_to_monday_1800_utc():
    # 2026-10-26 is a Monday; 10-30 Friday; 10-31 Saturday; 11-01 Sunday; 11-02 Monday.
    assert _utc(26, 0).isoweekday() == 1 and _utc(31, 0).isoweekday() == 6
    assert _utc(32, 0).isoweekday() == 7 and _utc(33, 0).isoweekday() == 1
    # Start edge: Friday 23:59 evaluates; Saturday 00:00 is quiet.
    assert _returns_a_row(_utc(30, 23, 59))
    assert not _returns_a_row(_utc(31, 0))
    # Inside: all of Saturday and Sunday, and Monday until 17:59.
    assert not _returns_a_row(_utc(31, 12))
    assert not _returns_a_row(_utc(31, 23, 59))
    assert not _returns_a_row(_utc(32, 0))
    assert not _returns_a_row(_utc(32, 23, 59))
    assert not _returns_a_row(_utc(33, 0))
    assert not _returns_a_row(_utc(33, 17, 59))
    # End edge (exclusive): Monday 18:00 evaluates again.
    assert _returns_a_row(_utc(33, 18))
    # Business days outside the window evaluate.
    for day in (27, 28, 29, 30):
        for hour in (0, 12, 23):
            assert _returns_a_row(_utc(day, hour))
    assert not _returns_a_row(_utc(26, 12))  # Monday before 18:00 is quiet
    assert _returns_a_row(_utc(26, 18))


def test_the_window_is_expressed_with_literal_edges():
    expression = _suppressed_when_true()
    assert "DayOfWeek == 6" in expression  # Saturday
    assert "DayOfWeek == 0" in expression  # Sunday
    assert "DayOfWeek == 1 and HourOfDay < 18" in expression  # Monday before 18:00, end exclusive


def test_auto_mitigation_is_on():
    assert re.search(r"^\s*auto_mitigation_enabled\s+= true$", ALERT, re.M)
    assert "auto_mitigation_enabled = false" not in ALERT


def test_the_alert_is_still_disabled_by_default():
    variables = (TF / "variables.tf").read_text()
    assert re.search(r"^\s*enabled\s+= var\.alert_enabled$", ALERT, re.M)
    block = variables[variables.index('variable "alert_enabled"') :]
    block = block[: block.index("\n}\n")]
    assert re.search(r"^\s*default\s+= false$", block, re.M)


def test_the_window_variable_bounds_are_unchanged():
    variables = (TF / "variables.tf").read_text()
    block = variables[variables.index('variable "missing_write_window_hours"') :]
    block = block[: block.index("\n}\n")]
    assert re.search(r"default\s+= 26$", block, re.M)
    assert "var.missing_write_window_hours >= 1 && var.missing_write_window_hours <= 48" in block


def test_the_comments_and_readme_state_what_the_alert_proves():
    comments = " ".join(
        re.sub(r"^\s*#\s?", "", line)
        for line in (TF / "monitoring.tf").read_text().splitlines()
        if "#" in line
    )
    for text in (" ".join(comments.split()), README):
        assert "absence of writes" in text.lower() or "ABSENCE of writes".lower() in text.lower()
        assert "suppression, not a recovery" in text
    assert "Sat 00:00 UTC to Mon 18:00 UTC" in README or "Saturday 00:00 UTC to Monday 18:00 UTC" in README
