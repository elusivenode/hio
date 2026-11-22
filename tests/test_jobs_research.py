"""The read API over pinned silver and gold (OD-0233; contract §9).

Everything is invented and built by hand under `tmp_path`: a small silver release made with
`hio.contracts.silver` (one fund, two snapshots, one revised close, one declared exclusion), two
factor builds written as the factor store lays them out, and a panel and a portfolio-path bundle made
with `hio.contracts.gold`. Nothing reads a real root, the network or git.
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

import pytest

from hio.contracts import gold
from hio.contracts import silver as contract
from hio.jobs.research import ResearchStore, SilverView
from hio.marketdata.silver_reader import FundObservations

BAR = "fact_listing_bar_day"
ADJ = "fact_vendor_adjusted_close_day"
DIST = "fact_distribution_event"
ZZZ = "ZZZ.US"


def _h(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _sk(label: str) -> str:
    return contract.sk("test", {"label": label})


SNAP = {"s1": _h("manifest one"), "s2": _h("manifest two")}
CAPTURE = {SNAP["s1"]: 1, SNAP["s2"]: 2}
CID = contract.correction_id(_h(f"obs{ZZZ}"), "exclude_distribution", "2024-01-09")

DIV0 = {
    "ex_date": "2024-01-05",
    "declaration_date": "2024-01-02",
    "record_date": "2024-01-08",
    "payment_date": "2024-01-15",
    "amount_unadjusted": "0.50",
    "amount_split_adjusted": "0.25",
    "currency": "USD",
    "period_label": "Q4",
    "franking": "",
}
DIV1 = {  # the declared exclusion
    "ex_date": "2024-01-09",
    "declaration_date": "",
    "record_date": "2024-01-10",
    "payment_date": "2024-01-16",
    "amount_unadjusted": "0.40",
    "amount_split_adjusted": "0.20",
    "currency": "USD",
    "period_label": "Q4 again",
    "franking": "",
}


def _eod(i: int, snap: str) -> dict[str, str]:
    revised = snap == "s2" and i == 1
    return {
        "date": f"2024-01-{i + 2:02d}",
        "open": "9.50",
        "high": "12.50",
        "low": "9.00",
        "close": "11.30" if revised else f"{10 + i}.25",
        "volume": str(1000 + i),
        "adjusted_close": "11.27" if revised else f"{10 + i}.20",
    }


def _row(table: str, **cells: str) -> dict[str, str]:
    row = dict.fromkeys(contract.TABLES[table], "")
    unknown = set(cells) - set(row)
    assert not unknown, f"{table}: {sorted(unknown)}"
    row.update(cells)
    return row


@dataclass
class Parts:
    tables: dict[str, list[dict[str, str]]] = field(default_factory=lambda: {n: [] for n in contract.TABLES})
    records: dict[tuple[str, str], list[dict[str, str]]] = field(default_factory=dict)
    newest: dict[tuple[str, str], tuple[str, str]] = field(default_factory=dict)
    seen: set[str] = field(default_factory=set)


def _record(parts: Parts, snap: str, kind: str, index: int, record: dict[str, str]) -> str:
    file_sha = _h(f"{ZZZ}:{kind}:{snap}")
    rid = contract.source_record_id(file_sha, index)
    if rid not in parts.seen:
        parts.seen.add(rid)
        parts.tables["source_record"].append(
            _row(
                "source_record",
                source_record_id=rid,
                file_sha256=file_sha,
                row_index=str(index),
                record_sha256=contract.record_sha256(record),
            )
        )
    return rid


def _observe(
    parts: Parts,
    snap: str,
    table: str,
    quantity: str,
    coordinate: dict[str, str | int],
    measures: dict[str, str],
    further: dict[str, str],
    rid: str,
    index: int,
) -> None:
    series = f"{ZZZ}.{quantity}"
    oid = contract.observation_id(series, coordinate)
    fingerprint = contract.value_fingerprint(measures)
    newest = parts.newest.get((table, oid))
    if newest is not None and newest[0] == fingerprint:
        vid = newest[1]
    else:
        vid = contract.vintage_id(oid, fingerprint, SNAP[snap])
        parts.newest[(table, oid)] = (fingerprint, vid)
        parts.tables[table].append(
            _row(
                table,
                vintage_id=vid,
                observation_id=oid,
                series_id=series,
                series_sk=_sk(series),
                source_sk=_sk("source"),
                audit_sk=_sk("audit"),
                origin_source_record_id=rid,
                anchor_snapshot_id=SNAP[snap],
                first_captured_at=f"2024-02-0{CAPTURE[SNAP[snap]]}T00:00:00Z",
                **measures,
                **further,
            )
        )
    parts.tables["bridge_vintage_support"].append(
        _row("bridge_vintage_support", vintage_id=vid, source_record_id=rid, snapshot_id=SNAP[snap])
    )
    parts.records.setdefault((ZZZ, snap), []).append(
        {
            "fact_table": table,
            "series_id": series,
            "observation_id": oid,
            "vintage_id": vid,
            "source_record_id": rid,
            "row_index": str(index),
            "disposition": "selected",
            "reason": "",
        }
    )


def _bar(parts: Parts, snap: str, index: int, rec: dict[str, str]) -> None:
    rid = _record(parts, snap, "eod", index, rec)
    common = {
        "listing_sk": _sk("listing"),
        "instrument_sk": _sk("instrument"),
        "trade_date_sk": _sk(f"date:{rec['date']}"),
        "trade_date": rec["date"],
        "quote_currency_sk": _sk("currency"),
    }
    coordinate: dict[str, str | int] = {"trade_date": rec["date"]}
    bar = {k: rec[k] for k in contract.MEASURES[BAR]}
    _observe(parts, snap, BAR, "bar_day", coordinate, bar, common, rid, index)
    adjusted = {"adjusted_close": rec["adjusted_close"]}
    _observe(parts, snap, ADJ, "adjusted_close_day", coordinate, adjusted, common, rid, index)


def _distribution(parts: Parts, snap: str, index: int, rec: dict[str, str]) -> None:
    rid = _record(parts, snap, "div", index, rec)
    further = {
        "instrument_sk": _sk("instrument"),
        "currency_sk": _sk("currency"),
        "ex_date_sk": _sk(f"date:{rec['ex_date']}"),
        "declaration_date_sk": _sk("date:declaration"),
        "record_date_sk": _sk("date:record"),
        "payment_date_sk": _sk("date:payment"),
        "ex_date": rec["ex_date"],
        "occurrence": "0",
    }
    measures = {k: rec[k] for k in contract.MEASURES[DIST]}
    coordinate: dict[str, str | int] = {"ex_date": rec["ex_date"], "occurrence": 0}
    _observe(parts, snap, DIST, "distribution", coordinate, measures, further, rid, index)


def _exclude(parts: Parts, snap: str, index: int) -> None:
    (row,) = [
        r for r in parts.records[(ZZZ, snap)] if r["fact_table"] == DIST and r["row_index"] == str(index)
    ]
    row["disposition"] = "excluded"
    row["reason"] = CID
    parts.tables["fact_correction_application"].append(
        _row(
            "fact_correction_application",
            application_id=contract.application_id(CID, SNAP[snap], row["source_record_id"]),
            correction_id=CID,
            snapshot_id=SNAP[snap],
            target_source_record_id=row["source_record_id"],
            target_vintage_id=row["vintage_id"],
            disposition="excluded",
        )
    )


def make_parts() -> Parts:
    parts = Parts()
    for name, order in (("s1", "1"), ("s2", "2")):
        parts.tables["snapshot"].append(
            _row(
                "snapshot",
                snapshot_id=SNAP[name],
                name=name,
                source_id="some.source",
                capture_order=order,
                first_retrieved_at=f"2024-02-0{order}T00:00:00Z",
                last_retrieved_at=f"2024-02-0{order}T00:10:00Z",
            )
        )
    parts.tables["dim_instrument"].append(
        _row("dim_instrument", instrument_sk=_sk("instrument"), instrument_code="example-fund", name="A fund")
    )
    parts.tables["dim_listing"].append(
        _row(
            "dim_listing",
            listing_sk=_sk("listing"),
            instrument_code="example-fund",
            instrument_sk=_sk("instrument"),
            mic="XXXX",
            ticker="ZZZ",
            quote_currency="USD",
        )
    )
    parts.tables["source_identity_mapping"].append(
        _row(
            "source_identity_mapping",
            source_id="some.source",
            source_symbol=ZZZ,
            instrument_code="example-fund",
            listing_sk=_sk("listing"),
        )
    )
    for snap in ("s1", "s2"):
        for i in range(2):
            _bar(parts, snap, i, _eod(i, snap))
        _distribution(parts, snap, 0, DIV0)
        _distribution(parts, snap, 1, DIV1)
        _exclude(parts, snap, 1)
    parts.tables["correction_rule"].append(
        _row(
            "correction_rule",
            correction_id=CID,
            observation_spec_sha256=_h(f"obs{ZZZ}"),
            source_symbol=ZZZ,
            action="exclude_distribution",
            ex_date="2024-01-09",
            reason="a duplicate",
            evidence="an invented note",
        )
    )
    return parts


def write_release(root: Path, parts: Parts) -> str:
    tables = {name: contract.table_bytes(name, rows, CAPTURE) for name, rows in parts.tables.items()}
    selections = {}
    for name, snap in (("latest", "s2"), ("older", "s1")):
        rows = parts.records[(ZZZ, snap)]
        policy = contract.selection_policy_bytes(
            name, {ZZZ: SNAP[snap]}, {r["reason"] for r in rows if r["reason"]}
        )
        selections[contract.selection_id(policy)] = (policy, contract.selection_bytes(rows))
    core = contract.manifest_core(
        release_spec={"name": "funds", "version": "0.1.0", "sha256": _h("release spec")},
        register_sha256=_h("register"),
        observation_specs=[{"source_symbol": ZZZ, "sha256": _h(f"obs{ZZZ}")}],
        snapshots=[{"name": n, "manifest_sha256": SNAP[n]} for n in ("s1", "s2")],
        code_commit="0123abc",
        tables=tables,
        selections=selections,
    )
    _directory, existed = contract.write_release(root, core, tables, selections)
    assert not existed
    return contract.release_id(core)


# -- factor builds and bundles ------------------------------------------------------------------

EQUITY = ("equity.factor", "0.1.0", "aaaaaaaaaaaaaaaa")
EXCESS = ("bonds.factor", "0.2.0", "bbbbbbbbbbbbbbbb")
EQUITY_CSV = (
    b"period_start,period_end,total_return\n"
    b"2024-01-02,2024-01-03,0.010\n"
    b"2024-01-03,2024-01-04,-0.020\n"
    b"2024-01-04,2024-01-05,0.005\n"
)
EXCESS_CSV = (
    b"period_start,period_end,asset_return,cash_return,excess_return\n"
    b"2024-01-02,2024-01-03,0.030,0.001,0.029\n"
    b"2024-01-03,2024-01-04,0.020,0.001,0.019\n"
)


def write_factor(
    store: Path, ident: tuple[str, str, str], data: bytes, series_class: str, *, numeraire: str = "USD"
) -> str:
    factor_id, version, bid = ident
    directory = store / factor_id / version / bid
    directory.mkdir(parents=True)
    digest = hashlib.sha256(data).hexdigest()
    record = {
        "factor_id": factor_id,
        "spec_version": version,
        "build_id": bid,
        "series_sha256": digest,
        "series_class": series_class,
        "numeraire": numeraire,
    }
    (directory / "build.json").write_text(json.dumps(record, sort_keys=True))
    (directory / "series.csv").write_bytes(data)
    return digest


def write_panel(root: Path, parent: dict[str, str]) -> str:
    recipe = gold.recipe(
        "panel",
        {"name": "example", "version": "0.1.0", "sha256": _h("panel spec")},
        {
            "frequency": "monthly",
            "alignment": "common_boundaries",
            "incomplete_periods": "exclude",
            "members": {"equity": EQUITY[0]},
        },
        [parent],
        "0123abc",
    )
    pid = gold.build_id(recipe)
    tables = {
        "bridge_panel_member": [
            {
                "panel_build_id": pid,
                "member_code": "equity",
                "column_order": "0",
                "factor_id": EQUITY[0],
                "spec_version": EQUITY[1],
                "input_build_id": EQUITY[2],
                "input_series_sha256": parent["payload_sha256"],
                "series_class": "total_return",
                "numeraire": "USD",
            }
        ],
        "fact_panel_return": [
            {
                "panel_build_id": pid,
                "member_code": "equity",
                "period_start": start,
                "period_end": end,
                "return": value,
                "asset_return": "",
                "cash_return": "",
            }
            for start, end, value in (
                ("2024-01-02", "2024-01-03", "0.010"),
                ("2024-01-03", "2024-01-04", "-0.020"),
            )
        ],
        "fact_panel_coverage": [
            {
                "panel_build_id": pid,
                "member_code": "equity",
                "first_boundary": "2024-01-02",
                "last_boundary": "2024-01-05",
                "boundaries": "4",
                "omitted_boundaries": "0",
                "common_first": "2024-01-02",
                "common_last": "2024-01-05",
                "months": "2",
            }
        ],
    }
    gold.write_bundle(root, recipe, {n: gold.table_bytes("panel", n, rows) for n, rows in tables.items()})
    return pid


def write_portfolio(root: Path, panel_id: str) -> str:
    panel = gold.open_bundle(root, "panel", panel_id)
    recipe = gold.recipe(
        "portfolio_path",
        {"name": "mix", "version": "0.1.0", "sha256": _h("portfolio spec")},
        {"panel": "example", "rebalance": "month_end", "weights": {"equity": "1"}},
        [{"role": "panel", "kind": "panel", "id": panel_id, "payload_sha256": panel.payload_sha256}],
        "0123abc",
    )
    qid = gold.build_id(recipe)
    tables = {
        "fact_target_allocation": [
            {"portfolio_build_id": qid, "member_code": "equity", "target_weight": "1"}
        ],
        "fact_portfolio_return": [
            {
                "portfolio_build_id": qid,
                "period_start": "2024-01-02",
                "period_end": "2024-01-03",
                "portfolio_return": "0.010",
                "wealth_index": "1.010",
            }
        ],
        "fact_return_contribution": [
            {
                "portfolio_build_id": qid,
                "member_code": "equity",
                "period_start": "2024-01-02",
                "period_end": "2024-01-03",
                "start_weight": "1",
                "member_return": "0.010",
                "contribution": "0.010",
            }
        ],
    }
    gold.write_bundle(
        root, recipe, {n: gold.table_bytes("portfolio_path", n, rows) for n, rows in tables.items()}
    )
    return qid


ENVIRONMENT = {"numpy": "9.9.9", "python": "3.99"}
WINDOW = "full"
RETURNS = (0.010, -0.020)  # the panel's one member, over its two months
VARIANCE = statistics.variance(RETURNS) * 12  # one member: a 1 x 1 covariance matrix
VOLATILITY = math.sqrt(VARIANCE)


def write_covariance(root: Path, panel_id: str) -> str:
    """A covariance bundle for the one-member panel, with one `full` window (hand-built rows)."""
    panel = gold.open_bundle(root, "panel", panel_id)
    recipe = gold.recipe(
        "covariance",
        {"name": "cov", "version": "0.1.0", "sha256": _h("covariance spec")},
        {"panel": "example", "estimator": "sample", "ddof": 1, "annualisation": 12, "trailing_months": None},
        [{"role": "panel", "kind": "panel", "id": panel_id, "payload_sha256": panel.payload_sha256}],
        "0123abc",
        environment=ENVIRONMENT,
    )
    cid = gold.build_id(recipe)
    tables = {
        "dim_window": [
            {
                "covariance_build_id": cid,
                "window_id": WINDOW,
                "window_kind": "full",
                "first_period_end": "2024-01-03",
                "last_period_end": "2024-01-04",
                "n_obs": "2",
            }
        ],
        "fact_covariance": [
            {
                "covariance_build_id": cid,
                "window_id": WINDOW,
                "member_i": "equity",
                "member_j": "equity",
                "covariance": gold.float_text(VARIANCE),
                "correlation": gold.float_text(1.0),
            }
        ],
        "fact_volatility": [
            {
                "covariance_build_id": cid,
                "window_id": WINDOW,
                "member_code": "equity",
                "volatility": gold.float_text(VOLATILITY),
            }
        ],
    }
    gold.write_bundle(
        root, recipe, {n: gold.table_bytes("covariance", n, rows) for n, rows in tables.items()}
    )
    return cid


def write_risk(root: Path, covariance_id: str, portfolio_id: str) -> str:
    """A risk bundle for the one-member portfolio (weight 1) on the covariance bundle above."""
    covariance = gold.open_bundle(root, "covariance", covariance_id)
    portfolio = gold.open_bundle(root, "portfolio_path", portfolio_id)
    recipe = gold.recipe(
        "risk_contribution",
        {"name": "risk", "version": "0.1.0", "sha256": _h("risk spec")},
        {"portfolio": "mix", "covariance": "cov"},
        [
            {
                "role": "covariance",
                "kind": "covariance",
                "id": covariance_id,
                "payload_sha256": covariance.payload_sha256,
            },
            {
                "role": "portfolio",
                "kind": "portfolio_path",
                "id": portfolio_id,
                "payload_sha256": portfolio.payload_sha256,
            },
        ],
        "0123abc",
        environment=ENVIRONMENT,
    )
    rid = gold.build_id(recipe)
    tables = {
        "fact_portfolio_risk": [
            {
                "risk_build_id": rid,
                "window_id": WINDOW,
                "portfolio_variance": gold.float_text(VARIANCE),
                "portfolio_volatility": gold.float_text(VOLATILITY),
                "diversification_ratio": gold.float_text(1.0),
                "euler_relative_gap": gold.float_text(0.0),
            }
        ],
        "fact_risk_contribution": [
            {
                "risk_build_id": rid,
                "window_id": WINDOW,
                "member_code": "equity",
                "weight": gold.float_text(1.0),
                "marginal_contribution": gold.float_text(VOLATILITY),
                "component_contribution": gold.float_text(VOLATILITY),
                "percentage_contribution": gold.float_text(1.0),
            }
        ],
    }
    gold.write_bundle(
        root, recipe, {n: gold.table_bytes("risk_contribution", n, rows) for n, rows in tables.items()}
    )
    return rid


@dataclass
class World:
    silver_root: Path
    factor_store: Path
    gold_root: Path
    release_id: str
    equity_sha: str
    excess_sha: str
    panel_id: str
    portfolio_id: str

    def store(self) -> ResearchStore:
        return ResearchStore(self.silver_root, self.factor_store, self.gold_root)


@pytest.fixture
def world(tmp_path: Path) -> World:
    silver_root, factor_store, gold_root = tmp_path / "silver", tmp_path / "factors", tmp_path / "gold"
    release_id = write_release(silver_root, make_parts())
    equity_sha = write_factor(factor_store, EQUITY, EQUITY_CSV, "total_return")
    excess_sha = write_factor(factor_store, EXCESS, EXCESS_CSV, "excess")
    parent = {
        "role": "equity",
        "kind": "factor_series",
        "id": EQUITY[2],
        "payload_sha256": equity_sha,
        "factor_id": EQUITY[0],
        "spec_version": EQUITY[1],
    }
    panel_id = write_panel(gold_root, parent)
    portfolio_id = write_portfolio(gold_root, panel_id)
    return World(
        silver_root, factor_store, gold_root, release_id, equity_sha, excess_sha, panel_id, portfolio_id
    )


def _tables(con) -> set[str]:
    return {r[0] for r in con.execute("SHOW TABLES").fetchall()}


def _columns(con, table: str) -> list[str]:
    sql = "SELECT column_name FROM information_schema.columns WHERE table_name = ? ORDER BY ordinal_position"
    return [r[0] for r in con.execute(sql, [table]).fetchall()]


# -- the surface --------------------------------------------------------------------------------


def test_the_public_attribute_names_are_exactly_the_four_reads(world):
    wanted = {"silver", "factor_series", "bundle", "connect"}
    assert {n for n in dir(ResearchStore) if not n.startswith("_")} == wanted
    assert {n for n in dir(world.store()) if not n.startswith("_")} == wanted
    assert {n for n in dir(ResearchStore()) if not n.startswith("_")} == wanted


def test_a_method_whose_root_was_not_given_refuses(world):
    with pytest.raises(ValueError, match="silver_root"):
        ResearchStore(factor_store=world.factor_store, gold_root=world.gold_root).silver(
            world.release_id, "latest"
        )
    with pytest.raises(ValueError, match="factor_store"):
        ResearchStore(silver_root=world.silver_root, gold_root=world.gold_root).factor_series(*EQUITY)
    with pytest.raises(ValueError, match="gold_root"):
        ResearchStore(silver_root=world.silver_root, factor_store=world.factor_store).bundle(
            "panel", world.panel_id
        )


def test_roots_may_be_text_or_paths(world):
    store = ResearchStore(str(world.silver_root), str(world.factor_store), str(world.gold_root))
    assert store.silver(world.release_id, "latest").release_id == world.release_id
    assert store.factor_series(*EQUITY).factor_id == EQUITY[0]
    assert store.bundle("panel", world.panel_id).build_id == world.panel_id


# -- silver --------------------------------------------------------------------------------------


def test_silver_resolves_a_selection_by_name_and_by_id(world):
    store = world.store()
    by_name = store.silver(world.release_id, "latest")
    assert isinstance(by_name, SilverView)
    assert by_name.release_id == world.release_id
    assert len(by_name.selection_id) == 64
    by_id = store.silver(world.release_id, by_name.selection_id)
    assert by_id.selection_id == by_name.selection_id
    assert store.silver(world.release_id, "older").selection_id != by_name.selection_id
    with pytest.raises(ValueError, match="unknown selection"):
        store.silver(world.release_id, "nope")


def test_silver_table_returns_rows_as_dicts_of_text(world):
    view = world.store().silver(world.release_id, "latest")
    snapshots = view.table("snapshot")
    assert [r["name"] for r in snapshots] == ["s1", "s2"]
    assert all(isinstance(v, str) for r in snapshots for v in r.values())
    assert len(view.table(BAR)) == 3  # the revised close has two vintages
    snapshots[0]["name"] = "changed"  # a caller's change does not reach the release
    assert view.table("snapshot")[0]["name"] == "s1"
    with pytest.raises(ValueError, match="unknown silver table"):
        view.table("nope")


def test_silver_fund_observations(world):
    view = world.store().silver(world.release_id, "latest")
    observed = view.fund_observations(ZZZ)
    assert isinstance(observed, FundObservations)
    assert observed.snapshot_name == "s2"
    assert observed.quote_currency == "USD"
    assert observed.closes == [
        {"date": "2024-01-02", "close": "10.25", "adjusted_close": "10.20"},
        {"date": "2024-01-03", "close": "11.30", "adjusted_close": "11.27"},
    ]
    assert [d["ex_date"] for d in observed.distributions] == ["2024-01-05"]
    assert len(observed.corrections) == 1
    with pytest.raises(ValueError, match="not a member"):
        view.fund_observations("QQQ.US")


def test_selected_leaves_out_an_excluded_vintage(world):
    view = world.store().silver(world.release_id, "latest")
    everything = view.table(DIST)
    assert sorted(r["ex_date"] for r in everything) == ["2024-01-05", "2024-01-09"]
    assert [r["ex_date"] for r in view.selected(DIST)] == ["2024-01-05"]
    assert [r["ex_date"] for r in view.table(DIST) if r["ex_date"] == "2024-01-09"] != []  # still in the fact


def test_selected_of_an_older_snapshot_returns_the_older_vintage(world):
    store = world.store()
    latest = store.silver(world.release_id, "latest").selected(BAR)
    older = store.silver(world.release_id, "older").selected(BAR)
    assert sorted(r["close"] for r in latest) == ["10.25", "11.30"]
    assert sorted(r["close"] for r in older) == ["10.25", "11.25"]
    assert {r["vintage_id"] for r in latest} != {r["vintage_id"] for r in older}
    assert [
        r["close"]
        for r in store.silver(world.release_id, "older").selected(BAR)
        if r["trade_date"] == "2024-01-03"
    ] == ["11.25"]
    # the unchanged first-day vintage is shared by both selections
    assert {r["vintage_id"] for r in latest} & {r["vintage_id"] for r in older}


def test_selected_refuses_a_name_that_is_not_a_fact_table(world):
    view = world.store().silver(world.release_id, "latest")
    for name in ("snapshot", "nope", "dim_date"):
        with pytest.raises(ValueError, match="not a silver fact table"):
            view.selected(name)


def test_a_tampered_release_is_refused(world):
    path = world.silver_root / "v2" / world.release_id / "tables" / f"{BAR}.csv"
    path.write_bytes(path.read_bytes().replace(b"11.30", b"11.31"))
    store = world.store()
    with pytest.raises(ValueError, match="sha256"):
        store.silver(world.release_id, "latest")
    assert _tables(store.connect()) == set()  # a refused release registers nothing


def test_a_release_id_that_is_not_a_full_id_is_refused(world):
    with pytest.raises(ValueError, match="sha256"):
        world.store().silver(world.release_id[:16], "latest")
    with pytest.raises(ValueError):
        world.store().silver("f" * 64, "latest")


# -- factor series ---------------------------------------------------------------------------------


def test_factor_series_is_verified_and_pinned(world):
    store = world.store()
    series = store.factor_series(*EQUITY)
    assert series.series_class == "total_return"
    assert series.series_sha256 == world.equity_sha
    assert [r["total_return"] for r in series.rows] == ["0.010", "-0.020", "0.005"]
    pinned = store.factor_series(*EQUITY, series_sha256=world.equity_sha)
    assert pinned == series
    assert store.factor_series(*EXCESS).series_class == "excess"


def test_a_wrong_series_pin_is_refused(world):
    with pytest.raises(ValueError, match="series_sha256"):
        world.store().factor_series(*EQUITY, series_sha256=world.excess_sha)
    with pytest.raises(ValueError, match="series_sha256"):
        world.store().factor_series(*EQUITY, series_sha256="0" * 64)


def test_a_wrong_or_missing_factor_build_is_refused(world):
    store = world.store()
    with pytest.raises(ValueError, match="not a factor build directory"):
        store.factor_series(EQUITY[0], EQUITY[1], "cccccccccccccccc")
    with pytest.raises(ValueError, match="path component"):
        store.factor_series("../" + EQUITY[0], EQUITY[1], EQUITY[2])


def test_a_tampered_series_is_refused(world):
    path = world.factor_store / EQUITY[0] / EQUITY[1] / EQUITY[2] / "series.csv"
    path.write_bytes(path.read_bytes().replace(b"0.010", b"0.011"))
    store = world.store()
    with pytest.raises(ValueError, match="sha256"):
        store.factor_series(*EQUITY)
    assert _tables(store.connect()) == set()


# -- bundles -----------------------------------------------------------------------------------------


def test_bundle_opens_a_verified_bundle(world):
    store = world.store()
    panel = store.bundle("panel", world.panel_id)
    assert panel.kind == "panel"
    assert panel.build_id == world.panel_id
    assert [r["return"] for r in panel.table("fact_panel_return")] == ["0.010", "-0.020"]
    assert panel.decimals("fact_panel_return", "return") == [Decimal("0.010"), Decimal("-0.020")]
    portfolio = store.bundle("portfolio_path", world.portfolio_id)
    assert portfolio.recipe["parents"][0]["id"] == world.panel_id


def test_a_tampered_bundle_is_refused(world):
    path = world.gold_root / "panel" / world.panel_id / "tables" / "fact_panel_return.csv"
    path.write_bytes(path.read_bytes().replace(b"0.010", b"0.011"))
    store = world.store()
    with pytest.raises(ValueError, match="sha256"):
        store.bundle("panel", world.panel_id)
    assert _tables(store.connect()) == set()


def test_a_bundle_is_opened_by_its_full_id_and_kind_only(world):
    store = world.store()
    with pytest.raises(ValueError, match="sha256"):
        store.bundle("panel", world.panel_id[:16])
    with pytest.raises(ValueError, match="unknown gold kind"):
        store.bundle("latest", world.panel_id)
    with pytest.raises(ValueError):
        store.bundle("portfolio_path", world.panel_id)  # the right id under the wrong kind


# -- connect -----------------------------------------------------------------------------------------


def test_opening_nothing_gives_an_empty_database(world):
    assert _tables(world.store().connect()) == set()
    assert _tables(ResearchStore().connect()) == set()


def test_connect_registers_silver_with_every_column_varchar(world):
    store = world.store()
    store.silver(world.release_id, "latest")
    con = store.connect()
    names = _tables(con)
    assert {f"silver_{t}" for t in contract.TABLES} | {"silver_selection"} == names
    for table in names:
        types = {
            r[0]
            for r in con.execute(
                f"SELECT data_type FROM information_schema.columns WHERE table_name = '{table}'"
            ).fetchall()
        }
        assert types == {"VARCHAR"}
    assert _columns(con, "silver_snapshot")[0] == "release_id"
    assert con.execute("SELECT DISTINCT release_id FROM silver_snapshot").fetchall() == [(world.release_id,)]
    assert con.execute(f"SELECT count(*) FROM silver_{BAR}").fetchone() == (3,)
    assert _columns(con, "silver_selection") == ["release_id", "selection_id", *contract.SELECTION_COLUMNS]


def test_connect_holds_each_opened_selection_once(world):
    store = world.store()
    latest = store.silver(world.release_id, "latest")
    store.silver(world.release_id, "latest")  # the same identity again
    older = store.silver(world.release_id, "older")
    con = store.connect()
    counts = dict(con.execute("SELECT selection_id, count(*) FROM silver_selection GROUP BY 1").fetchall())
    assert counts == {latest.selection_id: 6, older.selection_id: 6}
    assert con.execute("SELECT count(*) FROM silver_snapshot").fetchone() == (2,)


def test_a_join_across_silver_tables_restricts_to_the_selection(world):
    store = world.store()
    view = store.silver(world.release_id, "older")
    con = store.connect()
    rows = con.execute(
        f"SELECT b.trade_date, CAST(b.close AS DECIMAL(10, 2)) FROM silver_{BAR} b "
        "JOIN silver_selection s ON s.vintage_id = b.vintage_id AND s.release_id = b.release_id "
        "WHERE s.selection_id = ? AND s.disposition = 'selected' ORDER BY b.trade_date",
        [view.selection_id],
    ).fetchall()
    assert rows == [("2024-01-02", Decimal("10.25")), ("2024-01-03", Decimal("11.25"))]
    assert len(rows) == len(view.selected(BAR))


def test_connect_registers_factor_series_in_long_form(world):
    store = world.store()
    store.factor_series(*EQUITY)
    store.factor_series(*EXCESS)
    store.factor_series(*EQUITY, series_sha256=world.equity_sha)  # again: registered once
    con = store.connect()
    assert _tables(con) == {"factor_series"}
    assert _columns(con, "factor_series") == [
        "factor_id",
        "spec_version",
        "build_id",
        "period_start",
        "period_end",
        "measure",
        "value",
    ]
    assert con.execute("SELECT count(*) FROM factor_series").fetchone() == (3 + 2 * 3,)
    got = con.execute(
        "SELECT value FROM factor_series WHERE factor_id = ? AND measure = 'excess_return' "
        "ORDER BY period_end",
        [EXCESS[0]],
    ).fetchall()
    assert got == [("0.029",), ("0.019",)]
    assert con.execute(
        "SELECT build_id, spec_version FROM factor_series WHERE factor_id = ? LIMIT 1", [EQUITY[0]]
    ).fetchone() == (EQUITY[2], EQUITY[1])


def test_connect_registers_bundles_by_kind_and_table(world):
    store = world.store()
    store.bundle("panel", world.panel_id)
    con = store.connect()
    assert _tables(con) == {f"panel_{t}" for t in gold.TABLES["panel"]}
    store.bundle("portfolio_path", world.portfolio_id)
    con = store.connect()
    opened = ("panel", "portfolio_path")  # the two kinds this test opens; the float kinds have their own
    assert _tables(con) == {f"{k}_{t}" for k in opened for t in gold.TABLES[k]}
    assert con.execute('SELECT "return" FROM panel_fact_panel_return ORDER BY period_end').fetchall() == [
        ("0.010",),
        ("-0.020",),
    ]
    assert con.execute("SELECT wealth_index FROM portfolio_path_fact_portfolio_return").fetchall() == [
        ("1.010",)
    ]


def test_covariance_and_risk_bundles_open_read_floats_and_register(world):
    covariance_id = write_covariance(world.gold_root, world.panel_id)
    risk_id = write_risk(world.gold_root, covariance_id, world.portfolio_id)
    store = world.store()
    covariance = store.bundle("covariance", covariance_id)
    risk = store.bundle("risk_contribution", risk_id)
    assert (covariance.kind, risk.kind) == ("covariance", "risk_contribution")
    assert covariance.recipe["numeric_policy"] == gold.FLOAT_POLICY
    assert risk.recipe["environment"] == ENVIRONMENT
    assert [p["id"] for p in risk.recipe["parents"]] == [covariance_id, world.portfolio_id]
    assert covariance.floats("fact_volatility", "volatility") == [VOLATILITY]  # the written float, exactly
    assert covariance.floats("fact_covariance", "correlation") == [1.0]
    assert risk.floats("fact_portfolio_risk", "portfolio_variance") == [VARIANCE]
    assert risk.floats("fact_risk_contribution", "component_contribution") == [VOLATILITY]
    with pytest.raises(ValueError, match="no column"):
        covariance.floats("fact_volatility", "nope")
    with pytest.raises(ValueError):
        store.bundle("covariance", risk_id)  # the right id under the wrong kind
    con = store.connect()
    wanted = {f"{k}_{t}" for k in ("covariance", "risk_contribution") for t in gold.TABLES[k]}
    assert _tables(con) == wanted
    assert _columns(con, "covariance_fact_covariance") == list(gold.TABLES["covariance"]["fact_covariance"])
    assert con.execute("SELECT window_kind, n_obs FROM covariance_dim_window").fetchall() == [("full", "2")]
    # every cell is text; a float cell reads back as the float that was written
    got = con.execute("SELECT volatility FROM covariance_fact_volatility").fetchone()
    assert got == (repr(VOLATILITY),)
    assert con.execute(
        "SELECT CAST(portfolio_volatility AS DOUBLE) FROM risk_contribution_fact_portfolio_risk"
    ).fetchone() == (VOLATILITY,)
    joined = con.execute(
        "SELECT c.member_code FROM risk_contribution_fact_risk_contribution r "
        "JOIN covariance_fact_volatility c ON c.window_id = r.window_id AND c.member_code = r.member_code"
    ).fetchall()
    assert joined == [("equity",)]


def test_all_four_kinds_register_together(world):
    covariance_id = write_covariance(world.gold_root, world.panel_id)
    risk_id = write_risk(world.gold_root, covariance_id, world.portfolio_id)
    store = world.store()
    for kind, build_id in (
        ("panel", world.panel_id),
        ("portfolio_path", world.portfolio_id),
        ("covariance", covariance_id),
        ("risk_contribution", risk_id),
    ):
        store.bundle(kind, build_id)
    assert _tables(store.connect()) == {f"{k}_{t}" for k in gold.KINDS for t in gold.TABLES[k]}


def test_a_join_across_a_series_and_a_bundle(world):
    store = world.store()
    store.factor_series(*EQUITY)
    store.bundle("panel", world.panel_id)
    con = store.connect()
    rows = con.execute(
        'SELECT f.period_end, f.value, p."return" FROM factor_series f '
        "JOIN panel_fact_panel_return p ON p.period_end = f.period_end "
        "JOIN panel_bridge_panel_member m ON m.member_code = p.member_code AND m.factor_id = f.factor_id "
        "WHERE f.measure = 'total_return' ORDER BY f.period_end"
    ).fetchall()
    assert rows == [("2024-01-03", "0.010", "0.010"), ("2024-01-04", "-0.020", "-0.020")]


def test_everything_opened_is_registered_together(world):
    store = world.store()
    store.silver(world.release_id, "latest")
    store.factor_series(*EQUITY)
    store.bundle("panel", world.panel_id)
    names = _tables(store.connect())
    assert "silver_snapshot" in names
    assert "factor_series" in names
    assert "panel_fact_panel_return" in names
    assert "portfolio_path_fact_portfolio_return" not in names


def test_a_file_changed_after_opening_is_refused_by_connect(world):
    store = world.store()
    store.silver(world.release_id, "latest")
    path = world.silver_root / "v2" / world.release_id / "tables" / "dim_listing.csv"
    path.write_bytes(path.read_bytes().replace(b"XXXX", b"YYYY"))  # a table not read yet
    with pytest.raises(ValueError, match="sha256"):
        store.connect()
    other = world.store()
    other.bundle("panel", world.panel_id)
    bundle_path = world.gold_root / "panel" / world.panel_id / "tables" / "fact_panel_return.csv"
    bundle_path.write_bytes(bundle_path.read_bytes().replace(b"0.010", b"0.011"))
    with pytest.raises(ValueError, match="sha256"):
        other.connect()


def test_each_connect_is_a_fresh_database(world):
    store = world.store()
    first = store.connect()
    store.bundle("panel", world.panel_id)
    second = store.connect()
    assert _tables(first) == set()
    assert "panel_fact_panel_return" in _tables(second)
    second.execute("DELETE FROM panel_fact_panel_return")
    assert store.connect().execute("SELECT count(*) FROM panel_fact_panel_return").fetchone() == (2,)


# -- independence --------------------------------------------------------------------------------------


def test_two_stores_are_independent(world):
    one, two = world.store(), world.store()
    one.bundle("panel", world.panel_id)
    two.factor_series(*EQUITY)
    assert _tables(one.connect()) == {f"panel_{t}" for t in gold.TABLES["panel"]}
    assert _tables(two.connect()) == {"factor_series"}
    two.silver(world.release_id, "older")
    assert not any(n.startswith("silver_") for n in _tables(one.connect()))
    assert "silver_snapshot" in _tables(two.connect())


def test_a_store_with_other_roots_sees_only_its_own(world, tmp_path):
    empty = ResearchStore(tmp_path / "no-silver", tmp_path / "no-factors", tmp_path / "no-gold")
    with pytest.raises(ValueError):
        empty.silver(world.release_id, "latest")
    with pytest.raises(ValueError):
        empty.factor_series(*EQUITY)
    with pytest.raises(ValueError):
        empty.bundle("panel", world.panel_id)
