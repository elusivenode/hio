"""Tests for hio.contracts.gold: the gold marts contract (OD-0233). Invented data only."""

from __future__ import annotations

import hashlib
import json
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


# --------------------------------------------------------------------------------------
# Constants and tables
# --------------------------------------------------------------------------------------


def test_constants():
    assert gold.SCHEMA == "hio.gold/1"
    assert gold.NUMERIC_POLICY == "decimal-50/1"
    assert gold.CTX.prec == 50
    assert gold.KINDS == ("panel", "portfolio_path")
    assert list(gold.TABLES) == ["panel", "portfolio_path"]


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
