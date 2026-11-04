"""T-0022: the EODHD evaluation tool, on invented JSON only. Nothing here touches the network or a key."""

import importlib.util
import itertools
import json
import sys
from datetime import date, timedelta
from decimal import Decimal as D
from itertools import pairwise
from pathlib import Path

import pytest

from hio.contracts.rights import Operation, RightsRefused

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
_spec = importlib.util.spec_from_file_location("eodhd_eval", REPO / "tools" / "eodhd_eval.py")
tool = importlib.util.module_from_spec(_spec)
sys.modules["eodhd_eval"] = tool
_spec.loader.exec_module(tool)
MARKER = "invented-value-0123"


@pytest.fixture(autouse=True)
def private_tmp(tmp_path):
    tmp_path.chmod(0o700)


def an(currency, eod_rows, dividends, splits, listed="same"):
    return tool.analyse("X", currency, currency if listed == "same" else listed, eod_rows, dividends, splits)


def symbol_rows(exchange):
    wanted = [s.rsplit(".", 1)[0] for s in tool.ETFS if s.endswith(f".{exchange}")]
    return [{"Code": c, "Currency": "USD" if exchange == "US" else "AUD"} for c in wanted]


def trading_days(start: date, count: int) -> list[date]:
    out, day = [], start
    while len(out) < count:
        if day.weekday() < 5:
            out.append(day)
        day += timedelta(days=1)
    return out


def invented_eod(days, start=100.0, step=0.1, adjust=True):
    rows = []
    for i, day in enumerate(days):
        close = round(start + step * (i % 50), 4)
        rows.append({"date": day.isoformat(), "close": close, "adjusted_close": close if adjust else None})
    return rows


def responder(days, calls):
    def get(request):
        calls.append(request)
        path = request.split("?")[0].split("/")
        kind = path[1]
        if kind == "eod":
            return 200, json.dumps(invented_eod(days)).encode()
        if kind == "exchange-symbol-list":
            return 200, json.dumps(symbol_rows(path[2])).encode()
        return 200, b"[]"

    return get


def gate():
    return tool.make_gate({})


def snapshot(root, days, calls=None):
    return tool.fetch(
        root,
        "s1",
        gate=gate(),
        commit="c" * 40,
        get=responder(days, calls if calls is not None else []),
        pause=0,
    )


# --- rights and refusals


def test_the_record_allows_local_evaluation_and_denies_everything_wider():
    g = gate()
    for op in (
        Operation.FETCH,
        Operation.STORE_RAW,
        Operation.BUILD,
        Operation.STORE_DERIVED,
        Operation.REBUILD,
    ):
        g.authorise(op, [tool.SOURCE_ID])
    g.authorise(Operation.PUBLISH, [tool.SOURCE_ID], "hio_internal")
    for consumer in ("smsf_app", "smsf_trustee_pack", "smsf_auditor", "third_party"):
        with pytest.raises(RightsRefused):
            g.authorise(Operation.PUBLISH, [tool.SOURCE_ID], consumer)
    assert str(g.records[tool.SOURCE_ID].get("agent_context")).startswith(
        "conditional(derived statistics only"
    )
    assert str(g.records[tool.SOURCE_ID].get("quotation_in_documents")) == "deny"


@pytest.mark.parametrize("name", ["CI", "GITHUB_ACTIONS"])
def test_a_ci_host_refuses(name):
    with pytest.raises(RightsRefused, match="external_processing"):
        tool.make_gate({name: "true"}).authorise(Operation.FETCH, [tool.SOURCE_ID])


def test_the_parent_row_stays_refused():
    with pytest.raises(RightsRefused, match="verification is unverified"):
        gate().authorise(Operation.FETCH, ["eodhd"])


def test_a_root_inside_the_repository_refuses():
    with pytest.raises(tool.Stop, match="outside the repository"):
        tool.fetch(REPO / "data" / "x", "s1", gate=gate(), commit="c", get=lambda _r: (200, b"[]"))


@pytest.mark.parametrize("name", ["/tmp/elsewhere", "../escape", "a/b", "", ".", "..", "x" * 41])
def test_an_unsafe_snapshot_name_refuses_before_any_request(tmp_path, name):
    calls = []
    with pytest.raises(tool.Stop, match="snapshot name"):
        tool.fetch(tmp_path, name, gate=gate(), commit="c", get=lambda r: calls.append(r) or (200, b"[]"))
    assert calls == []


def test_a_root_readable_by_others_refuses(tmp_path):
    tmp_path.chmod(0o755)
    with pytest.raises(tool.Stop, match="mode 700"):
        tool.fetch(tmp_path, "s1", gate=gate(), commit="c", get=lambda _r: (200, b"[]"))


def test_a_missing_root_refuses(tmp_path):
    with pytest.raises(tool.Stop, match="existing directory"):
        tool.check_root(tmp_path / "absent")


def test_everything_created_under_the_root_is_private(tmp_path):
    previous = tool.os.umask(0o022)
    try:
        full_run(tmp_path)
    finally:
        tool.os.umask(previous)
    made = [p for p in tmp_path.rglob("*")]
    assert made
    assert [str(p) for p in made if p.stat().st_mode & 0o077] == []


@pytest.mark.parametrize("part", ["raw", "reports", "store", "reference"])
def test_a_linked_workspace_part_refuses_before_any_write(tmp_path, part):
    root, outside = tmp_path / "root", tmp_path / "outside"
    root.mkdir(mode=0o700)
    outside.mkdir(mode=0o700)
    (root / part).symlink_to(outside, target_is_directory=True)
    with pytest.raises(tool.Stop, match="must not be a link"):
        tool.fetch(root, "s1", gate=gate(), commit="c", get=lambda _r: pytest.fail("requested"))
    assert list(outside.iterdir()) == []


def test_a_linked_snapshot_refuses(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o700)
    root = tmp_path / "root"
    (root / "raw").mkdir(parents=True, mode=0o700)
    root.chmod(0o700)
    (root / "raw" / "s1").symlink_to(outside, target_is_directory=True)
    with pytest.raises(tool.Stop, match="stay under raw"):
        tool.fetch(root, "s1", gate=gate(), commit="c", get=lambda _r: pytest.fail("requested"))


def test_an_open_workspace_part_refuses(tmp_path):
    (tmp_path / "reports").mkdir(mode=0o755)
    (tmp_path / "reports").chmod(0o755)
    with pytest.raises(tool.Stop, match="reports must be private"):
        tool.check_root(tmp_path)


@pytest.mark.parametrize("make_link", [tool.os.symlink, tool.os.link])
def test_a_report_file_that_is_a_link_is_replaced_and_the_target_untouched(tmp_path, make_link):
    outside = tmp_path.parent / f"{tmp_path.name}-outside.md"
    outside.write_text("untouched")
    (tmp_path / "reports").mkdir(mode=0o700)
    report = tmp_path / "reports" / "owner-report.md"
    make_link(outside, report)
    full_run(tmp_path)
    assert outside.read_text() == "untouched"
    assert not report.is_symlink()
    assert report.read_text().startswith("# E-0002")
    assert report.stat().st_mode & 0o077 == 0


def test_a_failed_write_leaves_no_temporary_file(tmp_path, monkeypatch):
    monkeypatch.setattr(tool.os, "replace", lambda *_a: (_ for _ in ()).throw(OSError("invented")))
    with pytest.raises(OSError):
        tool.private_write(tmp_path / "x", b"y")
    assert list(tmp_path.iterdir()) == []


def test_an_existing_open_report_becomes_private(tmp_path):
    (tmp_path / "reports").mkdir(mode=0o700)
    existing = tmp_path / "reports" / "owner-report.md"
    existing.write_text("old")
    existing.chmod(0o644)
    full_run(tmp_path)
    assert existing.stat().st_mode & 0o077 == 0
    assert existing.read_text().startswith("# E-0002")


def test_a_snapshot_is_never_overwritten(tmp_path):
    days = trading_days(date(2020, 1, 6), 10)
    snapshot(tmp_path, days)
    calls = []
    with pytest.raises(tool.Stop, match="already exists"):
        snapshot(tmp_path, days, calls)
    assert calls == []


def test_the_key_is_never_recorded(tmp_path):
    def get(request):
        assert MARKER not in request  # the getter adds the key, so the tool never holds it in a request
        return 200, b"[]"

    manifest = tool.fetch(tmp_path, "s1", gate=gate(), commit="c", get=get, pause=0)
    assert MARKER not in json.dumps(manifest)
    assert "api_token" not in json.dumps(manifest)


def test_the_real_getter_adds_the_key_only_to_the_outgoing_url(monkeypatch):
    seen = {}

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return b"[]"

    def fake(request, timeout=None):
        del timeout
        seen["url"] = request.full_url
        return Response()

    monkeypatch.setattr(tool.urllib.request, "urlopen", fake)
    assert tool.http_getter(MARKER)("/eod/SPY.US?fmt=json") == (200, b"[]")
    assert MARKER in seen["url"]


@pytest.mark.parametrize("answer, why", [((403, b""), "HTTP 403"), ((200, b"<html>"), "not JSON")])
def test_the_first_surprise_stops_and_keeps_what_it_has(tmp_path, answer, why):
    calls = []

    def get(request):
        calls.append(request)
        return answer if len(calls) == 2 else (200, b"[]")

    manifest = tool.fetch(tmp_path, "s1", gate=gate(), commit="c", get=get, pause=0)
    assert why in manifest["stopped"] and len(manifest["files"]) == 1 and len(calls) == 2
    with pytest.raises(tool.Stop, match="stopped early"):
        tool.load_snapshot(tmp_path, "s1")


def test_tampered_bytes_stop(tmp_path):
    days = trading_days(date(2020, 1, 6), 10)
    manifest = snapshot(tmp_path, days)
    (tmp_path / manifest["files"][0]["path"]).write_bytes(b"[]")
    with pytest.raises(tool.Stop, match="don't match"):
        tool.load_snapshot(tmp_path, "s1")


def test_a_missing_vault_name_stops(tmp_path):
    with pytest.raises(tool.Stop, match="no vault name"):
        tool.vault_key(tmp_path)


def test_a_vault_failure_stops_and_shows_nothing_from_az(tmp_path, monkeypatch):
    (tmp_path / "vault-name").write_text("invented-vault")
    done = tool.subprocess.CompletedProcess([], 1, stdout="", stderr="provider text")
    monkeypatch.setattr(tool.subprocess, "run", lambda *_a, **_k: done)
    with pytest.raises(tool.Stop) as caught:
        tool.vault_key(tmp_path)
    assert "provider text" not in str(caught.value)


# --- events and return accounting


DAYS = trading_days(date(2020, 1, 6), 5)


def eod(*closes, adjusted=None):
    return [
        {"date": d.isoformat(), "close": D(str(c)), "adjusted_close": D(str(adjusted[i] if adjusted else c))}
        for i, (d, c) in enumerate(zip(DAYS, closes, strict=False))
    ]


def div(day, amount, currency="USD", **extra):
    return {
        "date": day.isoformat(),
        "unadjustedValue": D(str(amount)),
        "value": D(str(amount)),
        "currency": currency,
        **extra,
    }


def test_a_distribution_enters_on_its_ex_date_from_the_unadjusted_amount():
    s = an("USD", eod(100, 99), [div(DAYS[1], 2)], [])
    assert s.periods[0].total_return == D("0.01")
    assert s.qualified["Q2"] is True


def test_a_split_alone_gives_no_return_and_the_adjusted_series_agrees():
    s = an(
        "USD",
        eod(100, 50, adjusted=[50, 50]),
        [],
        [{"date": DAYS[1].isoformat(), "split": "2.000000/1.000000"}],
    )
    assert s.periods[0].total_return == 0
    assert s.qualified["Q3"] is True


def test_a_split_adjusted_value_is_counted_and_the_paid_amount_used():
    rec = {**div(DAYS[1], 2), "value": D(1)}
    s = an("USD", eod(100, 100), [rec], [])
    assert s.profile["counts"]["distributions_split_adjusted_value_differs"] == 1
    assert s.periods[0].income_return == D("0.02")


def test_a_missing_paid_amount_fails_q2_and_is_never_guessed():
    s = an("USD", eod(100, 100), [{"date": DAYS[1].isoformat(), "value": D(2), "currency": "USD"}], [])
    assert s.qualified["Q2"] is False
    assert s.profile["counts"]["distributions_missing_unadjusted"] == 1
    assert s.periods[0].income_return == 0


def test_another_currency_fails_q2():
    s = an("AUD", eod(100, 100), [div(DAYS[1], 2, "USD")], [])
    assert s.qualified["Q2"] is False
    assert s.profile["counts"]["distributions_other_currency"] == 1


def test_an_unparseable_split_fails_q2():
    s = an("USD", eod(100, 100), [], [{"date": DAYS[1].isoformat(), "split": "two for one"}])
    assert s.qualified["Q2"] is False


def test_an_action_on_an_unobserved_day_moves_forward_and_is_counted():
    rows = [eod(100, 100, 100)[0], eod(100, 100, 100)[2]]  # the middle day has no price
    s = an("USD", rows, [div(DAYS[1], 1)], [])
    assert s.periods[0].end == DAYS[2]
    assert s.periods[0].income_return == D("0.01")
    assert s.profile["counts"]["actions_moved_to_next_day"] == 1


def test_an_action_after_the_last_close_is_counted_not_used():
    s = an("USD", eod(100, 100), [div(DAYS[4], 1)], [])
    assert s.profile["counts"]["actions_after_the_last_close"] == 1


def test_a_missing_payment_date_is_counted():
    s = an("USD", eod(100, 100), [div(DAYS[1], 1, paymentDate=None)], [])
    assert s.profile["counts"]["distributions_missing_paymentDate"] == 1


@pytest.mark.parametrize(
    "rows, field",
    [
        ([{"date": "2020-01-06", "close": D(1)}, {"date": "2020-01-06", "close": D(1)}], "duplicate_dates"),
        ([{"date": "2020-01-07", "close": D(1)}, {"date": "2020-01-06", "close": D(1)}], "unordered_dates"),
        (
            [{"date": "2020-01-06", "close": D(0)}, {"date": "2020-01-07", "close": D(1)}],
            "non_positive_closes",
        ),
        ([{"date": "2020-01-06", "close": D(1)}, {"date": "2020-02-06", "close": D(1)}], "gaps_over_7_days"),
    ],
)
def test_bad_series_fail_q1_and_nothing_is_built(rows, field):
    s = an("USD", rows, [], [])
    assert s.qualified == {"Q1": False, "Q2": False, "Q3": False}
    assert s.profile["counts"][field] == 1 and s.periods == []


def test_an_adjusted_close_that_disagrees_fails_the_internal_check():
    s = an("USD", eod(100, 100, 100, 100, 100, adjusted=[100, 101, 102, 103, 104]), [], [])
    assert s.qualified["Q3"] is False


def test_a_period_without_an_adjusted_close_counts_against_q3():
    rows = eod(100, 100, 100, 100)
    for row in rows[1:3]:
        row["adjusted_close"] = None
    s = an("USD", rows, [], [])
    assert s.qualified["Q3"] is False
    assert s.profile["counts"]["internal_periods_without_adjusted"] == 3


@pytest.mark.parametrize("listed", ["EUR", None])
def test_a_wrong_or_unknown_quote_currency_fails_q1(listed):
    s = an("USD", eod(100, 100), [], [], listed=listed)
    assert s.qualified == {"Q1": False, "Q2": False, "Q3": False}
    assert s.periods == []


def test_the_quote_currency_comes_from_the_listing_and_ambiguity_is_unknown():
    assert tool.quote_currency([{"Code": "SPY", "Currency": "USD"}], "SPY.US") == "USD"
    assert tool.quote_currency([{"Code": "OTHER", "Currency": "USD"}], "SPY.US") is None
    both = [{"Code": "SPY", "Currency": "USD"}, {"Code": "SPY", "Currency": "EUR"}]
    assert tool.quote_currency(both, "SPY.US") is None


def test_a_reference_amount_is_compared_at_the_vendors_decimals(tmp_path):
    write_reference(tmp_path, "X", ["2020-01-07,0.607346"])
    assert (
        tool.check_reference(tmp_path, "X", [{"date": "2020-01-07", "unadjustedValue": D("0.60735")}])[
            "matched"
        ]
        == 1
    )
    other = tool.check_reference(tmp_path, "X", [{"date": "2020-01-07", "unadjustedValue": D("0.5")}])
    assert other["amount_differs"] == 1


def test_the_owner_report_alone_shows_a_differing_amount(tmp_path):
    write_reference(tmp_path, "BGBL.AU", ["2020-01-07,1.25"])
    lines = tool.reference_detail(tmp_path, "BGBL.AU", [{"date": "2020-01-07", "unadjustedValue": D("1.1")}])
    assert "vendor 1.1, issuer 1.25" in lines[0]
    assert "1.25" in tool.render_owner_report(None, lines)


def test_the_empty_series_fails():
    assert an("USD", [], [], []).qualified["Q1"] is False


def test_snapshot_changes_are_counted(tmp_path):
    days = trading_days(date(2020, 1, 6), 10)
    tool.fetch(tmp_path, "s1", gate=gate(), commit="c", get=responder(days, []), pause=0)
    second = responder(days[:-1], [])
    tool.fetch(tmp_path, "s2", gate=gate(), commit="c", get=second, pause=0)
    changes = tool.compare_snapshots(
        tmp_path, tool.load_snapshot(tmp_path, "s1"), tool.load_snapshot(tmp_path, "s2")
    )
    assert changes["SPY.US"]["closes_removed"] == 1
    assert changes["SPY.US"]["closes_changed"] == 0


def test_a_factor_style_difference_is_explained_and_counted():
    # P 100 to 90 with 2 paid: reinvested TR is -8.00%; a factor adjustment gives 90 / 98 - 1, about -8.16%.
    adjusted = [D("98"), D("90")]
    s = an("USD", eod(100, 90, adjusted=adjusted), [div(DAYS[1], 2)], [])
    counts = s.profile["counts"]
    assert counts["internal_differences_on_action_dates"] == 1
    assert counts["internal_differences_explained_by_factor_formula"] == 1
    assert s.periods[0].total_return == D("-0.08")


def test_a_difference_off_an_action_date_is_not_explained():
    s = an("USD", eod(100, 100, adjusted=[100, 101]), [], [])
    assert s.profile["counts"]["internal_differences_off_action_dates"] == 1
    assert not s.profile["counts"]["internal_differences_explained_by_factor_formula"]


def write_reference(root, symbol, rows):
    (root / "reference").mkdir(exist_ok=True)
    lines = ["ex_date,amount", *rows]
    (root / "reference" / f"{symbol}.csv").write_text("\n".join(lines) + "\n")


def test_the_reference_check_counts_each_outcome(tmp_path):
    write_reference(tmp_path, "X", ["2020-01-07,1.00", "2020-01-08,2.00", "2020-01-09,3.00"])
    vendor = [
        {"date": "2020-01-07", "unadjustedValue": D("1.00")},
        {"date": "2020-01-08", "unadjustedValue": D("2.50")},
        {"date": "2020-01-10", "unadjustedValue": D("4.00")},
    ]
    assert tool.check_reference(tmp_path, "X", vendor) == {
        "issuer_rows": 3,
        "matched": 1,
        "amount_differs": 1,
        "missing_from_vendor": 1,
        "only_in_vendor": 1,
    }


def test_no_reference_file_is_not_a_pass(tmp_path):
    assert tool.check_reference(tmp_path, "X", []) is None


# --- end to end, on invented data


def full_run(tmp_path):
    days = trading_days(date(2006, 1, 2), 5400)
    snapshot(tmp_path, days)
    return tool.run(tmp_path, "s1", gate=gate(), code={"commit": "c" * 40, "lock_sha256": "l" * 64})


def test_end_to_end_the_reader_and_comparison_run_on_invented_data(tmp_path):
    summary = full_run(tmp_path)
    assert summary["comparison_ran"] is True
    assert set(summary["releases"]) == {"equity", "treasury", "cash"}
    assert summary["windows_available"]["2008"] is True
    assert summary["independent_reference"]["SPY.US"].startswith("not read")
    assert (tmp_path / "reports" / "owner-report.md").read_text().startswith("# E-0002: for the owner only")
    values = json.loads((tmp_path / "reports" / "owner-values.json").read_text())
    assert set(values["windows"]["full"]["allocations"]) == set(tool.ALLOCATIONS)
    assert set(values["bootstrap_treasury_minus_cash"]) == {"12", "6", "24"}


def test_a_named_window_counts_its_last_month_and_the_open_window_does_not(tmp_path):
    full_run(tmp_path)
    values = json.loads((tmp_path / "reports" / "owner-values.json").read_text())
    days = trading_days(date(2006, 1, 2), 5400)
    panel = tool.fa.align(
        {
            s: [tool.fa.Interval(a, b, D("0")) for a, b in itertools.pairwise(days)]
            for s in ("equity", "treasury", "cash")
        }
    )
    part = tool.fa.window(panel, date(2019, 12, 31), date(2020, 3, 31))
    assert tool.describe(part, tool.ALLOCATIONS["100_equity"], closed=True)["volatility_monthly"] == 0
    assert values["windows"]["q1_2020"]["available"] is True
    assert tool.WINDOWS["from_2020"][0] == date(2019, 12, 31)


def _panel(days, returns):
    series = {
        name: [
            tool.fa.Interval(a, b, D(str(r if name == "equity" else 0)))
            for (a, b), r in zip(pairwise(days), returns, strict=True)
        ]
        for name in ("equity", "treasury", "cash")
    }
    return tool.fa.align(series)


def test_a_truncated_named_window_leaves_out_its_partial_last_month():
    # Reviewer's case: flat to the end of May 2008, then a 50% rise to 16 June, with the data stopping there.
    days = [date(2007, 12, 31), date(2008, 1, 31), date(2008, 2, 29), date(2008, 3, 31)]
    days += [date(2008, 4, 30), date(2008, 5, 30), date(2008, 6, 16)]
    panel = _panel(days, [0, 0, 0, 0, 0, 0.5])
    window = tool.compare_windows_only(panel)["2008"]
    equity = window["allocations"]["100_equity"]
    assert equity["volatility_monthly"] == 0
    a = window["dependence"]["sleeves"].index("equity")
    assert window["dependence"]["monthly"]["covariance"][a][a] == 0


def test_a_window_the_data_reaches_counts_its_last_month():
    days = [date(2019, 12, 31), date(2020, 1, 31), date(2020, 2, 28), date(2020, 3, 31), date(2020, 4, 30)]
    panel = _panel(days, [0, 0, -0.3, 0])
    equity = tool.compare_windows_only(panel)["q1_2020"]["allocations"]["100_equity"]
    assert equity["volatility_monthly"] > 0


def test_the_summary_for_agents_holds_no_value(tmp_path):
    summary = full_run(tmp_path)
    text = json.dumps(summary)
    values = (tmp_path / "reports" / "owner-values.json").read_text()
    wealth = json.loads(values)["windows"]["full"]["allocations"]["100_equity"]["final_wealth"]
    assert f"{wealth}"[:6] not in text
    for word in ("final_wealth", "volatility", "correlation", "adjusted_close", "max_drawdown"):
        assert word not in text


def test_the_comparison_does_not_run_if_a_sleeve_fails(tmp_path):
    days = trading_days(date(2006, 1, 2), 300)

    def get(request):
        path = request.split("?")[0].split("/")
        if path[1] == "eod" and path[2] == "IEF.US":
            return 200, json.dumps(invented_eod(days, adjust=False)).encode()
        return responder(days, [])(request)

    tool.fetch(tmp_path, "s1", gate=gate(), commit="c", get=get, pause=0)
    summary = tool.run(tmp_path, "s1", gate=gate(), code={"commit": "c", "lock_sha256": "l"})
    assert summary["comparison_ran"] is False
    assert "didn't run" in (tmp_path / "reports" / "owner-report.md").read_text()
    assert not (tmp_path / "reports" / "owner-values.json").exists()
