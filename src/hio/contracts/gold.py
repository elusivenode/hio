"""Gold marts contract, version 1: bundles, pins, tables, factor-series reader and spec readers.

Built to `docs/decisions/gold-marts-contract.md` (proposed; OD-0233, and §6a under OD-0234).
Section numbers in the docstrings are that document's. Everything here is pure and deterministic:
no clock, no environment, no git, no randomness in any output byte. This module imports no other
`hio` package except `hio.contracts.canonical` and `hio.contracts.silver`, and does not import
NumPy (the float kinds record the NumPy version in their recipe; they do not use it here).
"""

from __future__ import annotations

import csv
import io
import json
import math
import os
import re
import shutil
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Context, Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path
from typing import Any

import yaml

from hio.contracts.canonical import canonical_json, sha256_hex
from hio.contracts.silver import DIR_MODE, FILE_MODE, header_line

SCHEMA = "hio.gold/1"
NUMERIC_POLICY = "decimal-50/1"
CTX = Context(prec=50)

# §6a: the two kinds computed in IEEE float64 through NumPy. Their recipe carries `environment`.
FLOAT_POLICY = "float64/1"
FLOAT_KINDS: tuple[str, ...] = ("covariance", "risk_contribution")

KINDS: tuple[str, ...] = ("panel", "portfolio_path", *FLOAT_KINDS)

_SHA256 = re.compile(r"[0-9a-f]{64}")
_BUILD16 = re.compile(r"[0-9a-f]{16}")
_MEMBER_CODE = re.compile(r"[a-z][a-z0-9_]*")

# --------------------------------------------------------------------------------------
# Tables (§5, §6)
# --------------------------------------------------------------------------------------

TABLES: dict[str, dict[str, tuple[str, ...]]] = {
    "panel": {
        "bridge_panel_member": (
            "panel_build_id",
            "member_code",
            "column_order",
            "factor_id",
            "spec_version",
            "input_build_id",
            "input_series_sha256",
            "series_class",
            "numeraire",
        ),
        "fact_panel_return": (
            "panel_build_id",
            "member_code",
            "period_start",
            "period_end",
            "return",
            "asset_return",
            "cash_return",
        ),
        "fact_panel_coverage": (
            "panel_build_id",
            "member_code",
            "first_boundary",
            "last_boundary",
            "boundaries",
            "omitted_boundaries",
            "common_first",
            "common_last",
            "months",
        ),
    },
    "portfolio_path": {
        "fact_target_allocation": ("portfolio_build_id", "member_code", "target_weight"),
        "fact_portfolio_return": (
            "portfolio_build_id",
            "period_start",
            "period_end",
            "portfolio_return",
            "wealth_index",
        ),
        "fact_return_contribution": (
            "portfolio_build_id",
            "member_code",
            "period_start",
            "period_end",
            "start_weight",
            "member_return",
            "contribution",
        ),
    },
    "covariance": {
        "dim_window": (
            "covariance_build_id",
            "window_id",
            "window_kind",
            "first_period_end",
            "last_period_end",
            "n_obs",
        ),
        "fact_covariance": (
            "covariance_build_id",
            "window_id",
            "member_i",
            "member_j",
            "covariance",
            "correlation",
        ),
        "fact_volatility": ("covariance_build_id", "window_id", "member_code", "volatility"),
    },
    "risk_contribution": {
        "fact_portfolio_risk": (
            "risk_build_id",
            "window_id",
            "portfolio_variance",
            "portfolio_volatility",
            "diversification_ratio",
            "euler_relative_gap",
        ),
        "fact_risk_contribution": (
            "risk_build_id",
            "window_id",
            "member_code",
            "weight",
            "marginal_contribution",
            "component_contribution",
            "percentage_contribution",
        ),
    },
}

# Kind -> table -> the columns it sorts by, compared as text, most significant first. Ties are
# broken by the whole row in column order, so the result never depends on input order.
SORTS: dict[str, dict[str, tuple[str, ...]]] = {
    "panel": {
        "bridge_panel_member": ("member_code",),
        "fact_panel_return": ("member_code", "period_end"),
        "fact_panel_coverage": ("member_code",),
    },
    "portfolio_path": {
        "fact_target_allocation": ("member_code",),
        "fact_portfolio_return": ("period_end",),
        "fact_return_contribution": ("member_code", "period_end"),
    },
    "covariance": {
        "dim_window": ("window_kind", "last_period_end"),
        "fact_covariance": ("window_id", "member_i", "member_j"),
        "fact_volatility": ("window_id", "member_code"),
    },
    "risk_contribution": {
        "fact_portfolio_risk": ("window_id",),
        "fact_risk_contribution": ("window_id", "member_code"),
    },
}


def _need_sha(label: str, value: object) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ValueError(f"{label} is not a lower-case sha256: {value!r}")
    return value


def _need_text(label: str, value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be non-empty text: {value!r}")
    return value


def _need_keys(label: str, value: object, keys: Iterable[str]) -> Mapping[str, Any]:
    wanted = set(keys)
    if not isinstance(value, Mapping) or set(value) != wanted:
        raise ValueError(f"{label} must have exactly the keys {sorted(wanted)}")
    return value


def _need_kind(kind: object) -> str:
    if not isinstance(kind, str) or kind not in KINDS:
        raise ValueError(f"unknown gold kind: {kind!r}")
    return kind


def _columns(kind: str, table: str) -> tuple[str, ...]:
    _need_kind(kind)
    try:
        return TABLES[kind][table]
    except KeyError:
        raise ValueError(f"unknown {kind} table: {table!r}") from None


def _count(label: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} is not a count: {value!r}")
    return value


# --------------------------------------------------------------------------------------
# Encoding (§2)
# --------------------------------------------------------------------------------------


def decimal_text(value: Decimal) -> str:
    """§2: the text of a result, `format(value, "f")`: no exponent, nothing rounded or normalised
    (trailing zeros are kept). A non-finite value is refused with `ValueError`; anything that is
    not a `Decimal` is a `TypeError`."""
    if not isinstance(value, Decimal):
        raise TypeError(f"not a Decimal: {type(value).__name__}")
    if not value.is_finite():
        raise ValueError(f"non-finite decimal: {value}")
    return format(value, "f")


def float_text(value: float) -> str:
    """§6a: the text of a float result, Python's `repr` of it (the shortest text that reads back
    to the same float). A non-finite value is refused with `ValueError`; anything that is not a
    `float` (an `int`, a `Decimal`, text) is a `TypeError`. A `float` subclass such as NumPy's
    `float64` is written as the plain float it holds."""
    if not isinstance(value, float):
        raise TypeError(f"not a float: {type(value).__name__}")
    if not math.isfinite(value):
        raise ValueError(f"non-finite float: {value}")
    return repr(float(value))


def _render(label: str, columns: Sequence[str], rows: Iterable[Mapping[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(columns)
    wanted = set(columns)
    for number, row in enumerate(rows):
        if set(row) != wanted:
            raise ValueError(f"{label} row {number}: columns {sorted(row)} differ from {sorted(wanted)}")
        for column in columns:
            if not isinstance(row[column], str):
                raise ValueError(f"{label} row {number}: {column} is not text: {row[column]!r}")
        writer.writerow([row[column] for column in columns])
    return buffer.getvalue().encode("utf-8")


def _parse(label: str, columns: Sequence[str], data: bytes) -> list[dict[str, str]]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{label}: not UTF-8: {exc}") from exc
    try:
        parsed = list(csv.reader(io.StringIO(text, newline=""), strict=True))
    except csv.Error as exc:
        raise ValueError(f"{label}: malformed CSV: {exc}") from exc
    if not parsed or parsed[0] != list(columns):
        raise ValueError(f"{label}: header is not {','.join(columns)}")
    out: list[dict[str, str]] = []
    for number, cells in enumerate(parsed[1:]):
        if len(cells) != len(columns):
            raise ValueError(f"{label} row {number}: {len(cells)} cells, expected {len(columns)}")
        out.append(dict(zip(columns, cells, strict=True)))
    return out


def _sorted_rows(kind: str, table: str, rows: Iterable[Mapping[str, str]]) -> list[dict[str, str]]:
    columns = TABLES[kind][table]
    sort_columns = SORTS[kind][table]

    def key(row: dict[str, str]) -> tuple[Any, ...]:
        return (tuple(row[c] for c in sort_columns), tuple(row[c] for c in columns))

    return sorted((dict(row) for row in rows), key=key)


def table_bytes(kind: str, table: str, rows: Iterable[Mapping[str, str]]) -> bytes:
    """§1, §5 and §6: the table's CSV file.

    Every row must have exactly the table's columns and only `str` cells (else `ValueError`).
    Rows are sorted by the table's `SORTS` columns, compared as text, ties by the whole row in
    column order; they are written as UTF-8 with `lineterminator="\\n"`, minimal quoting and the
    header first. The result never depends on input order.
    """
    columns = _columns(kind, table)
    listed = list(rows)
    _render(table, columns, listed)  # validates before sorting, so a bad row is named as such
    return _render(table, columns, _sorted_rows(kind, table, listed))


def parse_table(kind: str, table: str, data: bytes) -> list[dict[str, str]]:
    """The rows of a table's CSV bytes, in file order; refuses a wrong header or a ragged row.

    `table_bytes(kind, table, parse_table(kind, table, data))` reproduces `data` when `data` was
    written by `table_bytes`.
    """
    return _parse(table, _columns(kind, table), data)


# --------------------------------------------------------------------------------------
# Recipe and manifest (§3)
# --------------------------------------------------------------------------------------

_PARAMETER_KEYS: dict[str, tuple[str, ...]] = {
    "panel": ("frequency", "alignment", "incomplete_periods", "members"),
    "portfolio_path": ("panel", "rebalance", "weights"),
    "covariance": ("panel", "estimator", "ddof", "annualisation", "trailing_months"),
    "risk_contribution": ("portfolio", "covariance"),
}
_RECIPE_KEYS = ("schema", "kind", "spec", "parameters", "parents", "numeric_policy", "code_commit")
_ENVIRONMENT_KEYS = ("numpy", "python")
# §6a: the (role, kind) of each parent of a float kind, sorted by role.
_FLOAT_PARENTS: dict[str, list[tuple[str, str]]] = {
    "covariance": [("panel", "panel")],
    "risk_contribution": [("covariance", "covariance"), ("portfolio", "portfolio_path")],
}
_BUNDLE_PARENT_KEYS = ("role", "kind", "id", "payload_sha256")
_FACTOR_PARENT_KEYS = (*_BUNDLE_PARENT_KEYS, "factor_id", "spec_version")
_TABLE_ENTRY_KEYS = ("name", "header_sha256", "file_sha256", "rows")


def _json_copy(label: str, value: object) -> Any:
    try:
        return json.loads(canonical_json(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} is not canonical JSON: {exc}") from exc


def _check_spec(spec: object) -> dict[str, str]:
    entry = _need_keys("recipe spec", spec, ("name", "version", "sha256"))
    _need_text("recipe spec name", entry["name"])
    _need_text("recipe spec version", entry["version"])
    _need_sha("recipe spec sha256", entry["sha256"])
    return {"name": entry["name"], "version": entry["version"], "sha256": entry["sha256"]}


def _check_trailing_months(label: str, value: object) -> int | None:
    """§6a: `trailing_months` is an integer of at least 2, or null. A boolean is not an integer."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 2:
        raise ValueError(f"{label} must be an integer of at least 2, or null: {value!r}")
    return value


def _check_int(label: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer: {value!r}")
    return value


def _check_parameters(kind: str, parameters: object) -> dict[str, Any]:
    _need_keys(f"{kind} parameters", parameters, _PARAMETER_KEYS[kind])
    assert isinstance(parameters, Mapping)
    copy = _json_copy("parameters", parameters)
    if kind in ("panel", "portfolio_path"):
        inner = "members" if kind == "panel" else "weights"
        mapping = copy[inner]
        if not isinstance(mapping, dict) or not all(isinstance(v, str) for v in mapping.values()):
            raise ValueError(f"parameters.{inner} must map text to text")
    elif kind == "covariance":
        for key in ("panel", "estimator"):
            _need_text(f"covariance parameters.{key}", copy[key])
        _check_int("covariance parameters.ddof", copy["ddof"])
        _check_int("covariance parameters.annualisation", copy["annualisation"])
        _check_trailing_months("covariance parameters.trailing_months", copy["trailing_months"])
    else:
        for key in _PARAMETER_KEYS[kind]:
            _need_text(f"{kind} parameters.{key}", copy[key])
    return copy


def _check_environment(environment: object) -> dict[str, str]:
    """§6a: exactly `{numpy, python}`, each non-empty text."""
    entry = _need_keys("recipe environment", environment, _ENVIRONMENT_KEYS)
    for key in _ENVIRONMENT_KEYS:
        _need_text(f"recipe environment.{key}", entry[key])
    return {key: entry[key] for key in _ENVIRONMENT_KEYS}


def _check_parent(parent: object) -> dict[str, str]:
    if not isinstance(parent, Mapping) or parent.get("kind") not in (*KINDS, "factor_series"):
        raise ValueError(f"parent kind must be one of {[*KINDS, 'factor_series']}: {parent!r}")
    if parent["kind"] == "factor_series":
        entry = _need_keys("factor_series parent", parent, _FACTOR_PARENT_KEYS)
        _need_text("parent factor_id", entry["factor_id"])
        _need_text("parent spec_version", entry["spec_version"])
        _need_text("parent id", entry["id"])
    else:
        entry = _need_keys("bundle parent", parent, _BUNDLE_PARENT_KEYS)
        _need_sha("parent id", entry["id"])
    _need_text("parent role", entry["role"])
    _need_sha("parent payload_sha256", entry["payload_sha256"])
    return {key: entry[key] for key in entry}


def _check_recipe(recipe: object) -> dict[str, Any]:
    """Refuse (`ValueError`) a recipe that is not of the §3 shape; return a copy."""
    # A float kind has one more key, `environment`; a decimal kind must not have it (§6a).
    hint = recipe.get("kind") if isinstance(recipe, Mapping) else None
    is_float = isinstance(hint, str) and hint in FLOAT_KINDS
    _need_keys("recipe", recipe, (*_RECIPE_KEYS, "environment") if is_float else _RECIPE_KEYS)
    assert isinstance(recipe, Mapping)
    if recipe["schema"] != SCHEMA:
        raise ValueError(f"recipe schema is not {SCHEMA}: {recipe['schema']!r}")
    kind = _need_kind(recipe["kind"])
    policy = FLOAT_POLICY if is_float else NUMERIC_POLICY
    if recipe["numeric_policy"] != policy:
        raise ValueError(f"recipe numeric_policy is not {policy}: {recipe['numeric_policy']!r}")
    if not isinstance(recipe["code_commit"], str):
        raise ValueError("recipe code_commit is not text")
    parents_in = recipe["parents"]
    if not isinstance(parents_in, list):
        raise ValueError("recipe parents must be a list")
    parents = [_check_parent(p) for p in parents_in]
    roles = [p["role"] for p in parents]
    if len(set(roles)) != len(roles):
        raise ValueError(
            f"recipe parents repeat a role: {sorted(r for r in set(roles) if roles.count(r) > 1)}"
        )
    if roles != sorted(roles):
        raise ValueError("recipe parents are not sorted by role")
    if is_float:
        shape = [(p["role"], p["kind"]) for p in parents]
        if shape != _FLOAT_PARENTS[kind]:
            raise ValueError(f"{kind} parents must be exactly (role, kind) {_FLOAT_PARENTS[kind]}: {shape}")
    checked: dict[str, Any] = {
        "schema": SCHEMA,
        "kind": kind,
        "spec": _check_spec(recipe["spec"]),
        "parameters": _check_parameters(kind, recipe["parameters"]),
        "parents": parents,
        "numeric_policy": policy,
        "code_commit": recipe["code_commit"],
    }
    if is_float:
        checked["environment"] = _check_environment(recipe["environment"])
    return checked


def recipe(
    kind: str,
    spec: Mapping[str, str],
    parameters: Mapping[str, Any],
    parents: Iterable[Mapping[str, str]],
    code_commit: str,
    *,
    environment: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """§3 and §6a: the recipe of a build, validated.

    `kind` is `panel`, `portfolio_path`, `covariance` or `risk_contribution`; `spec` is exactly
    `{name, version, sha256}`; `parameters` has exactly the spec's calculation keys (`frequency,
    alignment, incomplete_periods, members` for a panel; `panel, rebalance, weights` for a
    portfolio path; `panel, estimator, ddof, annualisation, trailing_months` for a covariance;
    `portfolio, covariance` for a risk contribution), with `members` or `weights` mapping text to
    text. Each parent has `role`, `kind`, `id` and `payload_sha256`; a `factor_series` parent also
    has `factor_id` and `spec_version` and no other key, and a bundle parent's `kind` is a gold
    kind and its `id` a 64-hex build id. Parents are sorted by `role`; a repeated role is refused.

    A decimal kind (`panel`, `portfolio_path`) takes no `environment`, has no `environment` key
    and `numeric_policy` `NUMERIC_POLICY`. A float kind (`FLOAT_KINDS`) requires `environment`,
    exactly `{numpy, python}` of non-empty text, stored under `environment`, with `numeric_policy`
    `FLOAT_POLICY`; its parents are bundle parents: a `covariance` has exactly one (role `panel`,
    kind `panel`), a `risk_contribution` exactly two (role `covariance` kind `covariance`, role
    `portfolio` kind `portfolio_path`). Refusals are `ValueError`.
    """
    kind = _need_kind(kind)
    listed = [dict(p) if isinstance(p, Mapping) else p for p in parents]
    for parent in listed:
        _check_parent(parent)
    ordered = sorted(listed, key=lambda p: p["role"])
    body: dict[str, Any] = {
        "schema": SCHEMA,
        "kind": kind,
        "spec": spec,
        "parameters": parameters,
        "parents": ordered,
        "numeric_policy": FLOAT_POLICY if kind in FLOAT_KINDS else NUMERIC_POLICY,
        "code_commit": code_commit,
    }
    if kind in FLOAT_KINDS:
        if environment is None:
            raise ValueError(f"a {kind} recipe requires an environment {{numpy, python}}")
        body["environment"] = environment
    elif environment is not None:
        raise ValueError(f"a {kind} recipe takes no environment")
    return _check_recipe(body)


def build_id(recipe: Mapping[str, Any]) -> str:
    """§3: the sha256 of the recipe's canonical JSON: 64 hex characters, never shortened. The
    recipe is validated first (`ValueError` on a malformed one)."""
    return sha256_hex(canonical_json(_check_recipe(recipe)))


def _table_entries(kind: str, tables: Mapping[str, bytes]) -> list[dict[str, Any]]:
    unknown = sorted(set(tables) - set(TABLES[kind]))
    missing = sorted(set(TABLES[kind]) - set(tables))
    if unknown:
        raise ValueError(f"unknown {kind} tables: {unknown}")
    if missing:
        raise ValueError(f"missing {kind} tables: {missing}")
    entries = []
    for name in sorted(tables):
        data = tables[name]
        if not isinstance(data, bytes):
            raise ValueError(f"table {name}: bytes expected")
        rows = parse_table(kind, name, data)  # refuses a wrong header
        entries.append(
            {
                "name": name,
                "header_sha256": sha256_hex(header_line(TABLES[kind][name])[:-1]),
                "file_sha256": sha256_hex(data),
                "rows": len(rows),
            }
        )
    return entries


def _payload_sha256(entries: Sequence[Mapping[str, Any]]) -> str:
    return sha256_hex(canonical_json(list(entries)))


def manifest(recipe: Mapping[str, Any], tables: Mapping[str, bytes]) -> dict[str, Any]:
    """§3: `{"build_id", "recipe", "tables", "payload_sha256"}`.

    `tables` maps every table name of the recipe's kind (no more, no fewer) to its file bytes;
    each entry is `{name, header_sha256, file_sha256, rows}`, sorted by name, computed from the
    bytes (a wrong header is refused). `payload_sha256` is the sha256 of the canonical JSON of
    the `tables` list.
    """
    checked = _check_recipe(recipe)
    entries = _table_entries(checked["kind"], tables)
    return {
        "build_id": build_id(checked),
        "recipe": checked,
        "tables": entries,
        "payload_sha256": _payload_sha256(entries),
    }


def manifest_bytes(manifest: Mapping[str, Any]) -> bytes:
    """§3: `manifest.json`: the manifest written with indent 1, sorted keys and a trailing newline."""
    return (json.dumps(manifest, indent=1, sort_keys=True) + "\n").encode("utf-8")


# --------------------------------------------------------------------------------------
# Bundle directory (§3)
# --------------------------------------------------------------------------------------


def _bundle_files(manifest_: Mapping[str, Any], tables: Mapping[str, bytes]) -> dict[str, bytes]:
    files = {"manifest.json": manifest_bytes(manifest_)}
    for name, data in tables.items():
        files[f"tables/{name}.csv"] = data
    return files


def _read_bundle(bundle_dir: Path) -> dict[str, bytes]:
    if bundle_dir.is_symlink() or not bundle_dir.is_dir():
        raise ValueError(f"not a bundle directory: {bundle_dir}")
    files: dict[str, bytes] = {}
    for path in sorted(bundle_dir.rglob("*")):
        relative = path.relative_to(bundle_dir).as_posix()
        if path.is_symlink():
            raise ValueError(f"unexpected symbolic link: {relative}")
        if path.is_dir():
            if relative != "tables":
                raise ValueError(f"unexpected directory: {relative}")
            continue
        if not path.is_file():
            raise ValueError(f"unexpected entry: {relative}")
        files[relative] = path.read_bytes()
    return files


def _same_bundle(target: Path, files: Mapping[str, bytes]) -> bool:
    try:
        existing = _read_bundle(target)
    except ValueError:
        return False
    return existing == dict(files)


def write_bundle(
    gold_root: Path, recipe: Mapping[str, Any], tables: Mapping[str, bytes]
) -> tuple[Path, bool]:
    """§3: write `<gold_root>/<kind>/<build_id>/` and return `(directory, already_there)`.

    The manifest is built from `recipe` and `tables` (so the recipe, the table names and every
    header are checked before anything is written). The bundle is built in a temporary sibling
    directory and renamed into place; files are mode 0600 and directories 0700. If the directory
    already exists with identical bytes the result is `(directory, True)` and nothing is
    changed; if it exists with different bytes the write is refused with `ValueError`. Nothing is
    overwritten. This does not check where `gold_root` is: callers do.
    """
    built = manifest(recipe, tables)
    kind = built["recipe"]["kind"]
    bid = built["build_id"]
    files = _bundle_files(built, tables)
    kind_dir = gold_root / kind
    target = kind_dir / bid
    if target.exists() or target.is_symlink():
        if _same_bundle(target, files):
            return target, True
        raise ValueError(f"bundle {bid} already exists with different bytes: {target}")
    gold_root.mkdir(mode=DIR_MODE, parents=True, exist_ok=True)
    kind_dir.mkdir(mode=DIR_MODE, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix=".tmp-", dir=kind_dir))
    try:
        os.chmod(scratch, DIR_MODE)
        (scratch / "tables").mkdir(mode=DIR_MODE)
        os.chmod(scratch / "tables", DIR_MODE)
        for relative, data in files.items():
            descriptor = os.open(scratch / relative, os.O_WRONLY | os.O_CREAT | os.O_EXCL, FILE_MODE)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
            os.chmod(scratch / relative, FILE_MODE)
        try:
            scratch.rename(target)
        except OSError:
            # Another writer got there first (or the name is taken): accept only identical bytes.
            if target.exists() and _same_bundle(target, files):
                return target, True
            raise ValueError(f"bundle {bid} already exists with different bytes: {target}") from None
    finally:
        if scratch.exists():
            shutil.rmtree(scratch)
    return target, False


def _check_entries(kind: str, entries: object) -> list[dict[str, Any]]:
    if not isinstance(entries, list):
        raise ValueError("manifest tables must be a list")
    names = []
    for entry in entries:
        _need_keys("manifest tables entry", entry, _TABLE_ENTRY_KEYS)
        _need_sha(f"table {entry['name']} header_sha256", entry["header_sha256"])
        _need_sha(f"table {entry['name']} file_sha256", entry["file_sha256"])
        _count(f"table {entry['name']} rows", entry["rows"])
        names.append(entry["name"])
    if names != sorted(TABLES[kind]):
        raise ValueError(f"manifest tables must list exactly {sorted(TABLES[kind])}, sorted by name")
    return entries


def verify_bundle(bundle_dir: Path) -> dict[str, Any]:
    """§3: check a bundle directory and return its manifest.

    Checks, refusing with `ValueError` naming the first problem: the manifest is of the §3
    shape and its recipe is valid; the manifest's `build_id` equals the one recomputed from the
    recipe; the directory's name equals `build_id`; the directory's parent is named for the
    recipe's kind; `manifest.json` is in its canonical rendering; exactly the manifest's tables
    are present (no missing and no extra file or directory, no symbolic link); each file's
    sha256, header and row count match the manifest; `payload_sha256` is recomputed and equal.
    """
    bundle_dir = Path(bundle_dir)
    files = _read_bundle(bundle_dir)
    if "manifest.json" not in files:
        raise ValueError("missing file: manifest.json")
    try:
        manifest_ = json.loads(files["manifest.json"])
    except ValueError as exc:
        raise ValueError(f"manifest.json is not JSON: {exc}") from exc
    _need_keys("manifest", manifest_, ("build_id", "recipe", "tables", "payload_sha256"))
    recipe_ = _check_recipe(manifest_["recipe"])
    kind = recipe_["kind"]
    recomputed = build_id(recipe_)
    if manifest_["build_id"] != recomputed:
        raise ValueError(f"build_id {manifest_['build_id']!r} does not match the recipe ({recomputed})")
    named = bundle_dir.resolve()
    if named.name != recomputed:
        raise ValueError(f"directory name {named.name!r} is not the build_id {recomputed}")
    if named.parent.name != kind:
        raise ValueError(f"directory kind {named.parent.name!r} is not the recipe's kind {kind!r}")
    entries = _check_entries(kind, manifest_["tables"])
    _need_sha("payload_sha256", manifest_["payload_sha256"])
    if files["manifest.json"] != manifest_bytes(manifest_):
        raise ValueError("manifest.json is not in the canonical rendering")
    expected = {"manifest.json", *(f"tables/{e['name']}.csv" for e in entries)}
    for path in sorted(expected - set(files)):
        raise ValueError(f"missing file: {path}")
    for path in sorted(set(files) - expected):
        raise ValueError(f"unexpected file: {path}")
    for entry in entries:
        name = entry["name"]
        data = files[f"tables/{name}.csv"]
        if sha256_hex(data) != entry["file_sha256"]:
            raise ValueError(f"table {name}: file sha256 differs from the manifest")
        if not data.startswith(header_line(TABLES[kind][name])):
            raise ValueError(f"table {name}: header is not {','.join(TABLES[kind][name])}")
        if sha256_hex(header_line(TABLES[kind][name])[:-1]) != entry["header_sha256"]:
            raise ValueError(f"table {name}: header sha256 differs from the manifest")
        rows = len(parse_table(kind, name, data))
        if rows != entry["rows"]:
            raise ValueError(f"table {name}: {rows} rows, the manifest says {entry['rows']}")
    if _payload_sha256(entries) != manifest_["payload_sha256"]:
        raise ValueError("payload_sha256 does not match the tables")
    return manifest_


@dataclass(frozen=True)
class Bundle:
    """A verified gold bundle (§3, §9). Build one with `open_bundle`; reading never builds."""

    directory: Path
    kind: str
    build_id: str
    payload_sha256: str
    recipe: dict[str, Any]
    manifest: dict[str, Any]

    def table(self, name: str) -> list[dict[str, str]]:
        """The rows of table `name` as dicts of text, in file order. The file is checked against
        the manifest's sha256 on every read, so a bundle changed after opening is refused."""
        columns = _columns(self.kind, name)
        data = (self.directory / "tables" / f"{name}.csv").read_bytes()
        entry = next(e for e in self.manifest["tables"] if e["name"] == name)
        if sha256_hex(data) != entry["file_sha256"]:
            raise ValueError(f"table {name}: file sha256 differs from the manifest")
        return _parse(name, columns, data)

    def decimals(self, table: str, column: str) -> list[Decimal]:
        """One column of `table` as `Decimal`, in file order. An empty cell, text that is not a
        decimal, or a non-finite value is refused with `ValueError`; an unknown column too."""
        if column not in _columns(self.kind, table):
            raise ValueError(f"table {table} has no column {column!r}")
        out: list[Decimal] = []
        for number, row in enumerate(self.table(table)):
            cell = row[column]
            if cell == "":
                raise ValueError(f"{table} row {number}: {column} is empty")
            try:
                value = Decimal(cell)
            except InvalidOperation:
                raise ValueError(f"{table} row {number}: {column} is not a decimal: {cell!r}") from None
            if not value.is_finite():
                raise ValueError(f"{table} row {number}: {column} is not finite: {cell!r}")
            out.append(value)
        return out

    def floats(self, table: str, column: str) -> list[float]:
        """§6a: one column of `table` as `float`, in file order (`float(text)`; a float cell is
        `repr` text, so the value read back is the value written). An empty cell, text that is
        not a number, or a non-finite value is refused with `ValueError`; an unknown column too."""
        if column not in _columns(self.kind, table):
            raise ValueError(f"table {table} has no column {column!r}")
        out: list[float] = []
        for number, row in enumerate(self.table(table)):
            cell = row[column]
            if cell == "":
                raise ValueError(f"{table} row {number}: {column} is empty")
            try:
                value = float(cell)
            except ValueError:
                raise ValueError(f"{table} row {number}: {column} is not a float: {cell!r}") from None
            if not math.isfinite(value):
                raise ValueError(f"{table} row {number}: {column} is not finite: {cell!r}")
            out.append(value)
        return out


def open_bundle(gold_root: Path, kind: str, build_id: str) -> Bundle:
    """§9: verify `<gold_root>/<kind>/<build_id>/` (as `verify_bundle`) and return it.

    `build_id` must be the full 64-hex id (an exact identity, never "latest" or a prefix).
    """
    _need_kind(kind)
    _need_sha("build_id", build_id)
    directory = Path(gold_root) / kind / build_id
    manifest_ = verify_bundle(directory)
    return Bundle(
        directory=directory,
        kind=kind,
        build_id=manifest_["build_id"],
        payload_sha256=manifest_["payload_sha256"],
        recipe=manifest_["recipe"],
        manifest=manifest_,
    )


# --------------------------------------------------------------------------------------
# Factor series (§4)
# --------------------------------------------------------------------------------------

_SERIES_CLASS_COLUMNS: dict[str, tuple[str, ...]] = {
    "total_return": ("total_return",),
    "excess": ("asset_return", "cash_return", "excess_return"),
}
_SERIES_LEADING = ("period_start", "period_end")


@dataclass(frozen=True)
class FactorSeries:
    """A verified factor series (§4): the record, the header and the rows as dicts of text."""

    factor_id: str
    spec_version: str
    build_id: str
    series_sha256: str
    series_class: str
    numeraire: str
    record: dict[str, Any]
    columns: tuple[str, ...]
    rows: list[dict[str, str]]

    def parent(self, role: str) -> dict[str, str]:
        """§3: this series as a recipe parent: `kind` `factor_series`, `id` the `build_id`,
        `payload_sha256` the `series_sha256`, plus `factor_id` and `spec_version`."""
        return {
            "role": role,
            "kind": "factor_series",
            "id": self.build_id,
            "payload_sha256": self.series_sha256,
            "factor_id": self.factor_id,
            "spec_version": self.spec_version,
        }


def _path_part(label: str, value: object) -> str:
    if not isinstance(value, str) or value in {"", ".", ".."} or "/" in value or "\\" in value:
        raise ValueError(f"{label} is not a single path component: {value!r}")
    return value


def read_factor_series(
    factor_store: Path,
    factor_id: str,
    spec_version: str,
    build_id: str,
    *,
    series_sha256: str | None = None,
) -> FactorSeries:
    """§4: read `<factor_store>/<factor_id>/<spec_version>/<build_id>/` after checking it.

    Refuses (`ValueError`, naming the first problem): a missing directory or file; a `build.json`
    that is not JSON or whose `factor_id`, `spec_version` or `build_id` differ from the
    directory's names; a `series.csv` whose sha256 differs from the record's `series_sha256`
    (or from the `series_sha256` argument when given); a `series_class` that is not
    `total_return` or `excess`; a record with no non-empty `numeraire`; a header that does not
    start `period_start,period_end`, repeats a column, or lacks the columns the class needs
    (`total_return`; or `asset_return`, `cash_return`, `excess_return`); a ragged row. Rows are
    dicts of text in file order.
    """
    _path_part("factor_id", factor_id)
    _path_part("spec_version", spec_version)
    _path_part("build_id", build_id)
    directory = Path(factor_store) / factor_id / spec_version / build_id
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError(f"not a factor build directory: {directory}")
    record_path = directory / "build.json"
    series_path = directory / "series.csv"
    for path in (record_path, series_path):
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"missing file: {path.name}")
    try:
        record = json.loads(record_path.read_bytes())
    except ValueError as exc:
        raise ValueError(f"build.json is not JSON: {exc}") from exc
    if not isinstance(record, dict):
        raise ValueError("build.json is not an object")
    for key, expected in (("factor_id", factor_id), ("spec_version", spec_version), ("build_id", build_id)):
        if record.get(key) != expected:
            raise ValueError(f"build.json {key} {record.get(key)!r} differs from the directory {expected!r}")
    recorded = _need_sha("build.json series_sha256", record.get("series_sha256"))
    if series_sha256 is not None and series_sha256 != recorded:
        raise ValueError(f"series_sha256 {series_sha256!r} differs from the record's {recorded}")
    data = series_path.read_bytes()
    if sha256_hex(data) != recorded:
        raise ValueError("series.csv sha256 differs from the record's series_sha256")
    series_class = record.get("series_class")
    if not isinstance(series_class, str) or series_class not in _SERIES_CLASS_COLUMNS:
        raise ValueError(f"series_class must be total_return or excess: {series_class!r}")
    numeraire = _need_text("build.json numeraire", record.get("numeraire"))
    try:
        parsed = list(csv.reader(io.StringIO(data.decode("utf-8"), newline=""), strict=True))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ValueError(f"series.csv is not UTF-8 CSV: {exc}") from exc
    if not parsed:
        raise ValueError("series.csv is empty")
    header = tuple(parsed[0])
    if header[:2] != _SERIES_LEADING:
        raise ValueError(f"series.csv header must start {','.join(_SERIES_LEADING)}")
    if len(set(header)) != len(header):
        raise ValueError("series.csv header repeats a column")
    for column in _SERIES_CLASS_COLUMNS[series_class]:
        if column not in header:
            raise ValueError(f"series.csv has no {column} column, which a {series_class} series needs")
    rows: list[dict[str, str]] = []
    for number, cells in enumerate(parsed[1:]):
        if len(cells) != len(header):
            raise ValueError(f"series.csv row {number}: {len(cells)} cells, expected {len(header)}")
        rows.append(dict(zip(header, cells, strict=True)))
    return FactorSeries(
        factor_id=factor_id,
        spec_version=spec_version,
        build_id=build_id,
        series_sha256=recorded,
        series_class=series_class,
        numeraire=numeraire,
        record=record,
        columns=header,
        rows=rows,
    )


# --------------------------------------------------------------------------------------
# Specs and the lock (§4, §5, §6)
# --------------------------------------------------------------------------------------


def _load_yaml(path: Path) -> tuple[dict[str, Any], str]:
    data = Path(path).read_bytes()
    try:
        loaded = yaml.safe_load(data)
    except yaml.YAMLError as exc:
        raise ValueError(f"{path}: not YAML: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ValueError(f"{path}: must be a mapping")
    return loaded, sha256_hex(data)


def _identity(label: str, value: object) -> dict[str, str]:
    entry = _need_keys(f"{label} identity", value, ("name", "version", "status"))
    for key in ("name", "version", "status"):
        _need_text(f"{label} identity.{key}", entry[key])
    return {key: entry[key] for key in ("name", "version", "status")}


def _member_codes(label: str, mapping: object) -> dict[str, Any]:
    if not isinstance(mapping, dict) or not mapping:
        raise ValueError(f"{label} must be a non-empty mapping")
    for code in mapping:
        if not isinstance(code, str) or not _MEMBER_CODE.fullmatch(code):
            raise ValueError(f"{label}: member code {code!r} does not match [a-z][a-z0-9_]*")
    return mapping


def _only(label: str, value: object, allowed: str) -> str:
    if value != allowed:
        raise ValueError(f"{label} must be {allowed!r}: {value!r}")
    return allowed


def read_lock(path: Path) -> dict[str, Any]:
    """§4: read a lock file (`specs/gold/locks/<name>.yaml`).

    Exact keys `identity` and `factor_series`; `identity` is exactly `{name, version, status}`
    of non-empty text; each `factor_series` entry (keyed by a non-empty factor id) is exactly
    `{spec_version: text, build_id: 16 lower-case hex, series_sha256: 64 lower-case hex}`.
    Returns `{name, version, status, factor_series, sha256}` where `sha256` is the file's.
    Refusals are `ValueError`.
    """
    loaded, digest = _load_yaml(path)
    _need_keys("lock", loaded, ("identity", "factor_series"))
    identity = _identity("lock", loaded["identity"])
    series = loaded["factor_series"]
    if not isinstance(series, dict):
        raise ValueError("lock factor_series must be a mapping")
    pins: dict[str, dict[str, str]] = {}
    for factor_id, entry in series.items():
        _need_text("lock factor id", factor_id)
        _need_keys(f"lock entry {factor_id}", entry, ("spec_version", "build_id", "series_sha256"))
        _need_text(f"lock entry {factor_id} spec_version", entry["spec_version"])
        if not isinstance(entry["build_id"], str) or not _BUILD16.fullmatch(entry["build_id"]):
            raise ValueError(
                f"lock entry {factor_id} build_id is not 16 lower-case hex: {entry['build_id']!r}"
            )
        _need_sha(f"lock entry {factor_id} series_sha256", entry["series_sha256"])
        pins[factor_id] = {
            "spec_version": entry["spec_version"],
            "build_id": entry["build_id"],
            "series_sha256": entry["series_sha256"],
        }
    return {**identity, "factor_series": pins, "sha256": digest}


def lock_pin(lock: Mapping[str, Any], factor_id: str) -> dict[str, str]:
    """§4: the lock's `{spec_version, build_id, series_sha256}` for `factor_id`. Nothing resolves
    "latest": a factor with no entry is refused with `ValueError`."""
    try:
        return dict(lock["factor_series"][factor_id])
    except KeyError:
        raise ValueError(f"lock has no entry for factor {factor_id!r}") from None


def read_panel_spec(path: Path) -> dict[str, Any]:
    """§5: read a panel spec (`specs/gold/panels/<name>.yaml`).

    Exact keys `identity, kind, frequency, alignment, incomplete_periods, members`; `kind` is
    `panel`, `frequency` is `monthly`, `alignment` is `common_boundaries`, `incomplete_periods`
    is `exclude`; `members` is a non-empty mapping of member code (`[a-z][a-z0-9_]*`) to a
    non-empty factor id. Returns `{name, version, status, kind, frequency, alignment,
    incomplete_periods, members, sha256}`; `sha256` is the file's. Refusals are `ValueError`.
    """
    loaded, digest = _load_yaml(path)
    _need_keys("panel spec", loaded, ("identity", "kind", *_PARAMETER_KEYS["panel"]))
    identity = _identity("panel spec", loaded["identity"])
    _only("panel spec kind", loaded["kind"], "panel")
    _only("panel spec frequency", loaded["frequency"], "monthly")
    _only("panel spec alignment", loaded["alignment"], "common_boundaries")
    _only("panel spec incomplete_periods", loaded["incomplete_periods"], "exclude")
    members = _member_codes("panel spec members", loaded["members"])
    for code, factor_id in members.items():
        _need_text(f"panel spec member {code} factor id", factor_id)
    return {
        **identity,
        "kind": "panel",
        "frequency": "monthly",
        "alignment": "common_boundaries",
        "incomplete_periods": "exclude",
        "members": dict(members),
        "sha256": digest,
    }


def _weight(code: str, value: object) -> Decimal:
    if not isinstance(value, str):
        raise ValueError(f"weight {code} must be a decimal string: {value!r}")
    if value != value.strip() or "_" in value:
        raise ValueError(f"weight {code} is not a decimal string: {value!r}")
    try:
        weight = Decimal(value)
    except InvalidOperation:
        raise ValueError(f"weight {code} is not a decimal string: {value!r}") from None
    if not weight.is_finite():
        raise ValueError(f"weight {code} is not finite: {value!r}")
    if weight.is_signed():
        raise ValueError(f"weight {code} is negative: {value!r}")
    return weight


def read_portfolio_spec(path: Path) -> dict[str, Any]:
    """§6: read a portfolio-path spec (`specs/gold/portfolios/<name>.yaml`).

    Exact keys `identity, kind, panel, rebalance, weights`; `kind` is `portfolio_path`,
    `rebalance` is `month_end`, `panel` is non-empty text; `weights` is a non-empty mapping of
    member code (`[a-z][a-z0-9_]*`) to a string that parses as a finite, non-negative `Decimal`,
    and the weights sum to exactly 1 (summed exactly, not in `CTX`). Returns `{name, version,
    status, kind, panel, rebalance, weights, sha256}` with `weights` as the strings as written
    (they go into the recipe unchanged) and `sha256` the file's. That the weights name exactly
    the panel's members is for the caller, who has the panel. Refusals are `ValueError`.
    """
    loaded, digest = _load_yaml(path)
    _need_keys("portfolio spec", loaded, ("identity", "kind", *_PARAMETER_KEYS["portfolio_path"]))
    identity = _identity("portfolio spec", loaded["identity"])
    _only("portfolio spec kind", loaded["kind"], "portfolio_path")
    _only("portfolio spec rebalance", loaded["rebalance"], "month_end")
    panel = _need_text("portfolio spec panel", loaded["panel"])
    weights = _member_codes("portfolio spec weights", loaded["weights"])
    total = Fraction(0)
    for code, value in weights.items():
        total += Fraction(_weight(code, value))
    if total != 1:
        raise ValueError(f"weights must sum to exactly 1: they sum to {total}")
    return {
        **identity,
        "kind": "portfolio_path",
        "panel": panel,
        "rebalance": "month_end",
        "weights": dict(weights),
        "sha256": digest,
    }


def _only_int(label: str, value: object, allowed: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value != allowed:
        raise ValueError(f"{label} must be {allowed}: {value!r}")
    return allowed


def read_covariance_spec(path: Path) -> dict[str, Any]:
    """§6a: read a covariance spec (`specs/gold/covariances/<name>.yaml`).

    Exact keys `identity, kind, panel, estimator, ddof, annualisation, trailing_months`; `kind`
    is `covariance`, `estimator` is `sample`, `ddof` is the integer 1, `annualisation` is the
    integer 12, `panel` is non-empty text, and `trailing_months` is an integer of at least 2 or
    null (a boolean is not an integer). Returns `{name, version, status, kind, panel, estimator,
    ddof, annualisation, trailing_months, sha256}`; `sha256` is the file's. Refusals are
    `ValueError`.
    """
    loaded, digest = _load_yaml(path)
    _need_keys("covariance spec", loaded, ("identity", "kind", *_PARAMETER_KEYS["covariance"]))
    identity = _identity("covariance spec", loaded["identity"])
    _only("covariance spec kind", loaded["kind"], "covariance")
    panel = _need_text("covariance spec panel", loaded["panel"])
    _only("covariance spec estimator", loaded["estimator"], "sample")
    _only_int("covariance spec ddof", loaded["ddof"], 1)
    _only_int("covariance spec annualisation", loaded["annualisation"], 12)
    trailing = _check_trailing_months("covariance spec trailing_months", loaded["trailing_months"])
    return {
        **identity,
        "kind": "covariance",
        "panel": panel,
        "estimator": "sample",
        "ddof": 1,
        "annualisation": 12,
        "trailing_months": trailing,
        "sha256": digest,
    }


def read_risk_spec(path: Path) -> dict[str, Any]:
    """§6a: read a risk-contribution spec (`specs/gold/risk/<name>.yaml`).

    Exact keys `identity, kind, portfolio, covariance`; `kind` is `risk_contribution`;
    `portfolio` and `covariance` are non-empty text (the names of a portfolio spec and a
    covariance spec). Returns `{name, version, status, kind, portfolio, covariance, sha256}`;
    `sha256` is the file's. Refusals are `ValueError`.
    """
    loaded, digest = _load_yaml(path)
    _need_keys("risk spec", loaded, ("identity", "kind", *_PARAMETER_KEYS["risk_contribution"]))
    identity = _identity("risk spec", loaded["identity"])
    _only("risk spec kind", loaded["kind"], "risk_contribution")
    return {
        **identity,
        "kind": "risk_contribution",
        "portfolio": _need_text("risk spec portfolio", loaded["portfolio"]),
        "covariance": _need_text("risk spec covariance", loaded["covariance"]),
        "sha256": digest,
    }
