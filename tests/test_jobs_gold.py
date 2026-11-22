"""The gold planner and runner (OD-0233): `hio.jobs.gold` and `tools/gold_build.py`. Invented data only."""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import importlib
import importlib.util
import json
import re
import sys
import types
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from hio.contracts import gold as contract
from hio.jobs import gold as jobs
from hio.models.panels import build_panel
from hio.portfolio.paths import build_portfolio_path

if importlib.util.find_spec("hio.models.risk") is None:  # pragma: no cover
    # The real calculations are written by another task (R2). Until they are on this tree, a placeholder
    # module lets `tools/gold_build.py` import; no test here calls it (the tests use the stand-ins below).
    def _not_written(*_args, **_kwargs):
        raise NotImplementedError("hio.models.risk is not on this tree yet")

    _placeholder = types.ModuleType("hio.models.risk")
    _placeholder.build_covariance = _not_written
    _placeholder.build_risk_contribution = _not_written
    sys.modules["hio.models.risk"] = _placeholder
risk_module = importlib.import_module("hio.models.risk")

REPO = Path(__file__).resolve().parent.parent
ENV = {"numpy": "9.9.9", "python": "3.13"}
ENV_B = {"numpy": "9.9.10", "python": "3.13"}


def _window_ends(panel_tables: dict) -> list[str]:
    return sorted({r["period_end"] for r in panel_tables["fact_panel_return"]})


def stand_in_covariance(spec, panel_tables, covariance_build_id):
    """A simple stand-in for `build_covariance`: one `full` window and constant, valid float rows."""
    assert spec["kind"] == "covariance"
    members = [
        r["member_code"] for r in sorted(panel_tables["bridge_panel_member"], key=lambda r: r["column_order"])
    ]
    ends = _window_ends(panel_tables)
    one = contract.float_text
    return {
        "dim_window": [
            {
                "covariance_build_id": covariance_build_id,
                "window_id": "full",
                "window_kind": "full",
                "first_period_end": ends[0],
                "last_period_end": ends[-1],
                "n_obs": str(len(ends)),
            }
        ],
        "fact_covariance": [
            {
                "covariance_build_id": covariance_build_id,
                "window_id": "full",
                "member_i": i,
                "member_j": j,
                "covariance": one(0.0004 if i == j else 0.0001),
                "correlation": one(1.0 if i == j else 0.25),
            }
            for i in members
            for j in members
        ],
        "fact_volatility": [
            {
                "covariance_build_id": covariance_build_id,
                "window_id": "full",
                "member_code": m,
                "volatility": one(0.02),
            }
            for m in members
        ],
    }


def stand_in_risk(spec, covariance_tables, portfolio_tables, risk_build_id):
    """A simple stand-in for `build_risk_contribution`: constant, valid float rows for each window."""
    assert spec["kind"] == "risk_contribution"
    one = contract.float_text
    windows = [r["window_id"] for r in covariance_tables["dim_window"]]
    weights = {
        r["member_code"]: float(r["target_weight"]) for r in portfolio_tables["fact_target_allocation"]
    }
    return {
        "fact_portfolio_risk": [
            {
                "risk_build_id": risk_build_id,
                "window_id": window,
                "portfolio_variance": one(0.0004),
                "portfolio_volatility": one(0.02),
                "diversification_ratio": one(1.2),
                "euler_relative_gap": one(0.0),
            }
            for window in windows
        ],
        "fact_risk_contribution": [
            {
                "risk_build_id": risk_build_id,
                "window_id": window,
                "member_code": member,
                "weight": one(weight),
                "marginal_contribution": one(0.01),
                "component_contribution": one(weight * 0.01),
                "percentage_contribution": one(weight),
            }
            for window in windows
            for member, weight in weights.items()
        ],
    }


# The real panel and portfolio calculations and stand-ins for the two float kinds.
BUILDERS = {
    "panel": build_panel,
    "portfolio_path": build_portfolio_path,
    "covariance": stand_in_covariance,
    "risk_contribution": stand_in_risk,
}


def _with_builders(function):
    def call(*positional, commit, builders=BUILDERS, environment=ENV):
        return function(*positional, commit=commit, builders=builders, environment=environment)

    call.__name__ = function.__name__
    return call


# The planner and runner with the calculations passed in, as `tools/gold_build.py` does.
gold = SimpleNamespace(
    plan=_with_builders(jobs.plan),
    run=_with_builders(jobs.run),
    verify=_with_builders(jobs.verify),
    Node=jobs.Node,
    Plan=jobs.Plan,
)
_spec = importlib.util.spec_from_file_location("gold_build", REPO / "tools" / "gold_build.py")
gold_build = importlib.util.module_from_spec(_spec)
sys.modules["gold_build"] = gold_build
_spec.loader.exec_module(gold_build)

COMMIT = "c" * 40
BOUNDS = [
    "2024-01-31",
    "2024-02-15",
    "2024-02-29",
    "2024-03-15",
    "2024-03-29",
    "2024-04-15",
    "2024-04-30",
]
EQUITY_RETURNS = ["0.0113", "-0.0051", "0.0027", "0.0049", "-0.0013", "0.0031"]
EQUITY_ALT_RETURNS = ["0.0213", "-0.0151", "0.0127", "0.0149", "-0.0113", "0.0131"]
BONDS_RETURNS = ["0.0021", "0.0017", "-0.0023", "0.0037", "0.0007", "0.0011"]
EQUITY_BUILD, BONDS_BUILD, ALT_BUILD = "a" * 16, "b" * 16, "c" * 16
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
ALL_RETURNS = {*EQUITY_RETURNS, *EQUITY_ALT_RETURNS, *BONDS_RETURNS}


def contiguous(returns: list[str], bounds: list[str] = BOUNDS) -> list[tuple[str, str, str]]:
    return [(s, e, r) for (s, e), r in zip(pairwise(bounds), returns, strict=True)]


def make_series(
    store: Path,
    factor_id: str,
    build_id: str,
    rows: list[tuple[str, str, str]],
    *,
    series_class: str = "total_return",
    numeraire: str = "AUD",
) -> dict[str, str]:
    """An invented factor build (contract §4) and its lock pin."""
    directory = store / factor_id / "0.1.0" / build_id
    directory.mkdir(parents=True)
    if series_class == "total_return":
        lines = ["period_start,period_end,total_return", *(f"{s},{e},{r}" for s, e, r in rows)]
    else:
        lines = [
            "period_start,period_end,asset_return,cash_return,excess_return",
            *(f"{s},{e},{r},0.0001,0.0002" for s, e, r in rows),
        ]
    data = ("\n".join(lines) + "\n").encode()
    (directory / "series.csv").write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    record = {
        "factor_id": factor_id,
        "spec_version": "0.1.0",
        "build_id": build_id,
        "series_class": series_class,
        "numeraire": numeraire,
        "series_sha256": digest,
    }
    (directory / "build.json").write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    return {"spec_version": "0.1.0", "build_id": build_id, "series_sha256": digest}


def write_yaml(path: Path, document: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(document, sort_keys=False))
    return path


def write_lock(path: Path, pins: dict[str, dict[str, str]]) -> Path:
    identity = {"name": "demo-lock", "version": "0.1.0", "status": "proposed"}
    return write_yaml(path, {"identity": identity, "factor_series": pins})


def panel_document(name: str = "demo") -> dict:
    return {
        "identity": {"name": name, "version": "0.1.0", "status": "proposed"},
        "kind": "panel",
        "frequency": "monthly",
        "alignment": "common_boundaries",
        "incomplete_periods": "exclude",
        "members": {"equity": "test.equity", "bonds": "test.bonds"},
    }


def portfolio_document(panel: str = "demo", weights: dict[str, str] | None = None) -> dict:
    return {
        "identity": {"name": "demo-60-40", "version": "0.1.0", "status": "proposed"},
        "kind": "portfolio_path",
        "panel": panel,
        "rebalance": "month_end",
        "weights": weights or {"equity": "0.60", "bonds": "0.40"},
    }


def covariance_document(panel: str = "demo", name: str = "demo-cov", trailing: int | None = None) -> dict:
    return {
        "identity": {"name": name, "version": "0.1.0", "status": "proposed"},
        "kind": "covariance",
        "panel": panel,
        "estimator": "sample",
        "ddof": 1,
        "annualisation": 12,
        "trailing_months": trailing,
    }


def risk_document(portfolio: str = "demo-60-40", covariance: str = "demo-cov") -> dict:
    return {
        "identity": {"name": "demo-risk", "version": "0.1.0", "status": "proposed"},
        "kind": "risk_contribution",
        "portfolio": portfolio,
        "covariance": covariance,
    }


@dataclass
class World:
    store: Path
    lock: Path
    panel: Path
    portfolio: Path
    gold: Path
    pins: dict[str, dict[str, str]]
    covariance: Path
    risk: Path


@pytest.fixture
def w(tmp_path: Path) -> World:
    store = tmp_path / "factors"
    pins = {
        "test.equity": make_series(store, "test.equity", EQUITY_BUILD, contiguous(EQUITY_RETURNS)),
        "test.bonds": make_series(store, "test.bonds", BONDS_BUILD, contiguous(BONDS_RETURNS)),
    }
    specs = tmp_path / "specs" / "gold"
    return World(
        store=store,
        lock=write_lock(specs / "locks" / "demo.yaml", pins),
        panel=write_yaml(specs / "panels" / "demo.yaml", panel_document()),
        portfolio=write_yaml(specs / "portfolios" / "demo-60-40.yaml", portfolio_document()),
        gold=tmp_path / "gold",
        pins=pins,
        covariance=write_yaml(specs / "covariances" / "demo-cov.yaml", covariance_document()),
        risk=write_yaml(specs / "risk" / "demo-risk.yaml", risk_document()),
    )


def args(w: World, target: Path, *, lock: Path | None = None, root: Path | None = None) -> tuple:
    return (target, lock or w.lock, w.store, root or w.gold)


def snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    return {
        p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def expected_panel_recipe(w: World, pins: dict[str, dict[str, str]], commit: str = COMMIT) -> dict:
    spec = contract.read_panel_spec(w.panel)
    parents = []
    for code, factor_id in sorted(spec["members"].items()):
        pin = pins[factor_id]
        series = contract.read_factor_series(
            w.store, factor_id, pin["spec_version"], pin["build_id"], series_sha256=pin["series_sha256"]
        )
        parents.append(series.parent(code))
    parameters = {key: spec[key] for key in ("frequency", "alignment", "incomplete_periods", "members")}
    ref = {"name": spec["name"], "version": spec["version"], "sha256": spec["sha256"]}
    return contract.recipe("panel", ref, parameters, parents, commit)


# --------------------------------------------------------------------------------------
# plan
# --------------------------------------------------------------------------------------


def test_plan_for_a_panel_target(w):
    plan = gold.plan(*args(w, w.panel), commit=COMMIT)
    expected_id = contract.build_id(expected_panel_recipe(w, w.pins))
    assert plan.nodes == (
        gold.Node("factor_series", "test.bonds", BONDS_BUILD, "input", ()),
        gold.Node("factor_series", "test.equity", EQUITY_BUILD, "input", ()),
        gold.Node("panel", "demo", expected_id, "missing", ("test.bonds", "test.equity")),
    )
    assert len(expected_id) == 64
    assert plan.marts == (plan.nodes[2],)


def test_plan_for_a_portfolio_target_is_pending_before_its_panel_exists(w):
    plan = gold.plan(*args(w, w.portfolio), commit=COMMIT)
    panel_id = contract.build_id(expected_panel_recipe(w, w.pins))
    assert [(n.kind, n.name, n.status) for n in plan.nodes] == [
        ("factor_series", "test.bonds", "input"),
        ("factor_series", "test.equity", "input"),
        ("panel", "demo", "missing"),
        ("portfolio_path", "demo-60-40", "pending"),
    ]
    assert plan.nodes[2].build_id == panel_id
    assert plan.nodes[3].build_id is None
    assert plan.nodes[3].parents == ("demo",)
    assert not w.gold.exists()  # planning writes nothing


def test_plan_resolves_the_portfolio_id_once_its_panel_is_built(w):
    gold.run(*args(w, w.panel), commit=COMMIT)
    plan = gold.plan(*args(w, w.portfolio), commit=COMMIT)
    panel, portfolio = plan.nodes[2], plan.nodes[3]
    assert panel.status == "present"
    assert portfolio.status == "missing"
    bundle = contract.open_bundle(w.gold, "panel", panel.build_id)
    spec = contract.read_portfolio_spec(w.portfolio)
    ref = {"name": spec["name"], "version": spec["version"], "sha256": spec["sha256"]}
    parent = {"role": "panel", "kind": "panel", "id": panel.build_id, "payload_sha256": bundle.payload_sha256}
    expected = contract.recipe(
        "portfolio_path",
        ref,
        {"panel": "demo", "rebalance": "month_end", "weights": {"equity": "0.60", "bonds": "0.40"}},
        [parent],
        COMMIT,
    )
    assert portfolio.build_id == contract.build_id(expected)


def test_plan_is_deterministic(w):
    first = gold.plan(*args(w, w.portfolio), commit=COMMIT)
    assert gold.plan(*args(w, w.portfolio), commit=COMMIT) == first


# --------------------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------------------


def test_run_builds_both_and_a_second_run_builds_nothing(w, monkeypatch):
    first = gold.run(*args(w, w.portfolio), commit=COMMIT)
    assert [n.status for n in first.nodes] == ["input", "input", "present", "present"]
    assert all(n.build_id and len(n.build_id) in (16, 64) for n in first.nodes)
    before = snapshot(w.gold)
    assert {p.split("/")[0] for p in before} == {"panel", "portfolio_path"}

    def refuse_to_write(*_a, **_k):
        raise AssertionError("a present bundle was written again")

    monkeypatch.setattr(jobs, "write_bundle", refuse_to_write)
    never = dict.fromkeys(BUILDERS, refuse_to_write)
    second = gold.run(*args(w, w.portfolio), commit=COMMIT, builders=never)
    assert second == first
    assert snapshot(w.gold) == before  # same bytes, same modification times
    assert gold.run(*args(w, w.panel), commit=COMMIT).nodes == first.nodes[:3]


def test_run_for_a_panel_target_builds_only_the_panel(w):
    plan = gold.run(*args(w, w.panel), commit=COMMIT)
    assert [n.kind for n in plan.marts] == ["panel"]
    assert not (w.gold / "portfolio_path").exists()


def test_built_bundle_recipes(w):
    plan = gold.run(*args(w, w.portfolio), commit=COMMIT)
    panel = contract.open_bundle(w.gold, "panel", plan.nodes[2].build_id)
    assert panel.recipe == expected_panel_recipe(w, w.pins)
    portfolio = contract.open_bundle(w.gold, "portfolio_path", plan.nodes[3].build_id)
    assert portfolio.recipe["parameters"] == {
        "panel": "demo",
        "rebalance": "month_end",
        "weights": {"equity": "0.60", "bonds": "0.40"},
    }
    assert portfolio.recipe["parents"] == [
        {"role": "panel", "kind": "panel", "id": panel.build_id, "payload_sha256": panel.payload_sha256}
    ]
    assert portfolio.recipe["code_commit"] == COMMIT


def test_built_tables_equal_the_direct_calculations(w):
    plan = gold.run(*args(w, w.portfolio), commit=COMMIT)
    panel_id, portfolio_id = plan.nodes[2].build_id, plan.nodes[3].build_id
    spec = contract.read_panel_spec(w.panel)
    series = {
        code: contract.read_factor_series(
            w.store,
            factor_id,
            w.pins[factor_id]["spec_version"],
            w.pins[factor_id]["build_id"],
            series_sha256=w.pins[factor_id]["series_sha256"],
        )
        for code, factor_id in spec["members"].items()
    }
    panel_rows = build_panel(spec, series, panel_id)
    panel = contract.open_bundle(w.gold, "panel", panel_id)
    for name in contract.TABLES["panel"]:
        direct = contract.parse_table("panel", name, contract.table_bytes("panel", name, panel_rows[name]))
        assert panel.table(name) == direct
        assert direct  # the invented data does produce rows
    portfolio_rows = build_portfolio_path(
        contract.read_portfolio_spec(w.portfolio),
        {name: panel.table(name) for name in contract.TABLES["panel"]},
        portfolio_id,
    )
    portfolio = contract.open_bundle(w.gold, "portfolio_path", portfolio_id)
    for name in contract.TABLES["portfolio_path"]:
        direct = contract.parse_table(
            "portfolio_path", name, contract.table_bytes("portfolio_path", name, portfolio_rows[name])
        )
        assert portfolio.table(name) == direct
        assert direct


# --------------------------------------------------------------------------------------
# identity: what changes a build_id and what does not
# --------------------------------------------------------------------------------------


def test_changing_one_pin_changes_the_panels_and_the_portfolios_id(w, tmp_path):
    alt = make_series(w.store, "test.equity", ALT_BUILD, contiguous(EQUITY_ALT_RETURNS))
    lock_b = write_lock(tmp_path / "lock-b.yaml", {**w.pins, "test.equity": alt})
    plan_a = gold.run(*args(w, w.portfolio), commit=COMMIT)
    plan_b = gold.run(*args(w, w.portfolio, lock=lock_b, root=tmp_path / "gold-b"), commit=COMMIT)
    assert plan_a.nodes[2].build_id != plan_b.nodes[2].build_id
    assert plan_a.nodes[3].build_id != plan_b.nodes[3].build_id
    assert plan_b.nodes[1].build_id == ALT_BUILD  # the pin is the series node's id
    assert plan_a.nodes[0] == plan_b.nodes[0]  # the unchanged member is the same node


def test_changing_only_the_weights_changes_the_portfolio_id_not_the_panels(w):
    before = gold.run(*args(w, w.portfolio), commit=COMMIT)
    panel_files = snapshot(w.gold / "panel")
    write_yaml(w.portfolio, portfolio_document(weights={"equity": "0.50", "bonds": "0.50"}))
    after = gold.plan(*args(w, w.portfolio), commit=COMMIT)
    assert after.nodes[2] == before.nodes[2]  # same panel id, still present
    assert after.nodes[3].status == "missing"
    assert after.nodes[3].build_id not in (None, before.nodes[3].build_id)
    final = gold.run(*args(w, w.portfolio), commit=COMMIT)
    assert snapshot(w.gold / "panel") == panel_files  # the panel was not rebuilt
    assert final.nodes[3].build_id == after.nodes[3].build_id


def test_a_different_commit_changes_both_ids(w, tmp_path):
    a = gold.run(*args(w, w.portfolio), commit="a" * 40)
    b = gold.run(*args(w, w.portfolio, root=tmp_path / "gold-b"), commit="b" * 40)
    assert a.nodes[2].build_id != b.nodes[2].build_id
    assert a.nodes[3].build_id != b.nodes[3].build_id


def test_a_changed_spec_changes_the_recipe(w):
    first = gold.plan(*args(w, w.panel), commit=COMMIT)
    document = panel_document()
    document["identity"]["version"] = "0.2.0"
    write_yaml(w.panel, document)
    assert gold.plan(*args(w, w.panel), commit=COMMIT).nodes[2].build_id != first.nodes[2].build_id


# --------------------------------------------------------------------------------------
# refusals
# --------------------------------------------------------------------------------------


def test_a_member_with_no_lock_entry_is_refused(w, tmp_path):
    lock = write_lock(tmp_path / "short.yaml", {"test.equity": w.pins["test.equity"]})
    with pytest.raises(ValueError, match=r"no entry for factor 'test\.bonds'"):
        gold.plan(*args(w, w.panel, lock=lock), commit=COMMIT)


def test_a_lock_entry_for_a_series_that_is_not_there_is_refused(w, tmp_path):
    ghost = {**w.pins["test.bonds"], "build_id": "d" * 16}
    lock = write_lock(tmp_path / "ghost.yaml", {**w.pins, "test.bonds": ghost})
    with pytest.raises(ValueError, match=r"test\.bonds"):
        gold.plan(*args(w, w.panel, lock=lock), commit=COMMIT)


def test_a_tampered_series_is_refused(w):
    series = w.store / "test.equity" / "0.1.0" / EQUITY_BUILD / "series.csv"
    series.write_bytes(series.read_bytes().replace(b"0.0113", b"0.0114"))
    with pytest.raises(ValueError, match=r"test\.equity.*sha256 differs"):
        gold.plan(*args(w, w.panel), commit=COMMIT)
    with pytest.raises(ValueError, match="sha256 differs"):
        gold.run(*args(w, w.panel), commit=COMMIT)
    assert not w.gold.exists()


def test_a_wrong_pin_hash_is_refused(w, tmp_path):
    wrong = {**w.pins["test.bonds"], "series_sha256": "0" * 64}
    lock = write_lock(tmp_path / "wrong.yaml", {**w.pins, "test.bonds": wrong})
    with pytest.raises(ValueError, match=r"test\.bonds.*differs"):
        gold.plan(*args(w, w.panel, lock=lock), commit=COMMIT)


def test_a_portfolio_naming_an_unknown_panel_is_refused(w):
    write_yaml(w.portfolio, portfolio_document(panel="nope"))
    with pytest.raises(ValueError, match="unknown panel"):
        gold.plan(*args(w, w.portfolio), commit=COMMIT)


@pytest.mark.parametrize("name", ["../demo", "a/b", ".."])
def test_a_panel_name_that_is_not_a_single_component_is_refused(w, name):
    write_yaml(w.portfolio, portfolio_document(panel=name))
    with pytest.raises(ValueError, match="panel"):
        gold.plan(*args(w, w.portfolio), commit=COMMIT)


def test_a_panel_name_mismatch_is_refused(w):
    write_yaml(w.panel, panel_document(name="other"))
    with pytest.raises(ValueError, match="is named 'other'"):
        gold.plan(*args(w, w.portfolio), commit=COMMIT)


def test_weights_that_do_not_name_the_panels_members_are_refused(w):
    write_yaml(w.portfolio, portfolio_document(weights={"equity": "0.60", "gold": "0.40"}))
    with pytest.raises(ValueError, match="weights name"):
        gold.plan(*args(w, w.portfolio), commit=COMMIT)


def test_members_with_different_numeraires_are_refused(w):
    usd = make_series(w.store, "test.bonds", "d" * 16, contiguous(BONDS_RETURNS), numeraire="USD")
    lock = write_lock(w.lock.parent / "usd.yaml", {**w.pins, "test.bonds": usd})
    with pytest.raises(ValueError, match="numeraire"):
        gold.plan(*args(w, w.panel, lock=lock), commit=COMMIT)


def test_a_portfolio_over_excess_members_is_refused_and_a_panel_is_not(w):
    pins = {
        "test.equity": make_series(
            w.store, "test.equity", "e" * 16, contiguous(EQUITY_RETURNS), series_class="excess"
        ),
        "test.bonds": make_series(
            w.store, "test.bonds", "f" * 16, contiguous(BONDS_RETURNS), series_class="excess"
        ),
    }
    lock = write_lock(w.lock.parent / "excess.yaml", pins)
    with pytest.raises(ValueError, match="total_return"):
        gold.plan(*args(w, w.portfolio, lock=lock), commit=COMMIT)
    assert gold.plan(*args(w, w.panel, lock=lock), commit=COMMIT).nodes[-1].status == "missing"


def test_a_target_that_is_none_of_the_four_kinds_is_refused(w, tmp_path):
    other = write_yaml(tmp_path / "other.yaml", {"kind": "something_else"})
    with pytest.raises(ValueError, match="kind must be"):
        gold.plan(*args(w, other), commit=COMMIT)


@pytest.mark.parametrize("commit", ["", None])
def test_a_missing_commit_is_refused(w, commit):
    with pytest.raises(ValueError, match="commit"):
        gold.plan(*args(w, w.panel), commit=commit)


def test_verify_refuses_a_missing_bundle_and_passes_once_built(w):
    with pytest.raises(ValueError, match="panel demo is missing"):
        gold.verify(*args(w, w.panel), commit=COMMIT)
    with pytest.raises(ValueError, match="pending"):
        gold.verify(*args(w, w.portfolio), commit=COMMIT)
    built = gold.run(*args(w, w.portfolio), commit=COMMIT)
    assert gold.verify(*args(w, w.portfolio), commit=COMMIT) == built
    assert gold.verify(*args(w, w.panel), commit=COMMIT).nodes == built.nodes[:3]


def test_verify_refuses_a_portfolio_whose_own_bundle_is_missing(w):
    gold.run(*args(w, w.panel), commit=COMMIT)
    with pytest.raises(ValueError, match="portfolio_path demo-60-40 is missing"):
        gold.verify(*args(w, w.portfolio), commit=COMMIT)


@pytest.mark.parametrize("command", [gold.plan, gold.run, gold.verify])
def test_a_tampered_existing_panel_bundle_is_refused_not_treated_as_present(w, command):
    plan = gold.run(*args(w, w.panel), commit=COMMIT)
    table = w.gold / "panel" / plan.nodes[2].build_id / "tables" / "fact_panel_return.csv"
    table.write_bytes(table.read_bytes() + b"x\n")
    tampered = snapshot(w.gold)
    with pytest.raises(ValueError, match="does not verify"):
        command(*args(w, w.panel), commit=COMMIT)
    assert snapshot(w.gold) == tampered  # nothing was repaired or overwritten


def test_a_tampered_panel_bundle_refuses_the_portfolio_plan_too(w):
    plan = gold.run(*args(w, w.panel), commit=COMMIT)
    (w.gold / "panel" / plan.nodes[2].build_id / "manifest.json").write_text("{}\n")
    with pytest.raises(ValueError, match="does not verify"):
        gold.plan(*args(w, w.portfolio), commit=COMMIT)


def test_a_tampered_portfolio_bundle_is_refused(w):
    plan = gold.run(*args(w, w.portfolio), commit=COMMIT)
    table = w.gold / "portfolio_path" / plan.nodes[3].build_id / "tables" / "fact_portfolio_return.csv"
    table.write_bytes(table.read_bytes() + b"x\n")
    with pytest.raises(ValueError, match="does not verify"):
        gold.verify(*args(w, w.portfolio), commit=COMMIT)


# --------------------------------------------------------------------------------------
# the covariance and risk kinds (OD-0234, contract §6a)
# --------------------------------------------------------------------------------------

KINDS_IN_ORDER = ["panel", "covariance", "portfolio_path", "risk_contribution"]


def ids(plan: gold.Plan) -> dict[str, str | None]:
    return {n.kind: n.build_id for n in plan.marts}


def statuses(plan: gold.Plan) -> dict[str, str]:
    return {n.kind: n.status for n in plan.marts}


def expected_covariance_recipe(w: World, panel_bundle, environment=ENV, commit: str = COMMIT) -> dict:
    spec = contract.read_covariance_spec(w.covariance)
    parameters = {
        key: spec[key] for key in ("panel", "estimator", "ddof", "annualisation", "trailing_months")
    }
    parent = {
        "role": "panel",
        "kind": "panel",
        "id": panel_bundle.build_id,
        "payload_sha256": panel_bundle.payload_sha256,
    }
    ref = {"name": spec["name"], "version": spec["version"], "sha256": spec["sha256"]}
    return contract.recipe("covariance", ref, parameters, [parent], commit, environment=environment)


def test_plan_for_a_covariance_target_is_pending_before_its_panel_exists(w):
    plan = gold.plan(*args(w, w.covariance), commit=COMMIT)
    assert [(n.kind, n.name, n.status) for n in plan.nodes] == [
        ("factor_series", "test.bonds", "input"),
        ("factor_series", "test.equity", "input"),
        ("panel", "demo", "missing"),
        ("covariance", "demo-cov", "pending"),
    ]
    assert plan.nodes[2].build_id == contract.build_id(expected_panel_recipe(w, w.pins))
    assert plan.nodes[3].build_id is None
    assert plan.nodes[3].parents == ("demo",)
    assert not w.gold.exists()


def test_plan_resolves_the_covariance_id_once_its_panel_is_built(w):
    gold.run(*args(w, w.panel), commit=COMMIT)
    plan = gold.plan(*args(w, w.covariance), commit=COMMIT)
    assert statuses(plan) == {"panel": "present", "covariance": "missing"}
    panel = contract.open_bundle(w.gold, "panel", plan.nodes[2].build_id)
    assert plan.nodes[3].build_id == contract.build_id(expected_covariance_recipe(w, panel))


def test_run_for_a_covariance_target_builds_the_panel_and_the_covariance_only(w):
    plan = gold.run(*args(w, w.covariance), commit=COMMIT)
    assert [n.kind for n in plan.marts] == ["panel", "covariance"]
    assert {n.status for n in plan.marts} == {"present"}
    assert {p.name for p in w.gold.iterdir()} == {"panel", "covariance"}
    panel = contract.open_bundle(w.gold, "panel", ids(plan)["panel"])
    bundle = contract.open_bundle(w.gold, "covariance", ids(plan)["covariance"])
    assert bundle.recipe == expected_covariance_recipe(w, panel)
    assert bundle.recipe["numeric_policy"] == "float64/1"
    assert bundle.recipe["environment"] == ENV
    assert bundle.recipe["parents"] == [
        {"role": "panel", "kind": "panel", "id": panel.build_id, "payload_sha256": panel.payload_sha256}
    ]
    assert set(bundle.recipe["parameters"]) == {
        "panel",
        "estimator",
        "ddof",
        "annualisation",
        "trailing_months",
    }
    # The decimal kinds carry no environment and keep their policy.
    assert "environment" not in panel.recipe and panel.recipe["numeric_policy"] == "decimal-50/1"


def test_plan_for_a_risk_target_is_a_pending_chain(w):
    plan = gold.plan(*args(w, w.risk), commit=COMMIT)
    assert [(n.kind, n.name, n.status) for n in plan.nodes] == [
        ("factor_series", "test.bonds", "input"),
        ("factor_series", "test.equity", "input"),
        ("panel", "demo", "missing"),
        ("covariance", "demo-cov", "pending"),
        ("portfolio_path", "demo-60-40", "pending"),
        ("risk_contribution", "demo-risk", "pending"),
    ]
    assert [n.build_id is None for n in plan.nodes[3:]] == [True, True, True]
    assert plan.nodes[3].parents == ("demo",)
    assert plan.nodes[4].parents == ("demo",)
    assert plan.nodes[5].parents == ("demo-cov", "demo-60-40")
    assert not w.gold.exists()


def test_the_pending_chain_resolves_as_each_parent_is_built(w):
    gold.run(*args(w, w.panel), commit=COMMIT)
    plan = gold.plan(*args(w, w.risk), commit=COMMIT)
    assert statuses(plan) == {
        "panel": "present",
        "covariance": "missing",
        "portfolio_path": "missing",
        "risk_contribution": "pending",
    }
    gold.run(*args(w, w.covariance), commit=COMMIT)
    plan = gold.plan(*args(w, w.risk), commit=COMMIT)
    assert statuses(plan)["covariance"] == "present"
    assert statuses(plan)["risk_contribution"] == "pending" and ids(plan)["risk_contribution"] is None
    gold.run(*args(w, w.portfolio), commit=COMMIT)
    plan = gold.plan(*args(w, w.risk), commit=COMMIT)
    assert statuses(plan) == {**dict.fromkeys(KINDS_IN_ORDER, "present"), "risk_contribution": "missing"}
    assert len(ids(plan)["risk_contribution"]) == 64
    built = gold.run(*args(w, w.risk), commit=COMMIT)
    assert set(statuses(built).values()) == {"present"}
    assert ids(built) == ids(plan)  # the id the plan computed is the id that was built
    assert gold.verify(*args(w, w.risk), commit=COMMIT) == built


def test_run_for_a_risk_target_builds_everything_in_order(w):
    plan = gold.run(*args(w, w.risk), commit=COMMIT)
    assert [n.kind for n in plan.marts] == KINDS_IN_ORDER
    assert {n.status for n in plan.marts} == {"present"}
    assert {p.name for p in w.gold.iterdir()} == set(KINDS_IN_ORDER)
    panel = contract.open_bundle(w.gold, "panel", ids(plan)["panel"])
    covariance = contract.open_bundle(w.gold, "covariance", ids(plan)["covariance"])
    portfolio = contract.open_bundle(w.gold, "portfolio_path", ids(plan)["portfolio_path"])
    risk = contract.open_bundle(w.gold, "risk_contribution", ids(plan)["risk_contribution"])
    assert covariance.recipe["parents"][0]["id"] == panel.build_id == portfolio.recipe["parents"][0]["id"]
    assert risk.recipe["numeric_policy"] == "float64/1"
    assert risk.recipe["environment"] == ENV
    assert risk.recipe["parameters"] == {"portfolio": "demo-60-40", "covariance": "demo-cov"}
    assert risk.recipe["parents"] == [
        {
            "role": "covariance",
            "kind": "covariance",
            "id": covariance.build_id,
            "payload_sha256": covariance.payload_sha256,
        },
        {
            "role": "portfolio",
            "kind": "portfolio_path",
            "id": portfolio.build_id,
            "payload_sha256": portfolio.payload_sha256,
        },
    ]
    assert risk.recipe["code_commit"] == COMMIT
    assert plan.nodes[-1].parents == ("demo-cov", "demo-60-40")


def test_the_builders_are_handed_their_parents_tables_and_their_own_id(w):
    seen: dict[str, tuple] = {}

    def spy(name, function):
        def call(*positional):
            seen[name] = positional
            return function(*positional)

        return call

    builders = {name: spy(name, function) for name, function in BUILDERS.items()}
    plan = jobs.run(*args(w, w.risk), commit=COMMIT, builders=builders, environment=ENV)
    built = ids(plan)
    spec, tables, own_id = seen["covariance"]
    assert (spec["kind"], spec["name"], own_id) == ("covariance", "demo-cov", built["covariance"])
    assert set(tables) == set(contract.TABLES["panel"])
    panel = contract.open_bundle(w.gold, "panel", built["panel"])
    assert tables["fact_panel_return"] == panel.table("fact_panel_return")
    spec, covariance_tables, portfolio_tables, own_id = seen["risk_contribution"]
    assert (spec["kind"], spec["portfolio"], spec["covariance"]) == (
        "risk_contribution",
        "demo-60-40",
        "demo-cov",
    )
    assert own_id == built["risk_contribution"]
    assert set(covariance_tables) == set(contract.TABLES["covariance"])
    assert set(portfolio_tables) == set(contract.TABLES["portfolio_path"])
    covariance = contract.open_bundle(w.gold, "covariance", built["covariance"])
    assert covariance_tables["dim_window"] == covariance.table("dim_window")
    assert {r["covariance_build_id"] for r in covariance_tables["fact_volatility"]} == {built["covariance"]}


def test_a_second_run_builds_nothing_for_the_float_kinds_too(w, monkeypatch):
    first = gold.run(*args(w, w.risk), commit=COMMIT)
    before = snapshot(w.gold)

    def refuse(*_a, **_k):
        raise AssertionError("a present bundle was written or built again")

    monkeypatch.setattr(jobs, "write_bundle", refuse)
    never = dict.fromkeys(BUILDERS, refuse)
    for target in (w.risk, w.covariance, w.portfolio, w.panel):
        again = jobs.run(*args(w, target), commit=COMMIT, builders=never, environment=ENV)
        assert again.nodes == tuple(n for n in first.nodes if n.kind in {m.kind for m in again.nodes})
    assert snapshot(w.gold) == before


def test_a_different_environment_changes_the_float_ids_and_not_the_decimal_ones(w, tmp_path):
    a = gold.run(*args(w, w.risk), commit=COMMIT, environment=ENV)
    b = gold.run(*args(w, w.risk, root=tmp_path / "gold-b"), commit=COMMIT, environment=ENV_B)
    assert ids(a)["panel"] == ids(b)["panel"]
    assert ids(a)["portfolio_path"] == ids(b)["portfolio_path"]
    assert ids(a)["covariance"] != ids(b)["covariance"]
    assert ids(a)["risk_contribution"] != ids(b)["risk_contribution"]
    # In one gold root the decimal bundles stay present and the float ones are new builds.
    after = gold.plan(*args(w, w.risk), commit=COMMIT, environment=ENV_B)
    assert statuses(after) == {
        "panel": "present",
        "covariance": "missing",
        "portfolio_path": "present",
        "risk_contribution": "pending",
    }
    assert ids(after)["covariance"] == ids(b)["covariance"]
    assert gold.plan(*args(w, w.portfolio), commit=COMMIT, environment=ENV_B).nodes[-1].status == "present"


def test_a_python_version_alone_changes_the_float_ids(w):
    other = {**ENV, "python": "3.14"}
    a = gold.plan(*args(w, w.covariance), commit=COMMIT, environment=ENV)
    assert a.nodes[-1].status == "pending"
    gold.run(*args(w, w.panel), commit=COMMIT)
    first = gold.plan(*args(w, w.covariance), commit=COMMIT, environment=ENV).nodes[-1].build_id
    second = gold.plan(*args(w, w.covariance), commit=COMMIT, environment=other).nodes[-1].build_id
    assert first != second


def test_a_changed_lock_pin_changes_all_four_ids(w, tmp_path):
    alt = make_series(w.store, "test.equity", ALT_BUILD, contiguous(EQUITY_ALT_RETURNS))
    lock_b = write_lock(tmp_path / "lock-b.yaml", {**w.pins, "test.equity": alt})
    a = gold.run(*args(w, w.risk), commit=COMMIT)
    b = gold.run(*args(w, w.risk, lock=lock_b, root=tmp_path / "gold-b"), commit=COMMIT)
    assert set(ids(a)) == set(ids(b)) == set(KINDS_IN_ORDER)
    for kind in KINDS_IN_ORDER:
        assert ids(a)[kind] != ids(b)[kind], kind


def test_a_different_commit_changes_the_float_ids_too(w, tmp_path):
    a = gold.run(*args(w, w.risk), commit="a" * 40)
    b = gold.run(*args(w, w.risk, root=tmp_path / "gold-b"), commit="b" * 40)
    for kind in KINDS_IN_ORDER:
        assert ids(a)[kind] != ids(b)[kind], kind


def test_a_changed_covariance_spec_changes_the_covariance_and_risk_ids_only(w):
    before = gold.run(*args(w, w.risk), commit=COMMIT)
    write_yaml(w.covariance, covariance_document(trailing=3))
    after = gold.plan(*args(w, w.risk), commit=COMMIT)
    assert ids(after)["panel"] == ids(before)["panel"]
    assert ids(after)["portfolio_path"] == ids(before)["portfolio_path"]
    assert ids(after)["covariance"] not in (None, ids(before)["covariance"])
    assert statuses(after)["covariance"] == "missing"
    assert statuses(after)["risk_contribution"] == "pending"


def test_existing_panel_and_portfolio_ids_do_not_depend_on_the_target_or_the_environment(w):
    panel_only = gold.plan(*args(w, w.panel), commit=COMMIT, environment=ENV_B)
    portfolio_only = gold.plan(*args(w, w.portfolio), commit=COMMIT, environment=ENV_B)
    assert ids(panel_only)["panel"] == contract.build_id(expected_panel_recipe(w, w.pins))
    risk = gold.run(*args(w, w.risk), commit=COMMIT)
    assert ids(risk)["panel"] == ids(panel_only)["panel"]
    assert gold.plan(*args(w, w.portfolio), commit=COMMIT).nodes[-1].build_id == ids(risk)["portfolio_path"]
    assert ids(portfolio_only)["panel"] == ids(risk)["panel"]
    panel = contract.open_bundle(w.gold, "panel", ids(risk)["panel"])
    portfolio = contract.open_bundle(w.gold, "portfolio_path", ids(risk)["portfolio_path"])
    assert "environment" not in panel.recipe and "environment" not in portfolio.recipe
    assert panel.recipe["numeric_policy"] == portfolio.recipe["numeric_policy"] == "decimal-50/1"


def test_a_risk_whose_covariance_and_portfolio_name_different_panels_is_refused(w):
    other = {**panel_document(name="other")}
    write_yaml(w.panel.parent / "other.yaml", other)
    write_yaml(w.covariance, covariance_document(panel="other"))
    with pytest.raises(ValueError, match=r"built on panel 'other'.*built on 'demo'"):
        gold.plan(*args(w, w.risk), commit=COMMIT)
    with pytest.raises(ValueError, match="built on panel"):
        gold.run(*args(w, w.risk), commit=COMMIT)
    assert not w.gold.exists()
    # Each of the two alone is fine.
    assert gold.plan(*args(w, w.covariance), commit=COMMIT).nodes[-1].name == "demo-cov"
    assert gold.plan(*args(w, w.portfolio), commit=COMMIT).nodes[-1].name == "demo-60-40"


def test_a_risk_whose_two_bundles_name_different_panel_ids_is_refused(w, monkeypatch):
    gold.run(*args(w, w.risk), commit=COMMIT)
    real = jobs.open_bundle

    def forged(root, kind, bid):
        bundle = real(root, kind, bid)
        if kind != "covariance":
            return bundle
        parents = [{**p, "id": "d" * 64} if p["role"] == "panel" else p for p in bundle.recipe["parents"]]
        return dataclasses.replace(bundle, recipe={**bundle.recipe, "parents": parents})

    monkeypatch.setattr(jobs, "open_bundle", forged)
    for command in (gold.plan, gold.run, gold.verify):
        with pytest.raises(ValueError, match="same panel bundle"):
            command(*args(w, w.risk), commit=COMMIT)
    # A covariance or a portfolio target does not look at the other's bundle.
    assert gold.plan(*args(w, w.portfolio), commit=COMMIT).nodes[-1].status == "present"


def test_a_risk_naming_an_unknown_or_misnamed_spec_is_refused(w):
    write_yaml(w.risk, risk_document(covariance="nope"))
    with pytest.raises(ValueError, match="unknown covariance"):
        gold.plan(*args(w, w.risk), commit=COMMIT)
    write_yaml(w.risk, risk_document(portfolio="nope"))
    with pytest.raises(ValueError, match="unknown portfolio"):
        gold.plan(*args(w, w.risk), commit=COMMIT)
    write_yaml(w.risk, risk_document())
    write_yaml(w.covariance, covariance_document(name="other"))
    with pytest.raises(ValueError, match="is named 'other'"):
        gold.plan(*args(w, w.risk), commit=COMMIT)
    write_yaml(w.covariance, covariance_document())
    write_yaml(
        w.portfolio, {**portfolio_document(), "identity": {**portfolio_document()["identity"], "name": "x"}}
    )
    with pytest.raises(ValueError, match="is named 'x'"):
        gold.plan(*args(w, w.risk), commit=COMMIT)


@pytest.mark.parametrize("name", ["../demo", "a/b", ".."])
def test_a_sibling_name_that_is_not_a_single_component_is_refused(w, name):
    write_yaml(w.risk, risk_document(covariance=name))
    with pytest.raises(ValueError, match="covariance"):
        gold.plan(*args(w, w.risk), commit=COMMIT)
    write_yaml(w.risk, risk_document(portfolio=name))
    with pytest.raises(ValueError, match="portfolio"):
        gold.plan(*args(w, w.risk), commit=COMMIT)
    write_yaml(w.covariance, covariance_document(panel=name))
    with pytest.raises(ValueError, match="panel"):
        gold.plan(*args(w, w.covariance), commit=COMMIT)


def test_a_covariance_naming_an_unknown_panel_is_refused(w):
    write_yaml(w.covariance, covariance_document(panel="nope"))
    with pytest.raises(ValueError, match="unknown panel"):
        gold.plan(*args(w, w.covariance), commit=COMMIT)
    write_yaml(w.panel, panel_document(name="other"))
    write_yaml(w.covariance, covariance_document())
    with pytest.raises(ValueError, match="is named 'other'"):
        gold.plan(*args(w, w.covariance), commit=COMMIT)


def test_a_covariance_over_excess_members_is_allowed_and_a_risk_is_not(w):
    pins = {
        "test.equity": make_series(
            w.store, "test.equity", "e" * 16, contiguous(EQUITY_RETURNS), series_class="excess"
        ),
        "test.bonds": make_series(
            w.store, "test.bonds", "f" * 16, contiguous(BONDS_RETURNS), series_class="excess"
        ),
    }
    lock = write_lock(w.lock.parent / "excess.yaml", pins)
    assert gold.plan(*args(w, w.covariance, lock=lock), commit=COMMIT).nodes[-1].status == "pending"
    with pytest.raises(ValueError, match="total_return"):
        gold.plan(*args(w, w.risk, lock=lock), commit=COMMIT)


def test_a_risk_whose_weights_do_not_name_the_panels_members_is_refused(w):
    write_yaml(w.portfolio, portfolio_document(weights={"equity": "0.60", "gold": "0.40"}))
    with pytest.raises(ValueError, match="weights name"):
        gold.plan(*args(w, w.risk), commit=COMMIT)


def test_a_covariance_with_a_member_with_no_lock_entry_is_refused(w, tmp_path):
    lock = write_lock(tmp_path / "short.yaml", {"test.equity": w.pins["test.equity"]})
    with pytest.raises(ValueError, match=r"no entry for factor 'test\.bonds'"):
        gold.plan(*args(w, w.covariance, lock=lock), commit=COMMIT)
    with pytest.raises(ValueError, match=r"no entry for factor 'test\.bonds'"):
        gold.run(*args(w, w.risk, lock=lock), commit=COMMIT)
    assert not w.gold.exists()


@pytest.mark.parametrize("kind", ["covariance", "risk_contribution"])
def test_verify_refuses_a_missing_float_bundle_and_a_tampered_one(w, kind):
    target = w.covariance if kind == "covariance" else w.risk
    with pytest.raises(ValueError, match="pending"):
        gold.verify(*args(w, target), commit=COMMIT)
    plan = gold.run(*args(w, target), commit=COMMIT)
    assert gold.verify(*args(w, target), commit=COMMIT) == plan
    table = next((w.gold / kind / ids(plan)[kind] / "tables").iterdir())
    table.write_bytes(table.read_bytes() + b"x\n")
    for command in (gold.plan, gold.run, gold.verify):
        with pytest.raises(ValueError, match=f"{kind} bundle .* does not verify"):
            command(*args(w, target), commit=COMMIT)


def test_a_builder_that_returns_invalid_rows_writes_nothing_for_that_node(w):
    def bad(*_a):
        return {"dim_window": [], "fact_covariance": [], "fact_volatility": [{"x": "y"}]}

    with pytest.raises(ValueError, match="fact_volatility"):
        gold.run(*args(w, w.covariance), commit=COMMIT, builders={**BUILDERS, "covariance": bad})
    assert {p.name for p in w.gold.iterdir()} == {"panel"}  # the parent is built, the child is not


# --------------------------------------------------------------------------------------
# the builders and the import rule
# --------------------------------------------------------------------------------------


def test_the_jobs_module_imports_neither_models_nor_portfolio():
    tree = ast.parse((REPO / "src" / "hio" / "jobs" / "gold.py").read_text())
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
            imported += [f"{node.module}.{alias.name}" for alias in node.names]
    assert imported  # the walk found the module's imports
    assert not [name for name in imported if name.startswith(("hio.models", "hio.portfolio"))]


def test_builders_and_environment_are_required_by_every_command(w):
    for command in (jobs.plan, jobs.run, jobs.verify):
        with pytest.raises(TypeError, match="builders"):
            command(*args(w, w.panel), commit=COMMIT, environment=ENV)
        with pytest.raises(TypeError, match="environment"):
            command(*args(w, w.panel), commit=COMMIT, builders=BUILDERS)


def _without(key: str) -> dict:
    return {k: v for k, v in BUILDERS.items() if k != key}


@pytest.mark.parametrize(
    "builders",
    [
        {},
        {"panel": build_panel},
        {"portfolio_path": build_portfolio_path},
        {"panel": build_panel, "portfolio_path": build_portfolio_path},  # the old two keys
        _without("panel"),
        _without("portfolio_path"),
        _without("covariance"),
        _without("risk_contribution"),
        {**BUILDERS, "extra": build_panel},
        {**_without("portfolio_path"), "portfolio": build_portfolio_path},
        {**BUILDERS, "risk_contribution": "not callable"},
        list(BUILDERS.items()),
        None,
    ],
)
@pytest.mark.parametrize("command", [jobs.plan, jobs.run, jobs.verify])
def test_a_wrong_builders_mapping_is_refused(w, command, builders):
    with pytest.raises(ValueError, match="builders"):
        command(*args(w, w.risk), commit=COMMIT, builders=builders, environment=ENV)
    assert not w.gold.exists()


def test_the_builder_keys_are_the_four_kinds():
    assert set(contract.KINDS) == set(jobs.BUILDER_KEYS)


@pytest.mark.parametrize("environment", [None, "numpy 9.9.9", [("numpy", "9.9.9")]])
def test_an_environment_that_is_not_a_mapping_is_refused(w, environment):
    with pytest.raises(ValueError, match="environment"):
        jobs.plan(*args(w, w.panel), commit=COMMIT, builders=BUILDERS, environment=environment)


@pytest.mark.parametrize("environment", [{}, {"numpy": "9.9.9"}, {"numpy": "9.9.9", "python": ""}])
def test_a_wrong_environment_is_refused_for_a_float_kind(w, environment):
    with pytest.raises(ValueError, match="environment"):
        gold.plan(*args(w, w.covariance), commit=COMMIT, environment=environment)
    with pytest.raises(ValueError, match="environment"):
        gold.plan(*args(w, w.risk), commit=COMMIT, environment=environment)


def test_run_uses_exactly_the_builders_it_is_given(w):
    calls: list[str] = []

    def spy(name, function):
        def call(*positional, **keyword):
            calls.append(name)
            return function(*positional, **keyword)

        return call

    builders = {name: spy(name, function) for name, function in BUILDERS.items()}
    plan = jobs.run(*args(w, w.portfolio), commit=COMMIT, builders=builders, environment=ENV)
    assert calls == ["panel", "portfolio_path"]
    assert [n.status for n in plan.marts] == ["present", "present"]
    calls.clear()
    plan = jobs.run(*args(w, w.risk), commit=COMMIT, builders=builders, environment=ENV)
    assert calls == ["covariance", "risk_contribution"]  # the panel and the portfolio are present already
    assert [n.kind for n in plan.marts] == ["panel", "covariance", "portfolio_path", "risk_contribution"]
    assert {n.status for n in plan.marts} == {"present"}


# --------------------------------------------------------------------------------------
# the command line
# --------------------------------------------------------------------------------------


@pytest.fixture
def cli(w, monkeypatch, capsys):
    monkeypatch.setattr(gold_build, "_commit", lambda: COMMIT)
    # The real covariance and risk calculations are another task's; the command runs the stand-ins here.
    monkeypatch.setattr(gold_build, "BUILDERS", BUILDERS)
    monkeypatch.setattr(gold_build, "_environment", lambda: ENV)

    def call(command: str, target: Path, **overrides) -> tuple[int, str, str]:
        values = {"target": target, "lock": w.lock, "factor-store": w.store, "gold-root": w.gold, **overrides}
        argv = [command]
        for flag, value in values.items():
            argv += [f"--{flag}", str(value)]
        code = gold_build.main(argv)
        captured = capsys.readouterr()
        return code, captured.out, captured.err

    return call


def lines(plan: gold.Plan) -> str:
    return "".join(f"{n.kind} {n.name} {n.status} {n.build_id or '-'}\n" for n in plan.nodes) + "pass\n"


def test_cli_plan_run_verify_output(w, cli):
    pending = gold.plan(*args(w, w.portfolio), commit=COMMIT)
    code, out, err = cli("plan", w.portfolio)
    assert (code, err) == (0, "")
    assert out == lines(pending)
    assert out.splitlines()[-2] == f"portfolio_path demo-60-40 pending -"  # noqa: F541
    assert out.splitlines()[0] == f"factor_series test.bonds input {BONDS_BUILD}"

    code, out, err = cli("verify", w.portfolio)
    assert code == 2 and out == ""
    assert err.startswith("refused: ")

    code, out, err = cli("run", w.portfolio)
    built = gold.plan(*args(w, w.portfolio), commit=COMMIT)
    assert (code, err) == (0, "")
    assert out == lines(built)
    assert [n.status for n in built.marts] == ["present", "present"]

    before = snapshot(w.gold)
    assert cli("run", w.portfolio) == (0, lines(built), "")
    assert cli("verify", w.portfolio) == (0, lines(built), "")
    assert cli("plan", w.panel)[1] == lines(gold.plan(*args(w, w.panel), commit=COMMIT))
    assert snapshot(w.gold) == before


def test_cli_output_holds_no_date_and_no_decimal_from_the_data(w, cli):
    outputs = [cli(command, w.portfolio) for command in ("plan", "run", "verify")]
    for _, out, err in outputs:
        text = out + err
        assert not DATE.search(text)
        assert not any(value in text for value in ALL_RETURNS)
        assert "0.60" not in text and "0.40" not in text
        assert not re.search(r"\d\.\d", text)


def test_cli_plan_run_verify_for_a_risk_target(w, cli):
    pending = gold.plan(*args(w, w.risk), commit=COMMIT)
    code, out, err = cli("plan", w.risk)
    assert (code, err) == (0, "")
    assert out == lines(pending)
    assert out.splitlines()[-2] == "risk_contribution demo-risk pending -"
    assert out.splitlines()[-4] == "covariance demo-cov pending -"

    code, out, err = cli("verify", w.risk)
    assert code == 2 and out == "" and err.startswith("refused: ")

    code, out, err = cli("run", w.risk)
    built = gold.plan(*args(w, w.risk), commit=COMMIT)
    assert (code, err) == (0, "")
    assert out == lines(built)
    assert [n.kind for n in built.marts] == KINDS_IN_ORDER
    assert {n.status for n in built.marts} == {"present"}

    before = snapshot(w.gold)
    assert cli("run", w.risk) == (0, lines(built), "")
    assert cli("verify", w.risk) == (0, lines(built), "")
    assert cli("plan", w.covariance)[1] == lines(gold.plan(*args(w, w.covariance), commit=COMMIT))
    assert snapshot(w.gold) == before


def test_cli_hands_its_environment_to_the_planner(w, cli, monkeypatch):
    cli("run", w.risk)
    built = gold.plan(*args(w, w.risk), commit=COMMIT, environment=ENV)
    monkeypatch.setattr(gold_build, "_environment", lambda: ENV_B)
    code, out, _ = cli("plan", w.risk)
    assert code == 0
    changed = gold.plan(*args(w, w.risk), commit=COMMIT, environment=ENV_B)
    assert out == lines(changed) != lines(built)
    assert [n.status for n in changed.marts] == ["present", "missing", "present", "pending"]


def test_cli_output_for_a_risk_target_holds_no_date_and_no_float_from_the_data(w, cli):
    for command in ("plan", "run", "verify"):
        _, out, err = cli(command, w.risk)
        text = out + err
        assert not DATE.search(text)
        assert not any(value in text for value in ALL_RETURNS)
        assert not re.search(r"\d\.\d", text)


def test_cli_refusal_never_quotes_a_date_or_a_value_from_the_data(w, cli):
    # Periods that do not join: the calculation's own message quotes both dates.
    gappy = [("2024-01-31", "2024-02-15", "0.0113"), ("2024-02-20", "2024-02-29", "0.0027")]
    pin = make_series(w.store, "test.bonds", "d" * 16, gappy)
    write_lock(w.lock, {**w.pins, "test.bonds": pin})
    with pytest.raises(ValueError, match=DATE.pattern):
        gold.run(*args(w, w.panel), commit=COMMIT)  # the library does name them ...
    code, out, err = cli("run", w.panel)
    assert code == 2 and out == ""
    assert err.startswith("refused: ") and "join" in err
    assert not DATE.search(err)  # ... the command does not
    assert "2024" not in err and "0.0113" not in err


def test_cli_scrub_keeps_build_ids_and_masks_other_digits():
    sha = "ab12" * 16
    short = "0123456789abcdef"
    text = f"{sha} {short} 2024-01-31 value 0.0113 'x0.5' row 12 version 0.1.0"
    assert gold_build._scrub(text) == f"{sha} {short} ####-##-## value #.#### 'x#.#' row ## version #.#.#"


def test_cli_refuses_a_gold_root_inside_the_repository(w, cli):
    inside = gold_build.REPO / "gold-marts-should-not-exist"
    code, out, err = cli("run", w.panel, **{"gold-root": inside})
    assert (code, out) == (2, "")
    assert err.startswith("refused: ") and "outside the repository" in err
    assert not inside.exists()
    code, _, err = cli("plan", w.panel, **{"gold-root": gold_build.REPO})
    assert code == 2 and "outside the repository" in err


def test_cli_passes_the_real_calculations_in():
    real = {
        "panel": build_panel,
        "portfolio_path": build_portfolio_path,
        "covariance": risk_module.build_covariance,
        "risk_contribution": risk_module.build_risk_contribution,
    }
    assert real == gold_build.BUILDERS
    assert set(gold_build.BUILDERS) == set(jobs.BUILDER_KEYS)


def test_cli_environment_is_the_numpy_and_python_versions():
    import numpy

    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    assert gold_build._environment() == {"numpy": numpy.__version__, "python": version}


def test_cli_refuses_what_the_planner_refuses(w, cli, tmp_path):
    lock = write_lock(tmp_path / "short.yaml", {"test.equity": w.pins["test.equity"]})
    code, out, err = cli("plan", w.panel, lock=lock)
    assert (code, out) == (2, "")
    assert err.startswith("refused: ") and "no entry for factor" in err
    code, _, err = cli("plan", tmp_path / "missing.yaml")
    assert code == 2 and err.startswith("refused: ")


def test_cli_commit_is_head_and_only_when_the_tree_is_clean(monkeypatch):
    calls: list[tuple[str, ...]] = []

    def fake(status: str):
        def run(command, **kwargs):
            calls.append(tuple(command))
            assert command[0] == "git" and kwargs["cwd"] == gold_build.REPO
            stdout = status if command[1] == "status" else "1234abcd\n"
            return gold_build.subprocess.CompletedProcess(command, 0, stdout, "")

        return run

    monkeypatch.setattr(gold_build.subprocess, "run", fake(""))
    assert gold_build._commit() == "1234abcd"
    assert calls == [("git", "status", "--porcelain"), ("git", "rev-parse", "HEAD")]
    monkeypatch.setattr(gold_build.subprocess, "run", fake(" M src/hio/jobs/gold.py\n"))
    with pytest.raises(ValueError, match="not clean"):
        gold_build._commit()


def test_cli_a_dirty_tree_is_a_refusal(w, monkeypatch, capsys):
    def dirty(command, **_kwargs):
        return gold_build.subprocess.CompletedProcess(command, 0, "?? stray\n", "")

    monkeypatch.setattr(gold_build.subprocess, "run", dirty)
    argv = ["plan", "--target", str(w.panel), "--lock", str(w.lock)]
    argv += ["--factor-store", str(w.store), "--gold-root", str(w.gold)]
    assert gold_build.main(argv) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and "not clean" in captured.err
    assert not w.gold.exists()
