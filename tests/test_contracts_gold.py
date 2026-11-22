"""Tests for hio.contracts.gold: the gold marts contract (OD-0233). Invented data only."""

from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import stat
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from hio.contracts import gold

ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / "specs" / "gold"

HEADERS = {
    ("panel", "bridge_panel_member"): (
        "panel_build_id,member_code,column_order,factor_id,spec_version,input_build_id,"
        "input_series_sha256,series_class,numeraire"
    ),
    ("panel", "fact_panel_return"): (
        "panel_build_id,member_code,period_start,period_end,return,asset_return,cash_return"
    ),
    ("panel", "fact_panel_coverage"): (
        "panel_build_id,member_code,first_boundary,last_boundary,boundaries,omitted_boundaries,"
        "common_first,common_last,months"
    ),
    ("portfolio_path", "fact_target_allocation"): "portfolio_build_id,member_code,target_weight",
    ("portfolio_path", "fact_portfolio_return"): (
        "portfolio_build_id,period_start,period_end,portfolio_return,wealth_index"
    ),
    ("portfolio_path", "fact_return_contribution"): (
        "portfolio_build_id,member_code,period_start,period_end,start_weight,member_return,contribution"
    ),
    ("covariance", "dim_window"): (
        "covariance_build_id,window_id,window_kind,first_period_end,last_period_end,n_obs"
    ),
    ("covariance", "fact_covariance"): (
        "covariance_build_id,window_id,member_i,member_j,covariance,correlation"
    ),
    ("covariance", "fact_volatility"): "covariance_build_id,window_id,member_code,volatility",
    ("risk_contribution", "fact_portfolio_risk"): (
        "risk_build_id,window_id,portfolio_variance,portfolio_volatility,diversification_ratio,"
        "euler_relative_gap"
    ),
    ("risk_contribution", "fact_risk_contribution"): (
        "risk_build_id,window_id,member_code,weight,marginal_contribution,component_contribution,"
        "percentage_contribution"
    ),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cj(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


SPEC = {"name": "example", "version": "0.1.0", "sha256": sha(b"spec")}
PANEL_PARAMETERS = {
    "frequency": "monthly",
    "alignment": "common_boundaries",
    "incomplete_periods": "exclude",
    "members": {"equity": "some.equity", "bonds": "some.bonds"},
}


def factor_parent(role: str, factor_id: str) -> dict[str, str]:
    return {
        "role": role,
        "kind": "factor_series",
        "id": sha(role.encode())[:16],
        "payload_sha256": sha(factor_id.encode()),
        "factor_id": factor_id,
        "spec_version": "0.1.0",
    }


def panel_recipe(code_commit: str = "c0ffee") -> dict[str, Any]:
    return gold.recipe(
        "panel",
        SPEC,
        PANEL_PARAMETERS,
        [factor_parent("equity", "some.equity"), factor_parent("bonds", "some.bonds")],
        code_commit,
    )


def invented_rows(kind: str, table: str, count: int = 3) -> list[dict[str, str]]:
    return [
        {column: f"{column}-{n}" for column in gold.TABLES[kind][table]}
        for n in range(count, 0, -1)  # deliberately not in sorted order
    ]


def panel_tables() -> dict[str, bytes]:
    return {t: gold.table_bytes("panel", t, invented_rows("panel", t)) for t in gold.TABLES["panel"]}


def write_panel(gold_root: Path, code_commit: str = "c0ffee") -> Path:
    directory, existed = gold.write_bundle(gold_root, panel_recipe(code_commit), panel_tables())
    assert existed is False
    return directory


def rewrite_manifest(directory: Path, mutate) -> None:
    path = directory / "manifest.json"
    body = json.loads(path.read_text())
    mutate(body)
    path.write_bytes(gold.manifest_bytes(body))


def portfolio_recipe() -> dict[str, Any]:
    return gold.recipe(
        "portfolio_path",
        SPEC,
        {"panel": "example", "rebalance": "month_end", "weights": {"equity": "0.60", "bonds": "0.40"}},
        [{"role": "panel", "kind": "panel", "id": sha(b"p"), "payload_sha256": sha(b"q")}],
        "c0ffee",
    )


def portfolio_tables() -> dict[str, bytes]:
    return {
        t: gold.table_bytes("portfolio_path", t, invented_rows("portfolio_path", t))
        for t in gold.TABLES["portfolio_path"]
    }


# Computed from the module before OD-0234 touched it. Adding the float kinds must not move a
# single byte of a panel or portfolio_path bundle: these literals are the proof.
PINNED_IDENTITIES = {
    "panel": (
        "960f633ed5d55042e4e12d54af8ba8681597c9d73fb2638382571c55ceec2230",  # build_id
        "9472e767a140ee9d1938497c95c07d1940d09404777af110a8df5413dbbad000",  # payload_sha256
        "2244c384f3e26cf4d09930cd408a64bdd9d4d6f8b9bbcf65cff1051b24effac3",  # sha256 of manifest.json
    ),
    "portfolio_path": (
        "779a5b386ea46832dd1cfb8be6e8dedd56006ecf44aa34990838b90070ea727c",
        "47974ff2fe4af1758eb17c0987761679f8511da8f9fbb4be8a8f1cc7e56a7328",
        "76b7143bcb98cc601f317addaf0e282ceb1fcfa7433b52b8bea93a1991c1df2b",
    ),
}


@pytest.mark.parametrize("kind", ["panel", "portfolio_path"])
def test_existing_kinds_keep_their_pinned_identities(kind, tmp_path):
    r, tables = (
        (panel_recipe(), panel_tables()) if kind == "panel" else (portfolio_recipe(), portfolio_tables())
    )
    assert "environment" not in r
    assert r["numeric_policy"] == "decimal-50/1"
    built = gold.manifest(r, tables)
    pinned_build, pinned_payload, pinned_manifest = PINNED_IDENTITIES[kind]
    assert built["build_id"] == gold.build_id(r) == pinned_build
    assert built["payload_sha256"] == pinned_payload
    assert sha(gold.manifest_bytes(built)) == pinned_manifest
    directory, _ = gold.write_bundle(tmp_path / "gold", r, tables)
    assert directory.name == pinned_build
    assert sha((directory / "manifest.json").read_bytes()) == pinned_manifest


# --------------------------------------------------------------------------------------
# Constants and tables
# --------------------------------------------------------------------------------------


def test_constants():
    assert gold.SCHEMA == "hio.gold/1"
    assert gold.NUMERIC_POLICY == "decimal-50/1"
    assert gold.CTX.prec == 50
    # OD-0234 appends the two float kinds; the first two are as they were.
    assert gold.KINDS == ("panel", "portfolio_path", "covariance", "risk_contribution")
    assert list(gold.TABLES) == ["panel", "portfolio_path", "covariance", "risk_contribution"]
    assert gold.FLOAT_POLICY == "float64/1"
    assert gold.FLOAT_KINDS == ("covariance", "risk_contribution")


@pytest.mark.parametrize(("kind", "table"), list(HEADERS))
def test_every_header_is_the_literal_contract_text(kind, table):
    assert ",".join(gold.TABLES[kind][table]) == HEADERS[(kind, table)]


def test_tables_are_exactly_the_contract_tables_in_order():
    assert list(gold.TABLES["panel"]) == ["bridge_panel_member", "fact_panel_return", "fact_panel_coverage"]
    assert list(gold.TABLES["portfolio_path"]) == [
        "fact_target_allocation",
        "fact_portfolio_return",
        "fact_return_contribution",
    ]


def test_sorts_are_the_contract_sorts():
    assert gold.SORTS == {
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


# --------------------------------------------------------------------------------------
# decimal_text
# --------------------------------------------------------------------------------------


def test_decimal_text_is_exact_with_no_exponent_and_keeps_trailing_zeros():
    assert gold.decimal_text(Decimal("1.500")) == "1.500"
    assert gold.decimal_text(Decimal("1E+3")) == "1000"
    assert gold.decimal_text(Decimal("1E-7")) == "0.0000001"
    assert gold.decimal_text(Decimal("-0.0250")) == "-0.0250"
    assert gold.decimal_text(Decimal("0.60") * Decimal("0.5")) == "0.300"


def test_decimal_text_refuses_non_finite_and_non_decimal():
    for bad in ("NaN", "Infinity", "-Infinity", "sNaN"):
        with pytest.raises(ValueError, match="non-finite"):
            gold.decimal_text(Decimal(bad))
    with pytest.raises(TypeError):
        gold.decimal_text(1.5)  # type: ignore[arg-type]


# --------------------------------------------------------------------------------------
# table_bytes and parse_table
# --------------------------------------------------------------------------------------


def row(kind: str, table: str, **cells: str) -> dict[str, str]:
    base = {column: "" for column in gold.TABLES[kind][table]}
    assert set(cells) <= set(base)
    return {**base, **cells}


def test_table_bytes_header_and_exact_text():
    rows = [
        row("portfolio_path", "fact_portfolio_return", period_end="2024-02-29", portfolio_return="0.0100"),
    ]
    data = gold.table_bytes("portfolio_path", "fact_portfolio_return", rows)
    assert data == (
        b"portfolio_build_id,period_start,period_end,portfolio_return,wealth_index\n,,2024-02-29,0.0100,\n"
    )


def test_table_bytes_empty_is_header_only():
    for (kind, table), header in HEADERS.items():
        assert gold.table_bytes(kind, table, []) == (header + "\n").encode()
        assert gold.parse_table(kind, table, (header + "\n").encode()) == []


def test_sort_fact_panel_return_by_member_then_period_end_as_text():
    rows = [
        row("panel", "fact_panel_return", member_code="b", period_end="2024-01-31", **{"return": "1"}),
        row("panel", "fact_panel_return", member_code="a", period_end="2024-02-29", **{"return": "2"}),
        row("panel", "fact_panel_return", member_code="a", period_end="2024-01-31", **{"return": "3"}),
        row("panel", "fact_panel_return", member_code="a", period_end="2023-12-31", **{"return": "4"}),
    ]
    parsed = gold.parse_table(
        "panel", "fact_panel_return", gold.table_bytes("panel", "fact_panel_return", rows)
    )
    assert [(r["member_code"], r["period_end"]) for r in parsed] == [
        ("a", "2023-12-31"),
        ("a", "2024-01-31"),
        ("a", "2024-02-29"),
        ("b", "2024-01-31"),
    ]


def test_sort_text_not_numeric_and_ties_by_whole_row():
    rows = [
        row("panel", "bridge_panel_member", member_code="m", column_order="10", factor_id="y"),
        row("panel", "bridge_panel_member", member_code="m", column_order="2", factor_id="z"),
        row("panel", "bridge_panel_member", member_code="m", column_order="2", factor_id="a"),
        row("panel", "bridge_panel_member", member_code="a", column_order="0"),
    ]
    out = gold.parse_table(
        "panel", "bridge_panel_member", gold.table_bytes("panel", "bridge_panel_member", rows)
    )
    assert [(r["member_code"], r["column_order"], r["factor_id"]) for r in out] == [
        ("a", "0", ""),
        ("m", "10", "y"),  # text order: "10" < "2"
        ("m", "2", "a"),
        ("m", "2", "z"),
    ]
    reversed_bytes = gold.table_bytes("panel", "bridge_panel_member", list(reversed(rows)))
    assert reversed_bytes == gold.table_bytes("panel", "bridge_panel_member", rows)


@pytest.mark.parametrize(
    ("kind", "table", "keys"),
    [
        ("panel", "bridge_panel_member", ("member_code",)),
        ("panel", "fact_panel_return", ("member_code", "period_end")),
        ("panel", "fact_panel_coverage", ("member_code",)),
        ("portfolio_path", "fact_target_allocation", ("member_code",)),
        ("portfolio_path", "fact_portfolio_return", ("period_end",)),
        ("portfolio_path", "fact_return_contribution", ("member_code", "period_end")),
        ("covariance", "dim_window", ("window_kind", "last_period_end")),
        ("covariance", "fact_covariance", ("window_id", "member_i", "member_j")),
        ("covariance", "fact_volatility", ("window_id", "member_code")),
        ("risk_contribution", "fact_portfolio_risk", ("window_id",)),
        ("risk_contribution", "fact_risk_contribution", ("window_id", "member_code")),
    ],
)
def test_each_table_sorts_by_its_contract_columns(kind, table, keys):
    rows = invented_rows(kind, table, 4)
    out = gold.parse_table(kind, table, gold.table_bytes(kind, table, rows))
    got = [tuple(r[k] for k in keys) for r in out]
    assert got == sorted(got)
    assert len(out) == 4


@pytest.mark.parametrize(("kind", "table"), list(HEADERS))
def test_round_trip_is_exact(kind, table):
    rows = invented_rows(kind, table)
    data = gold.table_bytes(kind, table, rows)
    parsed = gold.parse_table(kind, table, data)
    assert gold.table_bytes(kind, table, parsed) == data
    assert sorted(parsed, key=lambda r: tuple(r.values())) == sorted(rows, key=lambda r: tuple(r.values()))


def test_round_trip_quoting_and_unicode():
    rows = [row("panel", "bridge_panel_member", member_code="a", factor_id='x,"y"\nz', numeraire="é")]
    data = gold.table_bytes("panel", "bridge_panel_member", rows)
    assert gold.parse_table("panel", "bridge_panel_member", data) == rows
    assert (
        gold.table_bytes(
            "panel", "bridge_panel_member", gold.parse_table("panel", "bridge_panel_member", data)
        )
        == data
    )


def test_table_bytes_refuses_bad_rows_kinds_and_tables():
    good = row("panel", "bridge_panel_member", member_code="a")
    with pytest.raises(ValueError, match="columns"):
        gold.table_bytes("panel", "bridge_panel_member", [{**good, "extra": ""}])
    missing = dict(good)
    del missing["numeraire"]
    with pytest.raises(ValueError, match="columns"):
        gold.table_bytes("panel", "bridge_panel_member", [missing])
    with pytest.raises(ValueError, match="not text"):
        gold.table_bytes("panel", "bridge_panel_member", [{**good, "column_order": 0}])
    with pytest.raises(ValueError, match="not text"):
        gold.table_bytes("panel", "bridge_panel_member", [{**good, "numeraire": Decimal("1")}])
    with pytest.raises(ValueError, match="unknown gold kind"):
        gold.table_bytes("nope", "bridge_panel_member", [])
    with pytest.raises(ValueError, match="unknown panel table"):
        gold.table_bytes("panel", "fact_target_allocation", [])
    with pytest.raises(ValueError, match="unknown panel table"):
        gold.parse_table("panel", "fact_target_allocation", b"")


def test_parse_table_refuses_wrong_header_ragged_row_and_bad_bytes():
    header = HEADERS[("portfolio_path", "fact_target_allocation")]
    with pytest.raises(ValueError, match="header"):
        gold.parse_table("portfolio_path", "fact_target_allocation", b"a,b,c\n")
    with pytest.raises(ValueError, match="header"):
        gold.parse_table("portfolio_path", "fact_target_allocation", b"")
    with pytest.raises(ValueError, match="cells"):
        gold.parse_table("portfolio_path", "fact_target_allocation", f"{header}\nx,y\n".encode())
    with pytest.raises(ValueError, match="UTF-8"):
        gold.parse_table("portfolio_path", "fact_target_allocation", b"\xff\xfe")


# --------------------------------------------------------------------------------------
# recipe, build_id, manifest
# --------------------------------------------------------------------------------------


def test_recipe_shape_and_parent_sort():
    r = panel_recipe()
    assert r == {
        "schema": "hio.gold/1",
        "kind": "panel",
        "spec": SPEC,
        "parameters": PANEL_PARAMETERS,
        "parents": [factor_parent("bonds", "some.bonds"), factor_parent("equity", "some.equity")],
        "numeric_policy": "decimal-50/1",
        "code_commit": "c0ffee",
    }


def test_build_id_is_the_sha256_of_the_canonical_recipe_json():
    r = panel_recipe()
    expected = hashlib.sha256(cj(r)).hexdigest()
    assert gold.build_id(r) == expected
    assert len(expected) == 64
    assert gold.build_id(panel_recipe("other")) != expected
    assert gold.build_id(panel_recipe()) == expected


def test_portfolio_recipe_with_bundle_parent():
    parent = {"role": "panel", "kind": "panel", "id": sha(b"p"), "payload_sha256": sha(b"q")}
    params = {"panel": "example", "rebalance": "month_end", "weights": {"equity": "0.60", "bonds": "0.40"}}
    r = gold.recipe("portfolio_path", SPEC, params, [parent], "c0ffee")
    assert r["kind"] == "portfolio_path"
    assert r["parents"] == [parent]
    assert gold.build_id(r) == sha(cj(r))


def test_recipe_does_not_alias_its_arguments():
    params = json.loads(json.dumps(PANEL_PARAMETERS))
    r = gold.recipe("panel", SPEC, params, [factor_parent("equity", "some.equity")], "x")
    params["members"]["equity"] = "changed"
    assert r["parameters"]["members"]["equity"] == "some.equity"


def test_recipe_refusals():
    parents = [factor_parent("equity", "some.equity")]
    with pytest.raises(ValueError, match="unknown gold kind"):
        gold.recipe("nope", SPEC, PANEL_PARAMETERS, parents, "x")
    with pytest.raises(ValueError, match="spec"):
        gold.recipe("panel", {"name": "a", "version": "1"}, PANEL_PARAMETERS, parents, "x")
    with pytest.raises(ValueError, match="spec"):
        gold.recipe("panel", {**SPEC, "extra": "x"}, PANEL_PARAMETERS, parents, "x")
    with pytest.raises(ValueError, match="sha256"):
        gold.recipe("panel", {**SPEC, "sha256": "ABC"}, PANEL_PARAMETERS, parents, "x")
    with pytest.raises(ValueError, match="parameters"):
        gold.recipe("panel", SPEC, {"members": {}}, parents, "x")
    with pytest.raises(ValueError, match="parameters"):
        gold.recipe("panel", SPEC, {**PANEL_PARAMETERS, "extra": 1}, parents, "x")
    with pytest.raises(ValueError, match="text to text"):
        gold.recipe("panel", SPEC, {**PANEL_PARAMETERS, "members": {"equity": 1}}, parents, "x")
    with pytest.raises(ValueError, match="repeat"):
        gold.recipe("panel", SPEC, PANEL_PARAMETERS, [parents[0], dict(parents[0])], "x")
    with pytest.raises(ValueError, match="code_commit"):
        gold.recipe("panel", SPEC, PANEL_PARAMETERS, parents, 5)  # type: ignore[arg-type]


def test_recipe_parent_key_refusals():
    fp = factor_parent("equity", "some.equity")
    for missing in ("role", "kind", "id", "payload_sha256", "factor_id", "spec_version"):
        bad = {k: v for k, v in fp.items() if k != missing}
        with pytest.raises(ValueError, match="parent"):
            gold.recipe("panel", SPEC, PANEL_PARAMETERS, [bad], "x")
    with pytest.raises(ValueError, match="parent"):
        gold.recipe("panel", SPEC, PANEL_PARAMETERS, [{**fp, "extra": "x"}], "x")
    with pytest.raises(ValueError, match="parent kind"):
        gold.recipe("panel", SPEC, PANEL_PARAMETERS, [{**fp, "kind": "silver"}], "x")
    with pytest.raises(ValueError, match="payload_sha256"):
        gold.recipe("panel", SPEC, PANEL_PARAMETERS, [{**fp, "payload_sha256": "short"}], "x")
    bundle = {"role": "panel", "kind": "panel", "id": sha(b"p"), "payload_sha256": sha(b"q")}
    with pytest.raises(ValueError, match="parent id"):
        gold.recipe("panel", SPEC, PANEL_PARAMETERS, [{**bundle, "id": "abcd"}], "x")
    with pytest.raises(ValueError, match="parent"):
        gold.recipe("panel", SPEC, PANEL_PARAMETERS, [{**bundle, "factor_id": "x"}], "x")
    with pytest.raises(ValueError, match="parent"):
        gold.recipe("panel", SPEC, PANEL_PARAMETERS, ["equity"], "x")  # type: ignore[list-item]


def test_manifest_is_computed_independently():
    r = panel_recipe()
    tables = panel_tables()
    m = gold.manifest(r, tables)
    entries = []
    for name in sorted(tables):
        header = HEADERS[("panel", name)]
        entries.append(
            {
                "name": name,
                "header_sha256": sha(header.encode()),
                "file_sha256": sha(tables[name]),
                "rows": 3,
            }
        )
    assert m == {
        "build_id": sha(cj(r)),
        "recipe": r,
        "tables": entries,
        "payload_sha256": sha(cj(entries)),
    }
    assert [e["name"] for e in m["tables"]] == sorted(gold.TABLES["panel"])


def test_manifest_bytes_rendering():
    m = gold.manifest(panel_recipe(), panel_tables())
    data = gold.manifest_bytes(m)
    assert data == (json.dumps(m, indent=1, sort_keys=True) + "\n").encode()
    assert data.endswith(b"}\n")
    assert data.startswith(b'{\n "build_id"')
    assert json.loads(data) == m


def test_manifest_refuses_missing_unknown_and_bad_tables():
    r = panel_recipe()
    tables = panel_tables()
    with pytest.raises(ValueError, match="missing panel tables"):
        gold.manifest(r, {k: v for k, v in tables.items() if k != "fact_panel_return"})
    with pytest.raises(ValueError, match="unknown panel tables"):
        gold.manifest(r, {**tables, "fact_target_allocation": b""})
    with pytest.raises(ValueError, match="header"):
        gold.manifest(r, {**tables, "fact_panel_return": b"a,b\n"})
    with pytest.raises(ValueError, match="bytes expected"):
        gold.manifest(r, {**tables, "fact_panel_return": "text"})  # type: ignore[dict-item]


# --------------------------------------------------------------------------------------
# write_bundle and verify_bundle
# --------------------------------------------------------------------------------------


def test_write_verify_rewrite_and_refuse_different_bytes(tmp_path):
    root = tmp_path / "gold"
    directory = write_panel(root)
    r = panel_recipe()
    bid = sha(cj(r))
    assert directory == root / "panel" / bid
    assert sorted(p.name for p in directory.iterdir()) == ["manifest.json", "tables"]
    assert sorted(p.name for p in (directory / "tables").iterdir()) == [
        "bridge_panel_member.csv",
        "fact_panel_coverage.csv",
        "fact_panel_return.csv",
    ]
    m = gold.verify_bundle(directory)
    assert m == gold.manifest(r, panel_tables())
    assert (directory / "manifest.json").read_bytes() == gold.manifest_bytes(m)
    # An identical rewrite is "already there" and changes nothing.
    before = {p: p.read_bytes() for p in directory.rglob("*") if p.is_file()}
    again, existed = gold.write_bundle(root, r, panel_tables())
    assert (again, existed) == (directory, True)
    assert {p: p.read_bytes() for p in directory.rglob("*") if p.is_file()} == before
    # Same recipe, different table bytes: refused, nothing overwritten.
    different = panel_tables()
    different["fact_panel_return"] = gold.table_bytes(
        "panel", "fact_panel_return", invented_rows("panel", "fact_panel_return", 2)
    )
    with pytest.raises(ValueError, match="already exists with different bytes"):
        gold.write_bundle(root, r, different)
    assert {p: p.read_bytes() for p in directory.rglob("*") if p.is_file()} == before
    # No temporary directory is left behind.
    assert [p.name for p in (root / "panel").iterdir()] == [bid]


def test_same_recipe_gives_same_bytes_in_two_roots(tmp_path):
    a = write_panel(tmp_path / "a")
    b = write_panel(tmp_path / "b")
    files = lambda d: {p.relative_to(d).as_posix(): p.read_bytes() for p in d.rglob("*") if p.is_file()}  # noqa: E731
    assert files(a) == files(b)


def test_write_bundle_checks_before_writing(tmp_path):
    root = tmp_path / "gold"
    tables = panel_tables()
    del tables["fact_panel_coverage"]
    with pytest.raises(ValueError, match="missing panel tables"):
        gold.write_bundle(root, panel_recipe(), tables)
    assert not root.exists()


def test_file_and_directory_modes(tmp_path):
    directory = write_panel(tmp_path / "gold")
    for path in [tmp_path / "gold", tmp_path / "gold" / "panel", directory, directory / "tables"]:
        assert stat.S_IMODE(path.stat().st_mode) == 0o700, path
    for path in directory.rglob("*.csv"):
        assert stat.S_IMODE(path.stat().st_mode) == 0o600, path
    assert stat.S_IMODE((directory / "manifest.json").stat().st_mode) == 0o600


def test_verify_refuses_tampered_table(tmp_path):
    directory = write_panel(tmp_path / "gold")
    path = directory / "tables" / "fact_panel_return.csv"
    path.write_bytes(path.read_bytes() + b"x\n")
    with pytest.raises(ValueError, match="file sha256 differs"):
        gold.verify_bundle(directory)


def test_verify_refuses_missing_table(tmp_path):
    directory = write_panel(tmp_path / "gold")
    (directory / "tables" / "fact_panel_coverage.csv").unlink()
    with pytest.raises(ValueError, match=r"missing file: tables/fact_panel_coverage.csv"):
        gold.verify_bundle(directory)


def test_verify_refuses_extra_file_directory_and_symlink(tmp_path):
    directory = write_panel(tmp_path / "gold")
    extra = directory / "tables" / "extra.csv"
    extra.write_bytes(b"x")
    with pytest.raises(ValueError, match=r"unexpected file: tables/extra.csv"):
        gold.verify_bundle(directory)
    extra.unlink()
    (directory / "notes.txt").write_bytes(b"x")
    with pytest.raises(ValueError, match=r"unexpected file: notes.txt"):
        gold.verify_bundle(directory)
    (directory / "notes.txt").unlink()
    (directory / "sub").mkdir()
    with pytest.raises(ValueError, match=r"unexpected directory: sub"):
        gold.verify_bundle(directory)
    (directory / "sub").rmdir()
    os.symlink(directory / "manifest.json", directory / "link")
    with pytest.raises(ValueError, match="symbolic link"):
        gold.verify_bundle(directory)


def test_verify_refuses_wrong_directory_name(tmp_path):
    directory = write_panel(tmp_path / "gold")
    moved = directory.with_name("0" * 64)
    directory.rename(moved)
    with pytest.raises(ValueError, match="directory name"):
        gold.verify_bundle(moved)


def test_verify_refuses_wrong_kind_directory(tmp_path):
    root = tmp_path / "gold"
    directory = write_panel(root)
    (root / "portfolio_path").mkdir()
    moved = root / "portfolio_path" / directory.name
    directory.rename(moved)
    with pytest.raises(ValueError, match="directory kind"):
        gold.verify_bundle(moved)


def test_verify_refuses_wrong_row_count(tmp_path):
    directory = write_panel(tmp_path / "gold")
    rewrite_manifest(directory, lambda m: m["tables"][0].update(rows=m["tables"][0]["rows"] + 1))
    with pytest.raises(ValueError, match="rows, the manifest says"):
        gold.verify_bundle(directory)


def test_verify_refuses_wrong_header(tmp_path):
    directory = write_panel(tmp_path / "gold")
    path = directory / "tables" / "fact_panel_return.csv"
    path.write_bytes(b"a,b\n")

    def mutate(m):
        entry = next(e for e in m["tables"] if e["name"] == "fact_panel_return")
        entry.update(file_sha256=sha(b"a,b\n"), rows=0)
        m["payload_sha256"] = sha(cj(m["tables"]))

    rewrite_manifest(directory, mutate)
    with pytest.raises(ValueError, match="header is not panel_build_id"):
        gold.verify_bundle(directory)


def test_verify_refuses_wrong_header_sha_in_manifest(tmp_path):
    directory = write_panel(tmp_path / "gold")
    rewrite_manifest(directory, lambda m: m["tables"][0].update(header_sha256=sha(b"other")))
    with pytest.raises(ValueError, match="header sha256"):
        gold.verify_bundle(directory)


def test_verify_refuses_wrong_payload_sha256(tmp_path):
    directory = write_panel(tmp_path / "gold")
    rewrite_manifest(directory, lambda m: m.update(payload_sha256=sha(b"other")))
    with pytest.raises(ValueError, match="payload_sha256"):
        gold.verify_bundle(directory)


def test_verify_refuses_edited_recipe(tmp_path):
    directory = write_panel(tmp_path / "gold")
    rewrite_manifest(directory, lambda m: m["recipe"].update(code_commit="edited"))
    with pytest.raises(ValueError, match="does not match the recipe"):
        gold.verify_bundle(directory)


def test_verify_refuses_malformed_manifest_and_recipe(tmp_path):
    directory = write_panel(tmp_path / "gold")
    original = (directory / "manifest.json").read_bytes()
    (directory / "manifest.json").write_bytes(b"not json")
    with pytest.raises(ValueError, match="not JSON"):
        gold.verify_bundle(directory)
    rewrite_manifest_from = lambda mutate: (  # noqa: E731
        (directory / "manifest.json").write_bytes(original),
        rewrite_manifest(directory, mutate),
    )
    rewrite_manifest_from(lambda m: m.update(extra=1))
    with pytest.raises(ValueError, match="manifest must have exactly"):
        gold.verify_bundle(directory)
    rewrite_manifest_from(lambda m: m["recipe"].update(schema="hio.gold/2"))
    with pytest.raises(ValueError, match="schema"):
        gold.verify_bundle(directory)
    rewrite_manifest_from(lambda m: m["recipe"].update(numeric_policy="float"))
    with pytest.raises(ValueError, match="numeric_policy"):
        gold.verify_bundle(directory)
    rewrite_manifest_from(lambda m: m["recipe"]["parents"].reverse())
    with pytest.raises(ValueError, match="not sorted by role"):
        gold.verify_bundle(directory)
    rewrite_manifest_from(lambda m: m["tables"].reverse())
    with pytest.raises(ValueError, match="sorted by name"):
        gold.verify_bundle(directory)
    (directory / "manifest.json").write_bytes(original)
    (directory / "manifest.json").write_bytes(original.replace(b"\n", b"\r\n"))
    with pytest.raises(ValueError, match="canonical rendering"):
        gold.verify_bundle(directory)


def test_verify_refuses_missing_manifest_and_non_directory(tmp_path):
    directory = write_panel(tmp_path / "gold")
    (directory / "manifest.json").unlink()
    with pytest.raises(ValueError, match=r"missing file: manifest\.json"):
        gold.verify_bundle(directory)
    with pytest.raises(ValueError, match="not a bundle directory"):
        gold.verify_bundle(tmp_path / "absent")


# --------------------------------------------------------------------------------------
# Bundle
# --------------------------------------------------------------------------------------


def numeric_bundle(root: Path) -> gold.Bundle:
    r = gold.recipe(
        "portfolio_path",
        SPEC,
        {"panel": "example", "rebalance": "month_end", "weights": {"a": "0.60", "b": "0.40"}},
        [{"role": "panel", "kind": "panel", "id": sha(b"p"), "payload_sha256": sha(b"q")}],
        "c0ffee",
    )
    bid = gold.build_id(r)
    rows = [
        row(
            "portfolio_path",
            "fact_target_allocation",
            portfolio_build_id=bid,
            member_code="b",
            target_weight="0.40",
        ),
        row(
            "portfolio_path",
            "fact_target_allocation",
            portfolio_build_id=bid,
            member_code="a",
            target_weight="0.60",
        ),
    ]
    tables = {
        "fact_target_allocation": gold.table_bytes("portfolio_path", "fact_target_allocation", rows),
        "fact_portfolio_return": gold.table_bytes(
            "portfolio_path",
            "fact_portfolio_return",
            [
                row(
                    "portfolio_path",
                    "fact_portfolio_return",
                    period_end="2024-02-29",
                    portfolio_return="0.0100",
                ),
                row("portfolio_path", "fact_portfolio_return", period_end="2024-01-31", portfolio_return=""),
            ],
        ),
        "fact_return_contribution": gold.table_bytes("portfolio_path", "fact_return_contribution", []),
    }
    gold.write_bundle(root, r, tables)
    return gold.open_bundle(root, "portfolio_path", bid)


def test_open_bundle_properties_table_and_decimals(tmp_path):
    root = tmp_path / "gold"
    bundle = numeric_bundle(root)
    assert isinstance(bundle, gold.Bundle)
    assert bundle.kind == "portfolio_path"
    assert bundle.build_id == gold.build_id(bundle.recipe)
    assert bundle.payload_sha256 == bundle.manifest["payload_sha256"]
    assert bundle.recipe["kind"] == "portfolio_path"
    assert bundle.directory == root / "portfolio_path" / bundle.build_id
    rows = bundle.table("fact_target_allocation")
    assert [(r["member_code"], r["target_weight"]) for r in rows] == [("a", "0.60"), ("b", "0.40")]
    assert all(isinstance(v, str) for r in rows for v in r.values())
    weights = bundle.decimals("fact_target_allocation", "target_weight")
    assert weights == [Decimal("0.60"), Decimal("0.40")]
    assert all(isinstance(w, Decimal) for w in weights)
    assert str(weights[0]) == "0.60"  # trailing zeros kept
    assert bundle.table("fact_return_contribution") == []
    assert bundle.decimals("fact_return_contribution", "contribution") == []


def test_bundle_is_frozen():
    import dataclasses

    assert dataclasses.is_dataclass(gold.Bundle)
    assert gold.Bundle.__dataclass_params__.frozen  # type: ignore[attr-defined]
    assert gold.FactorSeries.__dataclass_params__.frozen  # type: ignore[attr-defined]


def test_decimals_refuses_empty_non_decimal_and_unknown_column(tmp_path):
    bundle = numeric_bundle(tmp_path / "gold")
    with pytest.raises(ValueError, match="is empty"):
        bundle.decimals("fact_portfolio_return", "portfolio_return")
    with pytest.raises(ValueError, match="no column"):
        bundle.decimals("fact_portfolio_return", "nope")
    with pytest.raises(ValueError, match="unknown portfolio_path table"):
        bundle.table("bridge_panel_member")
    with pytest.raises(ValueError, match="not a decimal"):
        bundle.decimals("fact_target_allocation", "member_code")


def test_decimals_refuses_non_finite(tmp_path):
    root = tmp_path / "gold"
    r = gold.recipe(
        "portfolio_path",
        SPEC,
        {"panel": "example", "rebalance": "month_end", "weights": {"a": "1"}},
        [{"role": "panel", "kind": "panel", "id": sha(b"p"), "payload_sha256": sha(b"q")}],
        "c0ffee",
    )
    tables = {
        "fact_target_allocation": gold.table_bytes(
            "portfolio_path",
            "fact_target_allocation",
            [row("portfolio_path", "fact_target_allocation", target_weight="NaN")],
        ),
        "fact_portfolio_return": gold.table_bytes("portfolio_path", "fact_portfolio_return", []),
        "fact_return_contribution": gold.table_bytes("portfolio_path", "fact_return_contribution", []),
    }
    gold.write_bundle(root, r, tables)
    bundle = gold.open_bundle(root, "portfolio_path", gold.build_id(r))
    with pytest.raises(ValueError, match="not finite"):
        bundle.decimals("fact_target_allocation", "target_weight")


def test_table_read_detects_change_after_open(tmp_path):
    bundle = numeric_bundle(tmp_path / "gold")
    path = bundle.directory / "tables" / "fact_target_allocation.csv"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="file sha256 differs"):
        bundle.table("fact_target_allocation")


def test_open_bundle_verifies_and_needs_an_exact_identity(tmp_path):
    root = tmp_path / "gold"
    directory = write_panel(root)
    assert gold.open_bundle(root, "panel", directory.name).build_id == directory.name
    with pytest.raises(ValueError, match="build_id"):
        gold.open_bundle(root, "panel", directory.name[:16])
    with pytest.raises(ValueError, match="build_id"):
        gold.open_bundle(root, "panel", "../" + directory.name)
    with pytest.raises(ValueError, match="unknown gold kind"):
        gold.open_bundle(root, "silver", directory.name)
    with pytest.raises(ValueError, match="not a bundle directory"):
        gold.open_bundle(root, "portfolio_path", directory.name)
    path = directory / "tables" / "fact_panel_return.csv"
    path.write_bytes(path.read_bytes() + b"x\n")
    with pytest.raises(ValueError, match="file sha256 differs"):
        gold.open_bundle(root, "panel", directory.name)


# --------------------------------------------------------------------------------------
# Factor series
# --------------------------------------------------------------------------------------

TOTAL_HEADER = "period_start,period_end,price_return,income_return,total_return,index"
TOTAL_ROWS = ["2024-01-01,2024-01-02,0.01,0,0.01,1.01", "2024-01-02,2024-01-03,-0.005,0,-0.005,1.00495"]
EXCESS_HEADER = "period_start,period_end,asset_return,cash_return,excess_return"
EXCESS_ROWS = ["2024-01-01,2024-01-02,0.01,0.0001,0.0099"]


def write_series(
    store: Path,
    factor_id: str = "some.factor",
    spec_version: str = "0.1.0",
    build_id: str = "0123456789abcdef",
    *,
    header: str = TOTAL_HEADER,
    rows: list[str] = TOTAL_ROWS,
    series_class: Any = "total_return",
    numeraire: Any = "AUD",
    **record_overrides: Any,
) -> Path:
    directory = store / factor_id / spec_version / build_id
    directory.mkdir(parents=True)
    data = ("\n".join([header, *rows]) + "\n").encode()
    (directory / "series.csv").write_bytes(data)
    record = {
        "factor_id": factor_id,
        "spec_version": spec_version,
        "build_id": build_id,
        "series_class": series_class,
        "numeraire": numeraire,
        "series_sha256": sha(data),
        "invariants": {"RA-INV-001": {"checked": len(rows), "passed": True}},
        **record_overrides,
    }
    (directory / "build.json").write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    return directory


def test_read_factor_series_total_return(tmp_path):
    directory = write_series(tmp_path)
    series = gold.read_factor_series(tmp_path, "some.factor", "0.1.0", "0123456789abcdef")
    assert series.factor_id == "some.factor"
    assert series.spec_version == "0.1.0"
    assert series.build_id == "0123456789abcdef"
    assert series.series_sha256 == sha((directory / "series.csv").read_bytes())
    assert series.series_class == "total_return"
    assert series.numeraire == "AUD"
    assert series.columns == tuple(TOTAL_HEADER.split(","))
    assert series.rows == [
        {"period_start": "2024-01-01", "period_end": "2024-01-02", "price_return": "0.01",
         "income_return": "0", "total_return": "0.01", "index": "1.01"},
        {"period_start": "2024-01-02", "period_end": "2024-01-03", "price_return": "-0.005",
         "income_return": "0", "total_return": "-0.005", "index": "1.00495"},
    ]  # fmt: skip
    assert series.record["invariants"] == {"RA-INV-001": {"checked": 2, "passed": True}}
    assert series.parent("equity") == {
        "role": "equity",
        "kind": "factor_series",
        "id": "0123456789abcdef",
        "payload_sha256": series.series_sha256,
        "factor_id": "some.factor",
        "spec_version": "0.1.0",
    }


def test_read_factor_series_excess_and_pin_argument(tmp_path):
    directory = write_series(tmp_path, header=EXCESS_HEADER, rows=EXCESS_ROWS, series_class="excess")
    digest = sha((directory / "series.csv").read_bytes())
    series = gold.read_factor_series(
        tmp_path, "some.factor", "0.1.0", "0123456789abcdef", series_sha256=digest
    )
    assert series.series_class == "excess"
    assert series.rows[0]["excess_return"] == "0.0099"
    # The pin is accepted as a parent of a recipe.
    gold.recipe("panel", SPEC, PANEL_PARAMETERS, [series.parent("equity")], "x")


def test_read_factor_series_refuses_tampered_series(tmp_path):
    directory = write_series(tmp_path)
    (directory / "series.csv").write_bytes((directory / "series.csv").read_bytes() + b"x\n")
    with pytest.raises(ValueError, match=r"series\.csv sha256 differs"):
        gold.read_factor_series(tmp_path, "some.factor", "0.1.0", "0123456789abcdef")


def test_read_factor_series_refuses_wrong_directory_names(tmp_path):
    write_series(tmp_path)
    store = tmp_path
    # A build copied under another name no longer matches its record.
    for wrong in (
        ("some.factor", "0.1.0", "fedcba9876543210"),
        ("some.factor", "0.2.0", "0123456789abcdef"),
        ("other.factor", "0.1.0", "0123456789abcdef"),
    ):
        target = store.joinpath(*wrong)
        target.parent.mkdir(parents=True, exist_ok=True)
        os.makedirs(target)
        for name in ("build.json", "series.csv"):
            (target / name).write_bytes(
                (store / "some.factor" / "0.1.0" / "0123456789abcdef" / name).read_bytes()
            )
        with pytest.raises(ValueError, match="differs from the directory"):
            gold.read_factor_series(store, *wrong)
    with pytest.raises(ValueError, match="not a factor build directory"):
        gold.read_factor_series(store, "some.factor", "0.1.0", "ffffffffffffffff")
    for bad in ("..", "a/b", ""):
        with pytest.raises(ValueError, match="path component"):
            gold.read_factor_series(store, "some.factor", "0.1.0", bad)


def test_read_factor_series_refuses_wrong_pin(tmp_path):
    write_series(tmp_path)
    with pytest.raises(ValueError, match="series_sha256"):
        gold.read_factor_series(tmp_path, "some.factor", "0.1.0", "0123456789abcdef", series_sha256=sha(b"x"))


def test_read_factor_series_refuses_missing_columns_and_bad_header(tmp_path):
    write_series(tmp_path, "a", header="period_start,period_end,price_return", rows=["x,y,1"])
    with pytest.raises(ValueError, match="no total_return column"):
        gold.read_factor_series(tmp_path, "a", "0.1.0", "0123456789abcdef")
    write_series(tmp_path, "b", header="period_start,period_end,asset_return,cash_return", rows=["x,y,1,2"],
                 series_class="excess")  # fmt: skip
    with pytest.raises(ValueError, match="no excess_return column"):
        gold.read_factor_series(tmp_path, "b", "0.1.0", "0123456789abcdef")
    write_series(tmp_path, "c", header="period_end,period_start,total_return", rows=["x,y,1"])
    with pytest.raises(ValueError, match="must start period_start,period_end"):
        gold.read_factor_series(tmp_path, "c", "0.1.0", "0123456789abcdef")
    write_series(tmp_path, "d", header="period_start,period_end,total_return,total_return", rows=["x,y,1,2"])
    with pytest.raises(ValueError, match="repeats a column"):
        gold.read_factor_series(tmp_path, "d", "0.1.0", "0123456789abcdef")
    write_series(tmp_path, "e", header="period_start,period_end,total_return", rows=["x,y"])
    with pytest.raises(ValueError, match="cells"):
        gold.read_factor_series(tmp_path, "e", "0.1.0", "0123456789abcdef")


def test_read_factor_series_refuses_unknown_class_and_bad_record(tmp_path):
    write_series(tmp_path, "a", series_class="price")
    with pytest.raises(ValueError, match="series_class"):
        gold.read_factor_series(tmp_path, "a", "0.1.0", "0123456789abcdef")
    write_series(tmp_path, "b", series_class=None)
    with pytest.raises(ValueError, match="series_class"):
        gold.read_factor_series(tmp_path, "b", "0.1.0", "0123456789abcdef")
    write_series(tmp_path, "c", numeraire="")
    with pytest.raises(ValueError, match="numeraire"):
        gold.read_factor_series(tmp_path, "c", "0.1.0", "0123456789abcdef")
    directory = write_series(tmp_path, "d")
    (directory / "build.json").write_text("[]")
    with pytest.raises(ValueError, match="not an object"):
        gold.read_factor_series(tmp_path, "d", "0.1.0", "0123456789abcdef")
    (directory / "build.json").write_text("{")
    with pytest.raises(ValueError, match="not JSON"):
        gold.read_factor_series(tmp_path, "d", "0.1.0", "0123456789abcdef")
    (directory / "build.json").unlink()
    with pytest.raises(ValueError, match=r"missing file: build\.json"):
        gold.read_factor_series(tmp_path, "d", "0.1.0", "0123456789abcdef")


# --------------------------------------------------------------------------------------
# Spec readers
# --------------------------------------------------------------------------------------

LOCK_TEXT = f"""\
identity: {{name: example, version: 0.1.0, status: proposed}}
factor_series:
  some.equity: {{spec_version: 0.1.0, build_id: "0123456789abcdef", series_sha256: "{"a" * 64}"}}
  some.bonds: {{spec_version: 0.2.0, build_id: "fedcba9876543210", series_sha256: "{"b" * 64}"}}
"""

PANEL_TEXT = """\
identity: {name: example, version: 0.1.0, status: proposed}
kind: panel
frequency: monthly
alignment: common_boundaries
incomplete_periods: exclude
members: {equity: some.equity, bonds: some.bonds}
"""

PORTFOLIO_TEXT = """\
identity: {name: mix, version: 0.1.0, status: proposed}
kind: portfolio_path
panel: example
rebalance: month_end
weights: {equity: "0.60", bonds: "0.40"}
"""


def write(tmp_path: Path, text: str, name: str = "spec.yaml") -> Path:
    path = tmp_path / name
    path.write_text(text)
    return path


def test_read_lock_valid_and_pin(tmp_path):
    path = write(tmp_path, LOCK_TEXT)
    lock = gold.read_lock(path)
    assert lock == {
        "name": "example",
        "version": "0.1.0",
        "status": "proposed",
        "factor_series": {
            "some.equity": {
                "spec_version": "0.1.0",
                "build_id": "0123456789abcdef",
                "series_sha256": "a" * 64,
            },
            "some.bonds": {
                "spec_version": "0.2.0",
                "build_id": "fedcba9876543210",
                "series_sha256": "b" * 64,
            },
        },
        "sha256": sha(LOCK_TEXT.encode()),
    }
    assert gold.lock_pin(lock, "some.bonds") == {
        "spec_version": "0.2.0",
        "build_id": "fedcba9876543210",
        "series_sha256": "b" * 64,
    }
    with pytest.raises(ValueError, match=r"no entry for factor 'some\.other'"):
        gold.lock_pin(lock, "some.other")


@pytest.mark.parametrize(
    ("old", "new", "match"),
    [
        ('build_id: "0123456789abcdef"', 'build_id: "0123"', "build_id"),
        ('build_id: "0123456789abcdef"', 'build_id: "0123456789ABCDEF"', "build_id"),
        ('build_id: "0123456789abcdef"', "build_id: 1234567890123456", "build_id"),
        ("a" * 64, "a" * 63, "series_sha256"),
        ("spec_version: 0.1.0", "spec_version: 0.1", "spec_version"),
        ("spec_version: 0.1.0,", "extra: 1, spec_version: 0.1.0,", "exactly the keys"),
        ("{name: example, version: 0.1.0, status: proposed}", "{name: example, version: 0.1.0}", "identity"),
        (
            "{name: example, version: 0.1.0, status: proposed}",
            "{name: example, version: 1.0, status: x}",
            "version",
        ),
        ("factor_series:", "factor_series: []\nignored:", "exactly the keys"),
    ],
)
def test_read_lock_refusals(tmp_path, old, new, match):
    assert old in LOCK_TEXT
    with pytest.raises(ValueError, match=match):
        gold.read_lock(write(tmp_path, LOCK_TEXT.replace(old, new, 1)))


def test_read_lock_refuses_non_mapping_and_bad_yaml(tmp_path):
    with pytest.raises(ValueError, match="must be a mapping"):
        gold.read_lock(write(tmp_path, "- a\n"))
    with pytest.raises(ValueError, match="not YAML"):
        gold.read_lock(write(tmp_path, "a: [\n"))
    with pytest.raises(ValueError, match="factor_series must be a mapping"):
        gold.read_lock(write(tmp_path, "identity: {name: a, version: b, status: c}\nfactor_series: [x]\n"))


def test_read_panel_spec_valid(tmp_path):
    spec = gold.read_panel_spec(write(tmp_path, PANEL_TEXT))
    assert spec == {
        "name": "example",
        "version": "0.1.0",
        "status": "proposed",
        "kind": "panel",
        "frequency": "monthly",
        "alignment": "common_boundaries",
        "incomplete_periods": "exclude",
        "members": {"equity": "some.equity", "bonds": "some.bonds"},
        "sha256": sha(PANEL_TEXT.encode()),
    }
    # The fields feed a recipe directly.
    params = {k: spec[k] for k in ("frequency", "alignment", "incomplete_periods", "members")}
    gold.recipe(
        "panel",
        {k: spec[k] for k in ("name", "version", "sha256")},
        params,
        [factor_parent("equity", "some.equity"), factor_parent("bonds", "some.bonds")],
        "c0ffee",
    )


@pytest.mark.parametrize(
    ("old", "new", "match"),
    [
        ("kind: panel", "kind: portfolio_path", "kind"),
        ("frequency: monthly", "frequency: daily", "frequency"),
        ("alignment: common_boundaries", "alignment: union", "alignment"),
        ("incomplete_periods: exclude", "incomplete_periods: include", "incomplete_periods"),
        ("kind: panel\n", "", "exactly the keys"),
        ("kind: panel\n", "kind: panel\nextra: 1\n", "exactly the keys"),
        ("members: {equity: some.equity, bonds: some.bonds}", "members: {}", "non-empty mapping"),
        ("members: {equity: some.equity, bonds: some.bonds}", "members: [equity]", "non-empty mapping"),
        ("equity: some.equity", "Equity: some.equity", "member code"),
        ("equity: some.equity", "1equity: some.equity", "member code"),
        ("equity: some.equity", "eq-uity: some.equity", "member code"),
        ("equity: some.equity", "equity: 5", "factor id"),
        ("equity: some.equity", "equity: ''", "factor id"),
        ("status: proposed", "status: ''", "status"),
    ],
)
def test_read_panel_spec_refusals(tmp_path, old, new, match):
    assert old in PANEL_TEXT
    with pytest.raises(ValueError, match=match):
        gold.read_panel_spec(write(tmp_path, PANEL_TEXT.replace(old, new, 1)))


def test_read_portfolio_spec_valid(tmp_path):
    spec = gold.read_portfolio_spec(write(tmp_path, PORTFOLIO_TEXT))
    assert spec == {
        "name": "mix",
        "version": "0.1.0",
        "status": "proposed",
        "kind": "portfolio_path",
        "panel": "example",
        "rebalance": "month_end",
        "weights": {"equity": "0.60", "bonds": "0.40"},
        "sha256": sha(PORTFOLIO_TEXT.encode()),
    }
    # Weights stay the strings as written; trailing zeros survive into the recipe.
    assert list(spec["weights"].values()) == ["0.60", "0.40"]


def test_read_portfolio_spec_sums_exactly_with_many_digits(tmp_path):
    text = PORTFOLIO_TEXT.replace(
        '{equity: "0.60", bonds: "0.40"}',
        '{equity: "0.3333333333333333333333333333333333333333333333333333333", '
        'bonds: "0.6666666666666666666666666666666666666666666666666666667"}',
    )
    assert gold.read_portfolio_spec(write(tmp_path, text))["weights"]["equity"].startswith("0.3333")
    off = text.replace("6667", "6666")
    with pytest.raises(ValueError, match="sum to exactly 1"):
        gold.read_portfolio_spec(write(tmp_path, off))
    assert gold.read_portfolio_spec(write(tmp_path, PORTFOLIO_TEXT.replace('"0.60"', '"6E-1"'), "b.yaml"))
    assert gold.read_portfolio_spec(write(tmp_path, PORTFOLIO_TEXT.replace('"0.60"', '"0.6000"'), "c.yaml"))


@pytest.mark.parametrize(
    ("old", "new", "match"),
    [
        ("kind: portfolio_path", "kind: panel", "kind"),
        ("rebalance: month_end", "rebalance: quarterly", "rebalance"),
        ("panel: example", "panel: ''", "panel"),
        ("panel: example\n", "", "exactly the keys"),
        ("rebalance: month_end\n", "rebalance: month_end\nextra: 1\n", "exactly the keys"),
        ('"0.60"', "0.60", "decimal string"),  # a YAML number is not a string
        ('"0.60"', '"abc"', "not a decimal string"),
        ('"0.60"', '"NaN"', "not finite"),
        ('"0.60"', '"Infinity"', "not finite"),
        ('"0.60"', '" 0.60"', "not a decimal string"),
        ('"0.60"', '"0_6"', "not a decimal string"),
        ('"0.60"', '""', "not a decimal string"),
        ('"0.60"', '"-0.20"', "negative"),
        ('"0.40"', '"1.40"', "sum to exactly 1"),
        ('"0.40"', '"0.39"', "sum to exactly 1"),
        ('"0.60"', '"0.6000000000000000000000000000000000000000000000000000001"', "sum to exactly 1"),
        ("weights: {equity", "weights: {Equity", "member code"),
        ("weights: {equity", "weights: {9equity", "member code"),
        ('weights: {equity: "0.60", bonds: "0.40"}', "weights: {}", "non-empty mapping"),
    ],
)
def test_read_portfolio_spec_refusals(tmp_path, old, new, match):
    assert old in PORTFOLIO_TEXT
    with pytest.raises(ValueError, match=match):
        gold.read_portfolio_spec(write(tmp_path, PORTFOLIO_TEXT.replace(old, new, 1)))


def test_read_portfolio_spec_refuses_negative_zero(tmp_path):
    text = PORTFOLIO_TEXT.replace('"0.40"', '"-0"').replace('"0.60"', '"1"')
    with pytest.raises(ValueError, match="negative"):
        gold.read_portfolio_spec(write(tmp_path, text))


# --------------------------------------------------------------------------------------
# The real specs
# --------------------------------------------------------------------------------------


def test_real_lock_loads():
    lock = gold.read_lock(SPECS / "locks" / "first.yaml")
    assert (lock["name"], lock["version"], lock["status"]) == ("first", "0.1.0", "proposed")
    assert sorted(lock["factor_series"]) == [
        "equity.au.vas.market_total_return",
        "equity.us.spy.aud_unhedged.total_return",
        "rates.au.vgb.market_total_return",
        "rates.us.ief.aud_unhedged.total_return",
    ]
    assert lock["sha256"] == sha((SPECS / "locks" / "first.yaml").read_bytes())
    assert gold.lock_pin(lock, "rates.au.vgb.market_total_return")["build_id"] == "e3e895a2ce53e464"


def test_real_panel_spec_loads_and_its_members_are_in_the_lock():
    lock = gold.read_lock(SPECS / "locks" / "first.yaml")
    panel = gold.read_panel_spec(SPECS / "panels" / "aud-four-sleeve.yaml")
    assert panel["name"] == "aud-four-sleeve"
    assert sorted(panel["members"]) == ["au_bonds", "au_equity", "us_bonds_unhedged", "us_equity_unhedged"]
    for factor_id in panel["members"].values():
        assert gold.lock_pin(lock, factor_id)["spec_version"] == "0.1.0"


def test_real_portfolio_spec_loads_and_names_the_panel_members():
    panel = gold.read_panel_spec(SPECS / "panels" / "aud-four-sleeve.yaml")
    portfolio = gold.read_portfolio_spec(SPECS / "portfolios" / "aud-eq60-dur40.yaml")
    assert portfolio["name"] == "aud-eq60-dur40"
    assert portfolio["panel"] == panel["name"]
    assert portfolio["weights"] == {
        "au_equity": "0.30",
        "us_equity_unhedged": "0.30",
        "au_bonds": "0.20",
        "us_bonds_unhedged": "0.20",
    }
    assert set(portfolio["weights"]) == set(panel["members"])


# --------------------------------------------------------------------------------------
# The float kinds (§6a, OD-0234)
# --------------------------------------------------------------------------------------

ENV = {"numpy": "2.1.0", "python": "3.13"}
COV_PARAMETERS = {
    "panel": "example",
    "estimator": "sample",
    "ddof": 1,
    "annualisation": 12,
    "trailing_months": 36,
}
RISK_PARAMETERS = {"portfolio": "mix", "covariance": "cov"}
PANEL_PARENT = {"role": "panel", "kind": "panel", "id": sha(b"panel"), "payload_sha256": sha(b"panel!")}
COV_PARENT = {
    "role": "covariance",
    "kind": "covariance",
    "id": sha(b"cov"),
    "payload_sha256": sha(b"cov!"),
}
PORTFOLIO_PARENT = {
    "role": "portfolio",
    "kind": "portfolio_path",
    "id": sha(b"pf"),
    "payload_sha256": sha(b"pf!"),
}


def cov_recipe(**over: Any) -> dict[str, Any]:
    args: dict[str, Any] = {
        "kind": "covariance",
        "spec": SPEC,
        "parameters": COV_PARAMETERS,
        "parents": [PANEL_PARENT],
        "code_commit": "c0ffee",
        "environment": ENV,
    }
    args.update(over)
    return gold.recipe(
        args["kind"],
        args["spec"],
        args["parameters"],
        args["parents"],
        args["code_commit"],
        environment=args["environment"],
    )


def risk_recipe(**over: Any) -> dict[str, Any]:
    args: dict[str, Any] = {
        "kind": "risk_contribution",
        "spec": SPEC,
        "parameters": RISK_PARAMETERS,
        "parents": [PORTFOLIO_PARENT, COV_PARENT],
        "code_commit": "c0ffee",
        "environment": ENV,
    }
    args.update(over)
    return cov_recipe(**args)


def test_new_tables_are_the_contract_tables_in_order():
    assert list(gold.TABLES["covariance"]) == ["dim_window", "fact_covariance", "fact_volatility"]
    assert list(gold.TABLES["risk_contribution"]) == ["fact_portfolio_risk", "fact_risk_contribution"]


def test_dim_window_sorts_by_window_kind_then_last_period_end_as_text():
    rows = [
        row("covariance", "dim_window", window_id="trailing:2024-03-31", window_kind="trailing",
            last_period_end="2024-03-31"),
        row("covariance", "dim_window", window_id="trailing:2024-02-29", window_kind="trailing",
            last_period_end="2024-02-29"),
        row("covariance", "dim_window", window_id="full", window_kind="full", last_period_end="2024-12-31"),
    ]  # fmt: skip
    out = gold.parse_table("covariance", "dim_window", gold.table_bytes("covariance", "dim_window", rows))
    assert [(r["window_kind"], r["last_period_end"]) for r in out] == [
        ("full", "2024-12-31"),
        ("trailing", "2024-02-29"),
        ("trailing", "2024-03-31"),
    ]


def test_fact_covariance_sorts_every_ordered_pair_by_window_then_members():
    cells = [("w2", "b", "a"), ("w1", "b", "b"), ("w1", "a", "b"), ("w1", "b", "a"), ("w1", "a", "a")]
    rows = [row("covariance", "fact_covariance", window_id=w, member_i=i, member_j=j) for w, i, j in cells]
    out = gold.parse_table(
        "covariance", "fact_covariance", gold.table_bytes("covariance", "fact_covariance", rows)
    )
    assert [(r["window_id"], r["member_i"], r["member_j"]) for r in out] == sorted(cells)


def test_risk_tables_sort_by_window_then_member():
    rows = [
        row("risk_contribution", "fact_risk_contribution", window_id=w, member_code=m)
        for w, m in [("w2", "a"), ("w1", "b"), ("w1", "a")]
    ]
    out = gold.parse_table(
        "risk_contribution",
        "fact_risk_contribution",
        gold.table_bytes("risk_contribution", "fact_risk_contribution", rows),
    )
    assert [(r["window_id"], r["member_code"]) for r in out] == [("w1", "a"), ("w1", "b"), ("w2", "a")]
    risk_rows = [row("risk_contribution", "fact_portfolio_risk", window_id=w) for w in ("w2", "w10", "w1")]
    out = gold.parse_table(
        "risk_contribution",
        "fact_portfolio_risk",
        gold.table_bytes("risk_contribution", "fact_portfolio_risk", risk_rows),
    )
    assert [r["window_id"] for r in out] == ["w1", "w10", "w2"]  # text order


def test_contracts_gold_does_not_import_numpy():
    tree = ast.parse((ROOT / "src" / "hio" / "contracts" / "gold.py").read_text())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert "numpy" not in imported
    assert imported - {"hio"} <= {
        "__future__", "csv", "io", "json", "math", "os", "re", "shutil", "tempfile",
        "collections", "dataclasses", "decimal", "fractions", "pathlib", "typing", "yaml",
    }  # fmt: skip


# float_text ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        0.1, 1e-17, 1 / 3, 2 / 3, 1e300, 5e-324, 1.7976931348623157e308,
        -0.0, 0.0, 1.0, -2.5, 123456789.123456789, 0.30000000000000004,
    ],
)  # fmt: skip
def test_float_text_round_trips_exactly(value):
    text = gold.float_text(value)
    assert text == repr(value)
    back = float(text)
    assert back == value
    assert math.copysign(1.0, back) == math.copysign(1.0, value)


def test_float_text_exact_texts():
    assert gold.float_text(0.1) == "0.1"
    assert gold.float_text(1e-17) == "1e-17"
    assert gold.float_text(1.0) == "1.0"
    assert gold.float_text(0.1 + 0.2) == "0.30000000000000004"


def test_float_text_writes_a_numpy_float_as_a_plain_float():
    import numpy as np

    assert gold.float_text(np.float64(0.1)) == "0.1"
    assert gold.float_text(float(np.float64(1) / np.float64(3))) == repr(1 / 3)


def test_float_text_refuses_non_finite_and_non_float():
    for bad in (math.nan, math.inf, -math.inf):
        with pytest.raises(ValueError, match="non-finite"):
            gold.float_text(bad)
    for wrong in (1, True, "0.1", Decimal("0.1"), None, [0.1]):
        with pytest.raises(TypeError, match="not a float"):
            gold.float_text(wrong)  # type: ignore[arg-type]


# recipe: environment, policy, parameters, parents -------------------------------------------


def test_float_recipes_have_environment_and_float_policy():
    r = cov_recipe()
    assert r == {
        "schema": "hio.gold/1",
        "kind": "covariance",
        "spec": SPEC,
        "parameters": COV_PARAMETERS,
        "parents": [PANEL_PARENT],
        "numeric_policy": "float64/1",
        "code_commit": "c0ffee",
        "environment": ENV,
    }
    assert gold.build_id(r) == sha(cj(r))
    k = risk_recipe()
    assert k["kind"] == "risk_contribution"
    assert k["numeric_policy"] == "float64/1"
    assert k["environment"] == ENV
    assert k["parents"] == [COV_PARENT, PORTFOLIO_PARENT]  # sorted by role
    assert k["parameters"] == RISK_PARAMETERS


def test_a_different_environment_is_a_different_build():
    base = gold.build_id(cov_recipe())
    assert gold.build_id(cov_recipe(environment={**ENV, "numpy": "2.2.0"})) != base
    assert gold.build_id(cov_recipe(environment={**ENV, "python": "3.12"})) != base
    assert gold.build_id(cov_recipe(environment=dict(ENV))) == base


def test_recipe_does_not_alias_its_environment():
    env = dict(ENV)
    r = cov_recipe(environment=env)
    env["numpy"] = "changed"
    assert r["environment"] == ENV


def test_environment_is_required_for_a_float_kind():
    with pytest.raises(ValueError, match="requires an environment"):
        cov_recipe(environment=None)
    with pytest.raises(ValueError, match="requires an environment"):
        risk_recipe(environment=None)


@pytest.mark.parametrize("kind", ["panel", "portfolio_path"])
def test_environment_is_refused_for_a_decimal_kind(kind):
    if kind == "panel":
        args = (SPEC, PANEL_PARAMETERS, [factor_parent("equity", "some.equity")])
    else:
        args = (SPEC, json.loads(json.dumps(portfolio_recipe()["parameters"])), [PANEL_PARENT])
    with pytest.raises(ValueError, match="takes no environment"):
        gold.recipe(kind, *args, "x", environment=ENV)
    with pytest.raises(ValueError, match="takes no environment"):
        gold.recipe(kind, *args, "x", environment={})
    assert "environment" not in gold.recipe(kind, *args, "x")
    assert "environment" not in gold.recipe(kind, *args, "x", environment=None)


@pytest.mark.parametrize(
    "environment",
    [
        {},
        {"numpy": "2.1.0"},
        {"python": "3.13"},
        {**ENV, "extra": "x"},
        {"numpy": "2.1.0", "Python": "3.13"},
        {"numpy": "", "python": "3.13"},
        {"numpy": "2.1.0", "python": ""},
        {"numpy": 2, "python": "3.13"},
        {"numpy": "2.1.0", "python": 3.13},
        {"numpy": None, "python": "3.13"},
        ["numpy", "python"],
        "numpy",
    ],
)
def test_environment_must_be_exactly_numpy_and_python_text(environment):
    with pytest.raises(ValueError, match="environment"):
        cov_recipe(environment=environment)


def test_environment_rule_holds_in_verify_bundle_in_both_directions(tmp_path):
    root = tmp_path / "gold"
    directory = write_cov_bundle(root)
    original = (directory / "manifest.json").read_bytes()

    def restore() -> None:
        (directory / "manifest.json").write_bytes(original)

    rewrite_manifest(directory, lambda m: m["recipe"].pop("environment"))
    with pytest.raises(ValueError, match="environment"):
        gold.verify_bundle(directory)
    restore()
    rewrite_manifest(directory, lambda m: m["recipe"]["environment"].update(extra="x"))
    with pytest.raises(ValueError, match="environment"):
        gold.verify_bundle(directory)
    restore()
    rewrite_manifest(directory, lambda m: m["recipe"].update(numeric_policy="decimal-50/1"))
    with pytest.raises(ValueError, match="numeric_policy is not float64/1"):
        gold.verify_bundle(directory)
    restore()
    rewrite_manifest(directory, lambda m: m["recipe"]["environment"].update(numpy=""))
    with pytest.raises(ValueError, match="environment"):
        gold.verify_bundle(directory)
    restore()
    assert gold.verify_bundle(directory)["recipe"]["environment"] == ENV

    panel_dir = write_panel(root)
    rewrite_manifest(panel_dir, lambda m: m["recipe"].update(environment=ENV))
    with pytest.raises(ValueError, match="exactly the keys"):
        gold.verify_bundle(panel_dir)
    rewrite_manifest(panel_dir, lambda m: m["recipe"].pop("environment"))
    rewrite_manifest(panel_dir, lambda m: m["recipe"].update(numeric_policy="float64/1"))
    with pytest.raises(ValueError, match="numeric_policy is not decimal-50/1"):
        gold.verify_bundle(panel_dir)


@pytest.mark.parametrize(
    ("override", "match"),
    [
        ({"panel": ""}, "panel"),
        ({"panel": 5}, "panel"),
        ({"estimator": ""}, "estimator"),
        ({"ddof": True}, "ddof must be an integer"),
        ({"ddof": 1.0}, "ddof must be an integer"),
        ({"ddof": "1"}, "ddof must be an integer"),
        ({"annualisation": True}, "annualisation must be an integer"),
        ({"annualisation": None}, "annualisation must be an integer"),
        ({"trailing_months": 1}, "at least 2"),
        ({"trailing_months": 0}, "at least 2"),
        ({"trailing_months": True}, "at least 2"),
        ({"trailing_months": 2.0}, "at least 2"),
        ({"trailing_months": "36"}, "at least 2"),
    ],
)
def test_covariance_parameter_refusals(override, match):
    with pytest.raises(ValueError, match=match):
        cov_recipe(parameters={**COV_PARAMETERS, **override})


def test_covariance_parameters_have_exactly_the_contract_keys_and_allow_null_window():
    for bad in (
        {k: v for k, v in COV_PARAMETERS.items() if k != "ddof"},
        {**COV_PARAMETERS, "extra": 1},
        {"panel": "example"},
    ):
        with pytest.raises(ValueError, match="covariance parameters"):
            cov_recipe(parameters=bad)
    for good in (None, 2, 36):
        r = cov_recipe(parameters={**COV_PARAMETERS, "trailing_months": good})
        assert r["parameters"]["trailing_months"] == good
    assert gold.build_id(cov_recipe(parameters={**COV_PARAMETERS, "trailing_months": None})) != gold.build_id(
        cov_recipe()
    )


def test_risk_parameters_refusals():
    for bad in (
        {"portfolio": "mix"},
        {**RISK_PARAMETERS, "extra": "x"},
    ):
        with pytest.raises(ValueError, match="risk_contribution parameters"):
            risk_recipe(parameters=bad)
    for key in RISK_PARAMETERS:
        with pytest.raises(ValueError, match=key):
            risk_recipe(parameters={**RISK_PARAMETERS, key: ""})
        with pytest.raises(ValueError, match=key):
            risk_recipe(parameters={**RISK_PARAMETERS, key: 1})


def test_covariance_parent_rules():
    assert cov_recipe()["parents"] == [PANEL_PARENT]
    with pytest.raises(ValueError, match="covariance parents"):
        cov_recipe(parents=[])
    with pytest.raises(ValueError, match="covariance parents"):
        cov_recipe(parents=[PANEL_PARENT, {**PORTFOLIO_PARENT, "role": "portfolio"}])
    with pytest.raises(ValueError, match="covariance parents"):
        cov_recipe(parents=[{**PANEL_PARENT, "role": "equity"}])  # wrong role
    with pytest.raises(ValueError, match="covariance parents"):
        cov_recipe(parents=[{**PANEL_PARENT, "kind": "portfolio_path"}])  # wrong kind
    with pytest.raises(ValueError, match="covariance parents"):
        cov_recipe(parents=[{**PANEL_PARENT, "kind": "covariance"}])
    with pytest.raises(ValueError, match="parent"):  # a factor series is not a bundle parent
        cov_recipe(parents=[factor_parent("panel", "some.equity")])
    with pytest.raises(ValueError, match="repeat"):
        cov_recipe(parents=[PANEL_PARENT, PANEL_PARENT])


def test_risk_parent_rules():
    assert risk_recipe(parents=[COV_PARENT, PORTFOLIO_PARENT])["parents"] == [COV_PARENT, PORTFOLIO_PARENT]
    for parents in (
        [],
        [COV_PARENT],
        [PORTFOLIO_PARENT],
        [COV_PARENT, PORTFOLIO_PARENT, PANEL_PARENT],
        [COV_PARENT, {**PORTFOLIO_PARENT, "kind": "panel"}],
        [{**COV_PARENT, "kind": "panel"}, PORTFOLIO_PARENT],
        [COV_PARENT, {**PORTFOLIO_PARENT, "role": "panel"}],
        [{**COV_PARENT, "role": "cov"}, PORTFOLIO_PARENT],
        [{**COV_PARENT, "role": "portfolio"}, {**PORTFOLIO_PARENT, "role": "covariance"}],
    ):
        with pytest.raises(ValueError, match=r"(risk_contribution parents|repeat)"):
            risk_recipe(parents=parents)
    with pytest.raises(ValueError, match="parent"):
        risk_recipe(parents=[COV_PARENT, factor_parent("portfolio", "some.equity")])


def test_decimal_kinds_keep_their_parent_freedom():
    # §6a adds parent rules for the float kinds only: a panel may still have any number of members.
    parents = [factor_parent(c, f"some.{c}") for c in ("a", "b", "c")]
    assert len(gold.recipe("panel", SPEC, PANEL_PARAMETERS, parents, "x")["parents"]) == 3


# bundles -----------------------------------------------------------------------------------

MEMBERS = ("bonds", "equity")
WINDOWS = (
    ("full", "full", "2023-01-31", "2024-12-31", "24"),
    ("trailing:2024-11-30", "trailing", "2023-12-31", "2024-11-30", "12"),
    ("trailing:2024-12-31", "trailing", "2024-01-31", "2024-12-31", "12"),
)
COV_VALUES = {
    ("bonds", "bonds"): 0.1,
    ("bonds", "equity"): 1 / 3,
    ("equity", "bonds"): 1 / 3,
    ("equity", "equity"): 1e-17,
}


def cov_tables(bid: str) -> dict[str, bytes]:
    dim = [
        row("covariance", "dim_window", covariance_build_id=bid, window_id=w, window_kind=k,
            first_period_end=first, last_period_end=last, n_obs=n)
        for w, k, first, last, n in reversed(WINDOWS)
    ]  # fmt: skip
    fact = [
        row("covariance", "fact_covariance", covariance_build_id=bid, window_id=w, member_i=i, member_j=j,
            covariance=gold.float_text(v), correlation=gold.float_text(v * 2))
        for w, *_ in WINDOWS
        for (i, j), v in COV_VALUES.items()
    ]  # fmt: skip
    vol = [
        row("covariance", "fact_volatility", covariance_build_id=bid, window_id=w, member_code=m,
            volatility=gold.float_text(0.1 * (n + 1)))
        for w, *_ in WINDOWS
        for n, m in enumerate(MEMBERS)
    ]  # fmt: skip
    return {
        "dim_window": gold.table_bytes("covariance", "dim_window", dim),
        "fact_covariance": gold.table_bytes("covariance", "fact_covariance", fact),
        "fact_volatility": gold.table_bytes("covariance", "fact_volatility", vol),
    }


def write_cov_bundle(root: Path) -> Path:
    r = cov_recipe()
    directory, existed = gold.write_bundle(root, r, cov_tables(gold.build_id(r)))
    assert existed is False
    return directory


def test_covariance_bundle_is_written_verified_and_reopened_with_floats(tmp_path):
    root = tmp_path / "gold"
    directory = write_cov_bundle(root)
    r = cov_recipe()
    bid = sha(cj(r))
    assert directory == root / "covariance" / bid
    assert sorted(p.name for p in (directory / "tables").iterdir()) == [
        "dim_window.csv",
        "fact_covariance.csv",
        "fact_volatility.csv",
    ]
    m = gold.verify_bundle(directory)
    assert m["recipe"] == r
    assert [e["name"] for e in m["tables"]] == ["dim_window", "fact_covariance", "fact_volatility"]
    assert [e["rows"] for e in m["tables"]] == [3, 12, 6]
    bundle = gold.open_bundle(root, "covariance", bid)
    assert bundle.kind == "covariance"
    assert bundle.recipe["environment"] == ENV
    assert bundle.recipe["numeric_policy"] == "float64/1"
    # Window rows come back full first, then the trailing windows by last_period_end.
    assert [r_["window_id"] for r_ in bundle.table("dim_window")] == [w[0] for w in WINDOWS]
    covariances = bundle.floats("fact_covariance", "covariance")
    assert len(covariances) == 12
    assert all(isinstance(v, float) for v in covariances)
    first_window = [COV_VALUES[k] for k in sorted(COV_VALUES)]
    assert covariances[:4] == first_window  # exact: repr text reads back to the same float
    assert bundle.floats("fact_covariance", "correlation")[:4] == [v * 2 for v in first_window]
    assert bundle.floats("fact_volatility", "volatility")[:2] == [0.1, 0.2]
    assert bundle.floats("dim_window", "n_obs") == [24.0, 12.0, 12.0]
    # An identical rewrite is "already there"; the same recipe gives the same bytes in two roots.
    again, existed = gold.write_bundle(root, r, cov_tables(bid))
    assert (again, existed) == (directory, True)
    other = write_cov_bundle(tmp_path / "other")
    files = lambda d: {p.relative_to(d).as_posix(): p.read_bytes() for p in d.rglob("*") if p.is_file()}  # noqa: E731
    assert files(other) == files(directory)


def test_covariance_bundle_files_modes_and_tamper_checks(tmp_path):
    directory = write_cov_bundle(tmp_path / "gold")
    for path in (directory, directory / "tables", directory.parent):
        assert stat.S_IMODE(path.stat().st_mode) == 0o700
    for path in directory.rglob("*.csv"):
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
    csv_path = directory / "tables" / "fact_volatility.csv"
    csv_path.write_bytes(csv_path.read_bytes() + b"x\n")
    with pytest.raises(ValueError, match="file sha256 differs"):
        gold.verify_bundle(directory)


def test_covariance_bundle_refuses_the_wrong_tables():
    r = cov_recipe()
    tables = cov_tables(gold.build_id(r))
    with pytest.raises(ValueError, match="missing covariance tables"):
        gold.manifest(r, {k: v for k, v in tables.items() if k != "fact_volatility"})
    with pytest.raises(ValueError, match="unknown covariance tables"):
        gold.manifest(r, {**tables, "fact_portfolio_risk": b""})
    with pytest.raises(ValueError, match="header"):
        gold.manifest(r, {**tables, "dim_window": b"a,b\n"})


def test_risk_bundle_is_written_verified_and_reopened_with_floats(tmp_path):
    root = tmp_path / "gold"
    r = risk_recipe()
    bid = gold.build_id(r)
    risk = [
        row("risk_contribution", "fact_portfolio_risk", risk_build_id=bid, window_id=w,
            portfolio_variance=gold.float_text(0.0123), portfolio_volatility=gold.float_text(0.0123**0.5),
            diversification_ratio=gold.float_text(1.25), euler_relative_gap=gold.float_text(1e-17))
        for w in ("w2", "w1")
    ]  # fmt: skip
    contributions = [
        row("risk_contribution", "fact_risk_contribution", risk_build_id=bid, window_id=w, member_code=m,
            weight=gold.float_text(0.5), marginal_contribution=gold.float_text(1 / 3),
            component_contribution=gold.float_text(1 / 6), percentage_contribution=gold.float_text(0.5))
        for w in ("w1", "w2")
        for m in MEMBERS
    ]  # fmt: skip
    tables = {
        "fact_portfolio_risk": gold.table_bytes("risk_contribution", "fact_portfolio_risk", risk),
        "fact_risk_contribution": gold.table_bytes(
            "risk_contribution", "fact_risk_contribution", contributions
        ),
    }
    directory, existed = gold.write_bundle(root, r, tables)
    assert existed is False
    assert directory == root / "risk_contribution" / sha(cj(r))
    assert gold.verify_bundle(directory)["recipe"] == r
    bundle = gold.open_bundle(root, "risk_contribution", bid)
    assert [x["window_id"] for x in bundle.table("fact_portfolio_risk")] == ["w1", "w2"]
    assert bundle.floats("fact_portfolio_risk", "euler_relative_gap") == [1e-17, 1e-17]
    assert bundle.floats("fact_portfolio_risk", "portfolio_volatility") == [0.0123**0.5] * 2
    assert bundle.floats("fact_risk_contribution", "marginal_contribution") == [1 / 3] * 4
    assert bundle.recipe["parents"] == [COV_PARENT, PORTFOLIO_PARENT]


def float_cell_bundle(root: Path, cells: list[str]) -> gold.Bundle:
    r = cov_recipe()
    bid = gold.build_id(r)
    tables = cov_tables(bid)
    rows = [
        row("covariance", "fact_volatility", covariance_build_id=bid, window_id="full", member_code=f"m{n}",
            volatility=cell)
        for n, cell in enumerate(cells)
    ]  # fmt: skip
    tables["fact_volatility"] = gold.table_bytes("covariance", "fact_volatility", rows)
    gold.write_bundle(root, r, tables)
    return gold.open_bundle(root, "covariance", bid)


def test_floats_refuses_empty_non_number_non_finite_and_unknown_column(tmp_path):
    with pytest.raises(ValueError, match="is empty"):
        float_cell_bundle(tmp_path / "a", ["0.1", ""]).floats("fact_volatility", "volatility")
    with pytest.raises(ValueError, match="not a float"):
        float_cell_bundle(tmp_path / "b", ["abc"]).floats("fact_volatility", "volatility")
    for cell in ("nan", "inf", "-inf", "Infinity"):
        with pytest.raises(ValueError, match="not finite"):
            float_cell_bundle(tmp_path / f"c{cell}", [cell]).floats("fact_volatility", "volatility")
    bundle = float_cell_bundle(tmp_path / "d", ["0.1", "1e-17"])
    assert bundle.floats("fact_volatility", "volatility") == [0.1, 1e-17]
    with pytest.raises(ValueError, match="no column"):
        bundle.floats("fact_volatility", "nope")
    with pytest.raises(ValueError, match="unknown covariance table"):
        bundle.floats("fact_portfolio_risk", "window_id")


def test_floats_reads_the_file_checked_against_the_manifest(tmp_path):
    bundle = float_cell_bundle(tmp_path / "gold", ["0.1"])
    path = bundle.directory / "tables" / "fact_volatility.csv"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="file sha256 differs"):
        bundle.floats("fact_volatility", "volatility")


# spec readers ------------------------------------------------------------------------------

COV_TEXT = """\
identity: {name: cov, version: 0.1.0, status: proposed}
kind: covariance
panel: example
estimator: sample
ddof: 1
annualisation: 12
trailing_months: 36
"""

RISK_TEXT = """\
identity: {name: risk, version: 0.1.0, status: proposed}
kind: risk_contribution
portfolio: mix
covariance: cov
"""


def test_read_covariance_spec_valid(tmp_path):
    spec = gold.read_covariance_spec(write(tmp_path, COV_TEXT))
    assert spec == {
        "name": "cov",
        "version": "0.1.0",
        "status": "proposed",
        "kind": "covariance",
        "panel": "example",
        "estimator": "sample",
        "ddof": 1,
        "annualisation": 12,
        "trailing_months": 36,
        "sha256": sha(COV_TEXT.encode()),
    }
    # The fields feed a recipe directly.
    params = {k: spec[k] for k in ("panel", "estimator", "ddof", "annualisation", "trailing_months")}
    r = gold.recipe(
        "covariance", {k: spec[k] for k in ("name", "version", "sha256")}, params, [PANEL_PARENT], "c",
        environment=ENV,
    )  # fmt: skip
    assert r["parameters"] == params


@pytest.mark.parametrize("value", ["null", "~", "2", "3", "120"])
def test_read_covariance_spec_trailing_months_null_or_at_least_two(tmp_path, value):
    spec = gold.read_covariance_spec(
        write(tmp_path, COV_TEXT.replace("trailing_months: 36", f"trailing_months: {value}"))
    )
    assert spec["trailing_months"] == (None if value in ("null", "~") else int(value))


@pytest.mark.parametrize(
    ("old", "new", "match"),
    [
        ("kind: covariance", "kind: panel", "kind"),
        ("kind: covariance\n", "", "exactly the keys"),
        ("kind: covariance\n", "kind: covariance\nextra: 1\n", "exactly the keys"),
        ("trailing_months: 36\n", "", "exactly the keys"),
        ("panel: example", "panel: ''", "panel"),
        ("panel: example", "panel: 5", "panel"),
        ("estimator: sample", "estimator: shrunk", "estimator"),
        ("ddof: 1", "ddof: 0", "ddof"),
        ("ddof: 1", "ddof: true", "ddof"),
        ("ddof: 1", "ddof: 1.0", "ddof"),
        ("ddof: 1", 'ddof: "1"', "ddof"),
        ("annualisation: 12", "annualisation: 252", "annualisation"),
        ("annualisation: 12", "annualisation: 12.0", "annualisation"),
        ("annualisation: 12", "annualisation: true", "annualisation"),
        ("trailing_months: 36", "trailing_months: 1", "at least 2"),
        ("trailing_months: 36", "trailing_months: 0", "at least 2"),
        ("trailing_months: 36", "trailing_months: -6", "at least 2"),
        ("trailing_months: 36", "trailing_months: true", "at least 2"),
        ("trailing_months: 36", "trailing_months: false", "at least 2"),
        ("trailing_months: 36", "trailing_months: 36.0", "at least 2"),
        ("trailing_months: 36", 'trailing_months: "36"', "at least 2"),
        ("trailing_months: 36", "trailing_months: ''", "at least 2"),
        ("status: proposed", "status: ''", "status"),
        ("{name: cov, version: 0.1.0, status: proposed}", "{name: cov, version: 0.1.0}", "identity"),
    ],
)
def test_read_covariance_spec_refusals(tmp_path, old, new, match):
    assert old in COV_TEXT
    with pytest.raises(ValueError, match=match):
        gold.read_covariance_spec(write(tmp_path, COV_TEXT.replace(old, new, 1)))


def test_read_covariance_spec_refuses_non_mapping_and_bad_yaml(tmp_path):
    with pytest.raises(ValueError, match="must be a mapping"):
        gold.read_covariance_spec(write(tmp_path, "- a\n"))
    with pytest.raises(ValueError, match="not YAML"):
        gold.read_covariance_spec(write(tmp_path, "a: [\n"))


def test_read_risk_spec_valid(tmp_path):
    spec = gold.read_risk_spec(write(tmp_path, RISK_TEXT))
    assert spec == {
        "name": "risk",
        "version": "0.1.0",
        "status": "proposed",
        "kind": "risk_contribution",
        "portfolio": "mix",
        "covariance": "cov",
        "sha256": sha(RISK_TEXT.encode()),
    }
    params = {k: spec[k] for k in ("portfolio", "covariance")}
    r = gold.recipe(
        "risk_contribution", {k: spec[k] for k in ("name", "version", "sha256")}, params,
        [COV_PARENT, PORTFOLIO_PARENT], "c", environment=ENV,
    )  # fmt: skip
    assert r["parameters"] == params


@pytest.mark.parametrize(
    ("old", "new", "match"),
    [
        ("kind: risk_contribution", "kind: covariance", "kind"),
        ("kind: risk_contribution\n", "", "exactly the keys"),
        ("covariance: cov\n", "covariance: cov\nextra: 1\n", "exactly the keys"),
        ("portfolio: mix\n", "", "exactly the keys"),
        ("covariance: cov\n", "", "exactly the keys"),
        ("portfolio: mix", "portfolio: ''", "portfolio"),
        ("portfolio: mix", "portfolio: 5", "portfolio"),
        ("covariance: cov", "covariance: ''", "covariance"),
        ("covariance: cov", "covariance: [cov]", "covariance"),
        ("status: proposed", "status: ''", "status"),
        ("{name: risk, version: 0.1.0, status: proposed}", "{name: risk, status: proposed}", "identity"),
    ],
)
def test_read_risk_spec_refusals(tmp_path, old, new, match):
    assert old in RISK_TEXT
    with pytest.raises(ValueError, match=match):
        gold.read_risk_spec(write(tmp_path, RISK_TEXT.replace(old, new, 1)))


def test_read_risk_spec_refuses_non_mapping_and_bad_yaml(tmp_path):
    with pytest.raises(ValueError, match="must be a mapping"):
        gold.read_risk_spec(write(tmp_path, "[]\n"))
    with pytest.raises(ValueError, match="not YAML"):
        gold.read_risk_spec(write(tmp_path, "a: [\n"))


def test_real_covariance_spec_loads_and_names_a_real_panel():
    panel = gold.read_panel_spec(SPECS / "panels" / "aud-four-sleeve.yaml")
    path = SPECS / "covariances" / "aud-four-sleeve-36m.yaml"
    spec = gold.read_covariance_spec(path)
    assert (spec["name"], spec["version"], spec["status"]) == ("aud-four-sleeve-36m", "0.1.0", "proposed")
    assert spec["panel"] == panel["name"]
    assert (spec["estimator"], spec["ddof"], spec["annualisation"], spec["trailing_months"]) == (
        "sample",
        1,
        12,
        36,
    )
    assert spec["sha256"] == sha(path.read_bytes())


def test_real_risk_spec_loads_and_names_a_real_portfolio_and_covariance():
    portfolio = gold.read_portfolio_spec(SPECS / "portfolios" / "aud-eq60-dur40.yaml")
    covariance = gold.read_covariance_spec(SPECS / "covariances" / "aud-four-sleeve-36m.yaml")
    path = SPECS / "risk" / "aud-eq60-dur40.yaml"
    spec = gold.read_risk_spec(path)
    assert (spec["name"], spec["version"], spec["status"]) == ("aud-eq60-dur40", "0.1.0", "proposed")
    assert spec["portfolio"] == portfolio["name"]
    assert spec["covariance"] == covariance["name"]
    assert spec["sha256"] == sha(path.read_bytes())
