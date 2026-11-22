"""The gold planner and runner (OD-0233): `hio.jobs.gold` and `tools/gold_build.py`. Invented data only."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import re
import sys
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

REPO = Path(__file__).resolve().parent.parent
BUILDERS = {"panel": build_panel, "portfolio_path": build_portfolio_path}


def _with_builders(function):
    def call(*positional, commit, builders=BUILDERS):
        return function(*positional, commit=commit, builders=builders)

    call.__name__ = function.__name__
    return call


# The planner and runner with the real calculations passed in, as `tools/gold_build.py` does.
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


@dataclass
class World:
    store: Path
    lock: Path
    panel: Path
    portfolio: Path
    gold: Path
    pins: dict[str, dict[str, str]]


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
    never = {"panel": refuse_to_write, "portfolio_path": refuse_to_write}
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


def test_a_target_that_is_neither_spec_is_refused(w, tmp_path):
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


def test_builders_are_required_by_every_command(w):
    for command in (jobs.plan, jobs.run, jobs.verify):
        with pytest.raises(TypeError, match="builders"):
            command(*args(w, w.panel), commit=COMMIT)


@pytest.mark.parametrize(
    "builders",
    [
        {},
        {"panel": build_panel},
        {"portfolio_path": build_portfolio_path},
        {"panel": build_panel, "portfolio_path": build_portfolio_path, "extra": build_panel},
        {"panel": build_panel, "portfolio": build_portfolio_path},
        {"panel": build_panel, "portfolio_path": "not callable"},
        [("panel", build_panel), ("portfolio_path", build_portfolio_path)],
        None,
    ],
)
@pytest.mark.parametrize("command", [jobs.plan, jobs.run, jobs.verify])
def test_a_wrong_builders_mapping_is_refused(w, command, builders):
    with pytest.raises(ValueError, match="builders"):
        command(*args(w, w.portfolio), commit=COMMIT, builders=builders)
    assert not w.gold.exists()


def test_run_uses_exactly_the_builders_it_is_given(w):
    calls: list[str] = []

    def spy(name, function):
        def call(*positional, **keyword):
            calls.append(name)
            return function(*positional, **keyword)

        return call

    builders = {
        "panel": spy("panel", build_panel),
        "portfolio_path": spy("portfolio_path", build_portfolio_path),
    }
    plan = jobs.run(*args(w, w.portfolio), commit=COMMIT, builders=builders)
    assert calls == ["panel", "portfolio_path"]
    assert [n.status for n in plan.marts] == ["present", "present"]


# --------------------------------------------------------------------------------------
# the command line
# --------------------------------------------------------------------------------------


@pytest.fixture
def cli(w, monkeypatch, capsys):
    monkeypatch.setattr(gold_build, "_commit", lambda: COMMIT)

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
    assert {"panel": build_panel, "portfolio_path": build_portfolio_path} == gold_build.BUILDERS


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
