"""T-0022: the EODHD evaluation tool, on invented JSON only. Nothing here touches the network or a key."""

import importlib.util
import json
import sys
from datetime import date, timedelta
from decimal import Decimal as D
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
    assert str(g.records[tool.SOURCE_ID].get("agent_context")) == "deny"
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
    s = tool.analyse("X", "USD", eod(100, 99), [div(DAYS[1], 2)], [])
    assert s.periods[0].total_return == D("0.01")
    assert s.qualified["Q2"] is True


def test_a_split_alone_gives_no_return_and_the_adjusted_series_agrees():
    s = tool.analyse(
        "X",
        "USD",
        eod(100, 50, adjusted=[50, 50]),
        [],
        [{"date": DAYS[1].isoformat(), "split": "2.000000/1.000000"}],
    )
    assert s.periods[0].total_return == 0
    assert s.qualified["Q3"] is True


def test_a_split_adjusted_value_is_counted_and_the_paid_amount_used():
    rec = {**div(DAYS[1], 2), "value": D(1)}
    s = tool.analyse("X", "USD", eod(100, 100), [rec], [])
    assert s.profile["counts"]["distributions_split_adjusted_value_differs"] == 1
    assert s.periods[0].income_return == D("0.02")


def test_a_missing_paid_amount_fails_q2_and_is_never_guessed():
    s = tool.analyse(
        "X", "USD", eod(100, 100), [{"date": DAYS[1].isoformat(), "value": D(2), "currency": "USD"}], []
    )
    assert s.qualified["Q2"] is False
    assert s.profile["counts"]["distributions_missing_unadjusted"] == 1
    assert s.periods[0].income_return == 0


def test_another_currency_fails_q2():
    s = tool.analyse("X", "AUD", eod(100, 100), [div(DAYS[1], 2, "USD")], [])
    assert s.qualified["Q2"] is False
    assert s.profile["counts"]["distributions_other_currency"] == 1


def test_an_unparseable_split_fails_q2():
    s = tool.analyse("X", "USD", eod(100, 100), [], [{"date": DAYS[1].isoformat(), "split": "two for one"}])
    assert s.qualified["Q2"] is False


def test_an_action_on_an_unobserved_day_moves_forward_and_is_counted():
    rows = [eod(100, 100, 100)[0], eod(100, 100, 100)[2]]  # the middle day has no price
    s = tool.analyse("X", "USD", rows, [div(DAYS[1], 1)], [])
    assert s.periods[0].end == DAYS[2]
    assert s.periods[0].income_return == D("0.01")
    assert s.profile["counts"]["actions_moved_to_next_day"] == 1


def test_an_action_after_the_last_close_is_counted_not_used():
    s = tool.analyse("X", "USD", eod(100, 100), [div(DAYS[4], 1)], [])
    assert s.profile["counts"]["actions_after_the_last_close"] == 1


def test_a_missing_payment_date_is_counted():
    s = tool.analyse("X", "USD", eod(100, 100), [div(DAYS[1], 1, paymentDate=None)], [])
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
    s = tool.analyse("X", "USD", rows, [], [])
    assert s.qualified == {"Q1": False, "Q2": False, "Q3": False}
    assert s.profile["counts"][field] == 1 and s.periods == []


def test_an_adjusted_close_that_disagrees_fails_the_internal_check():
    s = tool.analyse("X", "USD", eod(100, 100, 100, 100, 100, adjusted=[100, 101, 102, 103, 104]), [], [])
    assert s.qualified["Q3"] is False


def test_the_empty_series_fails():
    assert tool.analyse("X", "USD", [], [], []).qualified["Q1"] is False


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
    s = tool.analyse("X", "USD", eod(100, 90, adjusted=adjusted), [div(DAYS[1], 2)], [])
    counts = s.profile["counts"]
    assert counts["internal_differences_on_action_dates"] == 1
    assert counts["internal_differences_explained_by_factor_formula"] == 1
    assert s.periods[0].total_return == D("-0.08")


def test_a_difference_off_an_action_date_is_not_explained():
    s = tool.analyse("X", "USD", eod(100, 100, adjusted=[100, 101]), [], [])
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
