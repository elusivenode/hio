"""The gold-mart planner and runner (OD-0233, OD-0234; `docs/decisions/gold-marts-contract.md` §7, §6a).

A **plan** names a target spec (a panel, a portfolio path, a covariance or a risk contribution), a lock, the
factor store and the gold root. It resolves the target's parents from the specs and the lock, orders them
(parents before children), computes each `build_id` and marks each node:

- `input`: a factor series, read from the factor store at the lock's pin and verified against the pin's
  `series_sha256`. Factor series are inputs and are never built here;
- `present`: a verified bundle exists at the node's `build_id`;
- `missing`: no bundle exists there;
- `pending`: a mart whose parent bundle is not yet `present`. Its recipe needs the parent's `payload_sha256`,
  which exists only once the parent is built, so its `build_id` is `None` until then.

`run` builds each `missing` or `pending` mart node in order and verifies it before the next; a second `run`
builds nothing. `verify` refuses unless every mart node is `present`. Nothing here reads a clock or the
environment, and nothing resolves "latest": every identity comes from the specs, the lock, `commit` and, for
the two float kinds, the `environment` the caller passes in.

Targets, told apart by the spec's `kind`. The target's directory has siblings that hold the other specs:
`../panels/<name>.yaml`, `../portfolios/<name>.yaml`, `../covariances/<name>.yaml`; each named spec's
`identity.name` must equal the name used. The mart nodes of each target, in order:

| target | mart nodes |
|---|---|
| `panel` | panel |
| `portfolio_path` | panel, portfolio_path |
| `covariance` | panel, covariance |
| `risk_contribution` | panel, covariance, portfolio_path, risk_contribution |

Where the contract is silent (choices made here):

- A bundle directory that exists at a node's `build_id` but fails `open_bundle` is **refused**, never treated
  as `missing` (a rebuild would be refused by `write_bundle` anyway) and never as `present`.
- A factor-series node is named for its factor id; a mart node for its spec's `identity.name`.
- The checks that need only the loaded series (one numeraire and one series class across a panel's members;
  weights naming exactly the panel's members; total-return members for a portfolio) are made at plan time,
  so a plan that cannot be built is refused before anything is written.
- A risk target whose covariance and portfolio name different panel specs is refused at plan time. When both
  bundles are present it is also refused unless their recipes name the same panel parent `id`.
- `commit` is any non-empty text; this module never asks git. `environment` must be a mapping; its content
  is checked by `recipe` for the two float kinds and is otherwise unused (a decimal kind's recipe has none).
- The import rules (`tools/check_repo.py`) forbid `hio.jobs` from importing `hio.models` and `hio.portfolio`,
  so the calculations are passed in: `builders` is a required keyword argument of `plan`, `run` and `verify`,
  a mapping with exactly the keys `panel`, `portfolio_path`, `covariance` and `risk_contribution` whose
  values are `build_panel`, `build_portfolio_path`, `build_covariance` and `build_risk_contribution`. Any
  other mapping is refused. `plan` and `verify` never call them.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from hio.contracts.gold import (
    FLOAT_KINDS,
    TABLES,
    Bundle,
    FactorSeries,
    build_id,
    lock_pin,
    open_bundle,
    read_covariance_spec,
    read_factor_series,
    read_lock,
    read_panel_spec,
    read_portfolio_spec,
    read_risk_spec,
    recipe,
    table_bytes,
    write_bundle,
)

FACTOR_SERIES = "factor_series"
PANEL = "panel"
PORTFOLIO_PATH = "portfolio_path"
COVARIANCE = "covariance"
RISK_CONTRIBUTION = "risk_contribution"

BUILDER_KEYS = frozenset({PANEL, PORTFOLIO_PATH, COVARIANCE, RISK_CONTRIBUTION})
TARGET_KINDS = (PANEL, PORTFOLIO_PATH, COVARIANCE, RISK_CONTRIBUTION)

INPUT = "input"
PRESENT = "present"
MISSING = "missing"
PENDING = "pending"

# The recipe's calculation parameters (the spec's fields, contract §5, §6, §6a).
_PARAMETERS: dict[str, tuple[str, ...]] = {
    PANEL: ("frequency", "alignment", "incomplete_periods", "members"),
    PORTFOLIO_PATH: ("panel", "rebalance", "weights"),
    COVARIANCE: ("panel", "estimator", "ddof", "annualisation", "trailing_months"),
    RISK_CONTRIBUTION: ("portfolio", "covariance"),
}

# A mart's parent bundles as (role, kind); the panel's parents are factor series and are handled apart.
_PARENTS: dict[str, tuple[tuple[str, str], ...]] = {
    PORTFOLIO_PATH: (("panel", PANEL),),
    COVARIANCE: (("panel", PANEL),),
    RISK_CONTRIBUTION: (("covariance", COVARIANCE), ("portfolio", PORTFOLIO_PATH)),
}


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
class _Step:
    """One mart node with what the runner needs to build it. `recipe` is `None` while the node is pending."""

    node: Node
    spec: dict[str, Any]
    recipe: dict[str, Any] | None


@dataclass(frozen=True)
class _Resolved:
    """A plan with what the runner needs to build it: the factor series and each mart's step, by kind, in
    plan order."""

    plan: Plan
    series: dict[str, FactorSeries]
    steps: dict[str, _Step]


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
    if not isinstance(loaded, dict) or loaded.get("kind") not in TARGET_KINDS:
        raise ValueError(f"{target}: kind must be one of {list(TARGET_KINDS)}")
    return str(loaded["kind"])


def _sibling(
    target: Path,
    owner: str,
    owner_name: str,
    what: str,
    directory: str,
    name: str,
    reader: Callable[[Path], dict[str, Any]],
) -> dict[str, Any]:
    """The spec named `name`, read from `../<directory>/<name>.yaml` beside the target's directory. `owner`
    and `owner_name` say whose spec names it, for the refusal."""
    if name in {"", ".", ".."} or Path(name).name != name or "\\" in name:
        raise ValueError(f"{owner} names a {what} that is not a single path component: {name!r}")
    path = Path(target).parent.parent / directory / f"{name}.yaml"
    if not path.is_file():
        raise ValueError(f"{owner} {owner_name!r} names an unknown {what}: {path}")
    spec = reader(path)
    if spec["name"] != name:
        raise ValueError(f"{what} spec {path.name} is named {spec['name']!r}, but the {owner} names {name!r}")
    return spec


def _load_specs(target: Path, kind: str) -> dict[str, dict[str, Any]]:
    """The target's spec and those of its ancestors, by kind, parents before children."""
    if kind == PANEL:
        return {PANEL: read_panel_spec(target)}
    if kind == PORTFOLIO_PATH:
        portfolio = read_portfolio_spec(target)
        panel = _sibling(
            target, "portfolio", portfolio["name"], "panel", "panels", portfolio["panel"], read_panel_spec
        )
        return {PANEL: panel, PORTFOLIO_PATH: portfolio}
    if kind == COVARIANCE:
        covariance = read_covariance_spec(target)
        panel = _sibling(
            target, "covariance", covariance["name"], "panel", "panels", covariance["panel"], read_panel_spec
        )
        return {PANEL: panel, COVARIANCE: covariance}
    risk = read_risk_spec(target)
    covariance = _sibling(
        target, "risk", risk["name"], "covariance", "covariances", risk["covariance"], read_covariance_spec
    )
    portfolio = _sibling(
        target, "risk", risk["name"], "portfolio", "portfolios", risk["portfolio"], read_portfolio_spec
    )
    if covariance["panel"] != portfolio["panel"]:
        raise ValueError(
            f"risk {risk['name']!r}: covariance {covariance['name']!r} is built on panel "
            f"{covariance['panel']!r}, but portfolio {portfolio['name']!r} is built on {portfolio['panel']!r}"
        )
    panel = _sibling(
        target, "covariance", covariance["name"], "panel", "panels", covariance["panel"], read_panel_spec
    )
    return {PANEL: panel, COVARIANCE: covariance, PORTFOLIO_PATH: portfolio, RISK_CONTRIBUTION: risk}


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


def _panel_parent_id(kind: str, bundle: Bundle) -> str:
    """The `id` of the panel parent that a covariance or portfolio-path bundle's recipe names."""
    ids = [p["id"] for p in bundle.recipe["parents"] if p["role"] == PANEL and p["kind"] == PANEL]
    if len(ids) != 1:
        raise ValueError(f"{kind} bundle {bundle.build_id} names no single panel parent")
    return str(ids[0])


def _parameters(kind: str, spec: Mapping[str, Any]) -> dict[str, Any]:
    return {k: dict(spec[k]) if isinstance(spec[k], Mapping) else spec[k] for k in _PARAMETERS[kind]}


def _resolve(
    target: Path,
    lock: Path,
    factor_store: Path,
    gold_root: Path,
    commit: str,
    environment: Mapping[str, str],
) -> _Resolved:
    if not isinstance(commit, str) or not commit:
        raise ValueError(f"commit must be non-empty text: {commit!r}")
    if not isinstance(environment, Mapping):
        raise ValueError(f"environment must be a mapping: {type(environment).__name__}")
    target = Path(target)
    kind = _target_kind(target)
    if kind in FLOAT_KINDS:
        # Refused now, not when a pending node's recipe is first built, so a bad environment writes nothing.
        keys = sorted(environment)
        if keys != ["numpy", "python"] or not all(isinstance(v, str) and v for v in environment.values()):
            raise ValueError(f"environment must be exactly {{numpy, python}}, each non-empty text: {keys}")
    specs = _load_specs(target, kind)
    panel_spec = specs[PANEL]
    portfolio_spec = specs.get(PORTFOLIO_PATH)
    if portfolio_spec is not None and set(portfolio_spec["weights"]) != set(panel_spec["members"]):
        raise ValueError(
            f"weights name {sorted(portfolio_spec['weights'])}, but the panel's members are "
            f"{sorted(panel_spec['members'])}"
        )

    series = _read_members(panel_spec, read_lock(lock), Path(factor_store))
    if portfolio_spec is not None and {s.series_class for s in series.values()} != {"total_return"}:
        raise ValueError("a portfolio needs total_return members: an excess return is not a holding")

    codes = sorted(series)
    input_nodes = [Node(FACTOR_SERIES, series[c].factor_id, series[c].build_id, INPUT, ()) for c in codes]
    nodes: list[Node] = list(input_nodes)
    steps: dict[str, _Step] = {}
    bundles: dict[str, Bundle | None] = {}
    for kind, spec in specs.items():
        if kind == PANEL:
            parent_names = tuple(n.name for n in input_nodes)
            parents: list[dict[str, str]] | None = [series[c].parent(c) for c in codes]
        else:
            roles = _PARENTS[kind]
            parent_names = tuple(specs[parent_kind]["name"] for _, parent_kind in roles)
            parents = None
            if all(bundles[parent_kind] is not None for _, parent_kind in roles):
                parents = []
                for role, parent_kind in roles:
                    parent = bundles[parent_kind]
                    assert parent is not None
                    parents.append(
                        {
                            "role": role,
                            "kind": parent_kind,
                            "id": parent.build_id,
                            "payload_sha256": parent.payload_sha256,
                        }
                    )
        if parents is None:
            steps[kind] = _Step(Node(kind, spec["name"], None, PENDING, parent_names), spec, None)
            bundles[kind] = None
            nodes.append(steps[kind].node)
            continue
        if kind == RISK_CONTRIBUTION:
            covariance, portfolio = bundles[COVARIANCE], bundles[PORTFOLIO_PATH]
            assert covariance is not None and portfolio is not None
            if _panel_parent_id(COVARIANCE, covariance) != _panel_parent_id(PORTFOLIO_PATH, portfolio):
                raise ValueError(
                    f"risk {spec['name']!r}: the covariance bundle and the portfolio bundle "
                    "are not built on the same panel bundle"
                )
        rcp = recipe(
            kind,
            _spec_ref(spec),
            _parameters(kind, spec),
            parents,
            commit,
            environment=environment if kind in FLOAT_KINDS else None,
        )
        bid = build_id(rcp)
        status, bundle = _status(gold_root, kind, bid)
        bundles[kind] = bundle
        steps[kind] = _Step(Node(kind, spec["name"], bid, status, parent_names), spec, rcp)
        nodes.append(steps[kind].node)
    return _Resolved(plan=Plan(tuple(nodes)), series=series, steps=steps)


Builders = Mapping[str, Callable[..., Any]]


def _check_builders(builders: object) -> None:
    if not isinstance(builders, Mapping) or set(builders) != BUILDER_KEYS:
        keys = sorted(builders) if isinstance(builders, Mapping) else type(builders).__name__
        raise ValueError(f"builders must be a mapping with exactly the keys {sorted(BUILDER_KEYS)}: {keys}")
    for key, function in builders.items():
        if not callable(function):
            raise ValueError(f"builders[{key!r}] is not callable")


def plan(
    target: Path,
    lock: Path,
    factor_store: Path,
    gold_root: Path,
    *,
    commit: str,
    builders: Builders,
    environment: Mapping[str, str],
) -> Plan:
    """§7, §6a: the ordered nodes for `target` (a panel, portfolio, covariance or risk spec, told apart by
    its `kind`).

    Reads, writes nothing. `environment` is `{numpy, python}`; it is part of the identity of a covariance
    or a risk bundle and of no other. Refuses with `ValueError`: a member with no lock entry; a series that
    fails verification against the lock's pin; a spec that names a sibling spec that is missing or is not
    named as the spec says; weights that do not name exactly the panel's members; members that do not
    share a numeraire and a series class; a portfolio over `excess` members; a risk contribution whose
    covariance and portfolio are not built on the same panel; a bundle at a computed `build_id` that does
    not verify; a `builders` mapping that is not exactly `{panel, portfolio_path, covariance,
    risk_contribution}`. The builders are not called here.
    """
    _check_builders(builders)
    return _resolve(target, lock, factor_store, gold_root, commit, environment).plan


def _write(
    gold_root: Path, kind: str, rcp: dict[str, Any], rows: Mapping[str, list[dict[str, str]]]
) -> Bundle:
    tables = {name: table_bytes(kind, name, rows[name]) for name in TABLES[kind]}
    write_bundle(gold_root, rcp, tables)
    return open_bundle(gold_root, kind, build_id(rcp))


def _tables(gold_root: Path, kind: str, bid: str | None) -> dict[str, list[dict[str, str]]]:
    assert bid is not None
    bundle = open_bundle(gold_root, kind, bid)
    return {name: bundle.table(name) for name in TABLES[kind]}


def _rows(
    kind: str,
    step: _Step,
    resolved: _Resolved,
    gold_root: Path,
    builders: Builders,
) -> Mapping[str, list[dict[str, str]]]:
    """Call `kind`'s builder with its spec, its parents' tables and its own `build_id`."""
    bid = step.node.build_id
    assert bid is not None
    steps = resolved.steps
    if kind == PANEL:
        return builders[PANEL](step.spec, resolved.series, bid)
    if kind == PORTFOLIO_PATH:
        return builders[PORTFOLIO_PATH](step.spec, _tables(gold_root, PANEL, steps[PANEL].node.build_id), bid)
    if kind == COVARIANCE:
        return builders[COVARIANCE](step.spec, _tables(gold_root, PANEL, steps[PANEL].node.build_id), bid)
    return builders[RISK_CONTRIBUTION](
        step.spec,
        _tables(gold_root, COVARIANCE, steps[COVARIANCE].node.build_id),
        _tables(gold_root, PORTFOLIO_PATH, steps[PORTFOLIO_PATH].node.build_id),
        bid,
    )


def run(
    target: Path,
    lock: Path,
    factor_store: Path,
    gold_root: Path,
    *,
    commit: str,
    builders: Builders,
    environment: Mapping[str, str],
) -> Plan:
    """§7: plan, then build each `missing` or `pending` mart node in order, verifying each before the
    next, and return the final plan, in which every mart node is `present`. A pending child's recipe is
    resolved from its parents once they are built. Nothing that is `present` is rebuilt, so a second
    run writes nothing and returns the same plan."""
    _check_builders(builders)
    gold_root = Path(gold_root)
    resolved = _resolve(target, lock, factor_store, gold_root, commit, environment)
    for kind in list(resolved.steps):
        step = resolved.steps[kind]
        if step.node.status == PRESENT:
            continue
        assert step.recipe is not None and step.node.build_id is not None
        rows = _rows(kind, step, resolved, gold_root, builders)
        _write(gold_root, kind, step.recipe, rows)
        resolved = _resolve(
            target, lock, factor_store, gold_root, commit, environment
        )  # children resolve now
    final = resolved.plan
    not_built = [f"{n.kind} {n.name}" for n in final.marts if n.status != PRESENT]
    if not_built:
        raise ValueError(f"after the run these are not present: {not_built}")
    return final


def verify(
    target: Path,
    lock: Path,
    factor_store: Path,
    gold_root: Path,
    *,
    commit: str,
    builders: Builders,
    environment: Mapping[str, str],
) -> Plan:
    """§7: plan, and refuse (`ValueError`) unless every mart node is `present`."""
    result = plan(
        target, lock, factor_store, gold_root, commit=commit, builders=builders, environment=environment
    )
    absent = [f"{n.kind} {n.name} is {n.status}" for n in result.marts if n.status != PRESENT]
    if absent:
        raise ValueError("; ".join(absent))
    return result
