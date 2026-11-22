"""The gold-mart planner and runner (OD-0233; `docs/decisions/gold-marts-contract.md` §7).

A **plan** names a target spec (a panel or a portfolio path), a lock, the factor store and the gold root. It
resolves the target's parents from the specs and the lock, orders them (parents before children), computes
each `build_id` and marks each node:

- `input`: a factor series, read from the factor store at the lock's pin and verified against the pin's
  `series_sha256`. Factor series are inputs and are never built here;
- `present`: a verified bundle exists at the node's `build_id`;
- `missing`: no bundle exists there;
- `pending`: a portfolio path whose panel is `missing`. Its recipe needs the panel's `payload_sha256`, which
  exists only once the panel is built, so its `build_id` is `None` until then.

`run` builds each `missing` or `pending` mart node in order and verifies it before the next; a second `run`
builds nothing. `verify` refuses unless every mart node is `present`. Nothing here reads a clock or the
environment, and nothing resolves "latest": every identity comes from the specs, the lock and `commit`.

Where the contract is silent (choices made here):

- A bundle directory that exists at a node's `build_id` but fails `open_bundle` is **refused**, never treated
  as `missing` (a rebuild would be refused by `write_bundle` anyway) and never as `present`.
- A factor-series node is named for its factor id; a mart node for its spec's `identity.name`.
- The checks that need only the loaded series (one numeraire and one series class across a panel's members;
  weights naming exactly the panel's members; total-return members for a portfolio) are made at plan time,
  so a plan that cannot be built is refused before anything is written.
- `commit` is any non-empty text; this module never asks git.
- The import rules (`tools/check_repo.py`) forbid `hio.jobs` from importing `hio.models` and `hio.portfolio`,
  so the calculations are passed in: `builders` is a required keyword argument of `plan`, `run` and `verify`,
  a mapping with exactly the keys `panel` and `portfolio_path` whose values are `build_panel` and
  `build_portfolio_path` (same signatures). Any other mapping is refused. `plan` and `verify` never call them.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from hio.contracts.gold import (
    TABLES,
    Bundle,
    FactorSeries,
    build_id,
    lock_pin,
    open_bundle,
    read_factor_series,
    read_lock,
    read_panel_spec,
    read_portfolio_spec,
    recipe,
    table_bytes,
    write_bundle,
)

BUILDER_KEYS = frozenset({"panel", "portfolio_path"})

FACTOR_SERIES = "factor_series"
PANEL = "panel"
PORTFOLIO_PATH = "portfolio_path"

INPUT = "input"
PRESENT = "present"
MISSING = "missing"
PENDING = "pending"


@dataclass(frozen=True)
class Node:
    """One step of a plan. `parents` are the parent nodes' names; `build_id` is `None` only for a pending
    node. A factor-series node has status `input` and its `build_id` is the lock's pin (16 hex)."""

    kind: str
    name: str
    build_id: str | None
    status: str
    parents: tuple[str, ...]


@dataclass(frozen=True)
class Plan:
    """The nodes, parents before children."""

    nodes: tuple[Node, ...]

    @property
    def marts(self) -> tuple[Node, ...]:
        """The nodes that are built here: every node that is not a factor series."""
        return tuple(n for n in self.nodes if n.kind != FACTOR_SERIES)


@dataclass(frozen=True)
class _Resolved:
    """A plan with what the runner needs to build it."""

    plan: Plan
    panel_spec: dict[str, Any]
    series: dict[str, FactorSeries]
    panel_recipe: dict[str, Any]
    panel_id: str
    portfolio_spec: dict[str, Any] | None
    portfolio_recipe: dict[str, Any] | None  # None while the panel is missing
    portfolio_id: str | None


def _spec_ref(spec: Mapping[str, Any]) -> dict[str, str]:
    return {"name": spec["name"], "version": spec["version"], "sha256": spec["sha256"]}


def _status(gold_root: Path, kind: str, bid: str) -> tuple[str, Bundle | None]:
    """`present` with the verified bundle, or `missing`. A directory that exists but does not verify is
    refused with the `ValueError` `open_bundle` raised."""
    directory = Path(gold_root) / kind / bid
    if not (directory.exists() or directory.is_symlink()):
        return MISSING, None
    try:
        bundle = open_bundle(gold_root, kind, bid)
    except ValueError as exc:
        raise ValueError(f"{kind} bundle {bid} exists but does not verify: {exc}") from exc
    return PRESENT, bundle


def _target_kind(target: Path) -> str:
    try:
        loaded = yaml.safe_load(Path(target).read_bytes())
    except yaml.YAMLError as exc:
        raise ValueError(f"{target}: not YAML: {exc}") from exc
    if not isinstance(loaded, dict) or loaded.get("kind") not in (PANEL, PORTFOLIO_PATH):
        raise ValueError(f"{target}: kind must be {PANEL!r} or {PORTFOLIO_PATH!r}")
    return str(loaded["kind"])


def _panel_path(target: Path, name: str) -> Path:
    if name in {"", ".", ".."} or Path(name).name != name or "\\" in name:
        raise ValueError(f"portfolio names a panel that is not a single path component: {name!r}")
    return Path(target).parent.parent / "panels" / f"{name}.yaml"


def _read_members(
    panel_spec: Mapping[str, Any], lock: Mapping[str, Any], factor_store: Path
) -> dict[str, FactorSeries]:
    """Each member's series, read at the lock's pin and verified against the pin's `series_sha256`."""
    series: dict[str, FactorSeries] = {}
    for code in sorted(panel_spec["members"]):
        factor_id = panel_spec["members"][code]
        pin = lock_pin(lock, factor_id)  # a member with no lock entry is refused
        try:
            series[code] = read_factor_series(
                factor_store,
                factor_id,
                pin["spec_version"],
                pin["build_id"],
                series_sha256=pin["series_sha256"],
            )
        except ValueError as exc:
            raise ValueError(f"factor {factor_id!r} (member {code!r}): {exc}") from exc
    if len({s.numeraire for s in series.values()}) != 1:
        raise ValueError("panel members do not share one numeraire")
    if len({s.series_class for s in series.values()}) != 1:
        raise ValueError("panel members do not share one series_class")
    return series


def _resolve(target: Path, lock: Path, factor_store: Path, gold_root: Path, commit: str) -> _Resolved:
    if not isinstance(commit, str) or not commit:
        raise ValueError(f"commit must be non-empty text: {commit!r}")
    target = Path(target)
    kind = _target_kind(target)
    portfolio_spec: dict[str, Any] | None = None
    if kind == PORTFOLIO_PATH:
        portfolio_spec = read_portfolio_spec(target)
        panel_path = _panel_path(target, portfolio_spec["panel"])
        if not panel_path.is_file():
            raise ValueError(f"portfolio {portfolio_spec['name']!r} names an unknown panel: {panel_path}")
        panel_spec = read_panel_spec(panel_path)
        if panel_spec["name"] != portfolio_spec["panel"]:
            raise ValueError(
                f"panel spec {panel_path.name} is named {panel_spec['name']!r}, "
                f"but the portfolio names {portfolio_spec['panel']!r}"
            )
        if set(portfolio_spec["weights"]) != set(panel_spec["members"]):
            raise ValueError(
                f"weights name {sorted(portfolio_spec['weights'])}, but the panel's members are "
                f"{sorted(panel_spec['members'])}"
            )
    else:
        panel_spec = read_panel_spec(target)

    series = _read_members(panel_spec, read_lock(lock), Path(factor_store))
    if portfolio_spec is not None and {s.series_class for s in series.values()} != {"total_return"}:
        raise ValueError("a portfolio needs total_return members: an excess return is not a holding")

    codes = sorted(series)
    input_nodes = [Node(FACTOR_SERIES, series[c].factor_id, series[c].build_id, INPUT, ()) for c in codes]
    panel_recipe = recipe(
        PANEL,
        _spec_ref(panel_spec),
        {
            "frequency": panel_spec["frequency"],
            "alignment": panel_spec["alignment"],
            "incomplete_periods": panel_spec["incomplete_periods"],
            "members": dict(panel_spec["members"]),
        },
        [series[c].parent(c) for c in codes],
        commit,
    )
    panel_id = build_id(panel_recipe)
    panel_status, panel_bundle = _status(gold_root, PANEL, panel_id)
    panel_node = Node(PANEL, panel_spec["name"], panel_id, panel_status, tuple(n.name for n in input_nodes))
    nodes = [*input_nodes, panel_node]

    portfolio_recipe: dict[str, Any] | None = None
    portfolio_id: str | None = None
    if portfolio_spec is not None:
        parents = (panel_spec["name"],)
        if panel_bundle is None:
            nodes.append(Node(PORTFOLIO_PATH, portfolio_spec["name"], None, PENDING, parents))
        else:
            portfolio_recipe = recipe(
                PORTFOLIO_PATH,
                _spec_ref(portfolio_spec),
                {
                    "panel": portfolio_spec["panel"],
                    "rebalance": portfolio_spec["rebalance"],
                    "weights": dict(portfolio_spec["weights"]),
                },
                [
                    {
                        "role": "panel",
                        "kind": PANEL,
                        "id": panel_bundle.build_id,
                        "payload_sha256": panel_bundle.payload_sha256,
                    }
                ],
                commit,
            )
            portfolio_id = build_id(portfolio_recipe)
            status, _ = _status(gold_root, PORTFOLIO_PATH, portfolio_id)
            nodes.append(Node(PORTFOLIO_PATH, portfolio_spec["name"], portfolio_id, status, parents))
    return _Resolved(
        plan=Plan(tuple(nodes)),
        panel_spec=panel_spec,
        series=series,
        panel_recipe=panel_recipe,
        panel_id=panel_id,
        portfolio_spec=portfolio_spec,
        portfolio_recipe=portfolio_recipe,
        portfolio_id=portfolio_id,
    )


Builders = Mapping[str, Callable[..., Any]]


def _check_builders(builders: object) -> None:
    if not isinstance(builders, Mapping) or set(builders) != BUILDER_KEYS:
        keys = sorted(builders) if isinstance(builders, Mapping) else type(builders).__name__
        raise ValueError(f"builders must be a mapping with exactly the keys {sorted(BUILDER_KEYS)}: {keys}")
    for key, function in builders.items():
        if not callable(function):
            raise ValueError(f"builders[{key!r}] is not callable")


def plan(
    target: Path, lock: Path, factor_store: Path, gold_root: Path, *, commit: str, builders: Builders
) -> Plan:
    """§7: the ordered nodes for `target` (a panel spec or a portfolio spec, told apart by its `kind`).

    Reads, writes nothing. Refuses with `ValueError`: a member with no lock entry; a series that fails
    verification against the lock's pin; a portfolio whose panel spec is missing or is not named as the
    portfolio says; weights that do not name exactly the panel's members; members that do not share a
    numeraire and a series class; a portfolio over `excess` members; a bundle at a computed `build_id`
    that does not verify; a `builders` mapping that is not exactly `{panel, portfolio_path}`. The builders
    are not called here.
    """
    _check_builders(builders)
    return _resolve(target, lock, factor_store, gold_root, commit).plan


def _write(
    gold_root: Path, kind: str, rcp: dict[str, Any], rows: Mapping[str, list[dict[str, str]]]
) -> Bundle:
    tables = {name: table_bytes(kind, name, rows[name]) for name in TABLES[kind]}
    write_bundle(gold_root, rcp, tables)
    return open_bundle(gold_root, kind, build_id(rcp))


def run(
    target: Path, lock: Path, factor_store: Path, gold_root: Path, *, commit: str, builders: Builders
) -> Plan:
    """§7: plan, then build each `missing` or `pending` mart node in order, verifying each before the
    next, and return the final plan, in which every mart node is `present`. A pending child's recipe is
    resolved from its parent once the parent is built. Nothing that is `present` is rebuilt, so a second
    run writes nothing and returns the same plan."""
    _check_builders(builders)
    build_panel = builders["panel"]
    build_portfolio_path = builders["portfolio_path"]
    resolved = _resolve(target, lock, factor_store, gold_root, commit)
    panel_node = next(n for n in resolved.plan.nodes if n.kind == PANEL)
    if panel_node.status != PRESENT:
        rows = build_panel(resolved.panel_spec, resolved.series, resolved.panel_id)
        _write(Path(gold_root), PANEL, resolved.panel_recipe, rows)
        resolved = _resolve(target, lock, factor_store, gold_root, commit)  # the child's recipe now resolves
    if resolved.portfolio_spec is not None:
        node = next(n for n in resolved.plan.nodes if n.kind == PORTFOLIO_PATH)
        if node.status != PRESENT:
            assert resolved.portfolio_recipe is not None and resolved.portfolio_id is not None
            panel = open_bundle(gold_root, PANEL, resolved.panel_id)
            panel_tables = {name: panel.table(name) for name in TABLES[PANEL]}
            rows = build_portfolio_path(resolved.portfolio_spec, panel_tables, resolved.portfolio_id)
            _write(Path(gold_root), PORTFOLIO_PATH, resolved.portfolio_recipe, rows)
    final = _resolve(target, lock, factor_store, gold_root, commit).plan
    not_built = [f"{n.kind} {n.name}" for n in final.marts if n.status != PRESENT]
    if not_built:
        raise ValueError(f"after the run these are not present: {not_built}")
    return final


def verify(
    target: Path, lock: Path, factor_store: Path, gold_root: Path, *, commit: str, builders: Builders
) -> Plan:
    """§7: plan, and refuse (`ValueError`) unless every mart node is `present`."""
    result = plan(target, lock, factor_store, gold_root, commit=commit, builders=builders)
    absent = [f"{n.kind} {n.name} is {n.status}" for n in result.marts if n.status != PRESENT]
    if absent:
        raise ValueError("; ".join(absent))
    return result
