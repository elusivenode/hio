"""The read API over pinned silver and gold (OD-0233; `docs/decisions/gold-marts-contract.md` §9).

A `ResearchStore` opens things that already exist, by exact identity, and verifies each one before it
returns anything. **Reading never builds and never searches**: there is no method that lists, finds
or picks a release, a build or "the latest". The public surface is exactly four methods:

    store = ResearchStore(silver_root=..., factor_store=..., gold_root=...)
    view = store.silver(release_id, selection)            # selection by name or id
    series = store.factor_series(factor_id, spec_version, build_id, series_sha256=None)
    bundle = store.bundle(kind, build_id)                 # `.table(...)`, `.decimals(...)`, `.floats(...)`
    con = store.connect()                                 # an in-memory DuckDB of everything opened

A method whose root was not given refuses (`ValueError`). Every refusal is a `ValueError`.

`connect()` registers, in a fresh in-memory database, one table for everything opened so far through
this store. **Every column is `VARCHAR`**, because every cell in silver and gold is text and nothing is
rounded: do numeric work with `CAST(col AS DECIMAL(38, 18))` (or `DOUBLE` where a float is acceptable)
in SQL, or read a column as `Decimal` with `Bundle.decimals` (as `float` with `Bundle.floats` for the
`covariance` and `risk_contribution` kinds, whose cells are float text). A column named `return` or `schema`
needs double quotes in SQL.

- `silver_<table>`: each table of each opened release, with a leading `release_id` column.
- `silver_selection`: the rows of each opened selection, as `release_id, selection_id`, then the
  selection columns.
- `factor_series`: each opened series in long form, as `factor_id, spec_version, build_id,
  period_start, period_end, measure, value`.
- `<kind>_<table>`: each table of each opened bundle of that kind (`panel_fact_panel_return`, ...);
  the rows carry their own build id.

A table exists only once something of its group has been opened; opening nothing gives an empty
database. Opening the same identity twice registers it once. Two stores share nothing.

Where the contract is silent (choices made here):

- `SilverView.table` and `.selected` return fresh dicts, so a caller cannot change what the release
  caches. `.selected(fact_table)` keeps the fact table's file order, and refuses a name that is not one
  of the four measurement facts.
- A release is registered for `connect()` only after its selection also resolved; a refusal registers
  nothing.
- `silver_selection` has one row per selection row, whatever its disposition.
- A bundle's tables are read (and so re-verified against the manifest) when `connect()` runs.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import duckdb

from hio.contracts import gold, silver
from hio.contracts.gold import Bundle, FactorSeries, open_bundle, read_factor_series
from hio.marketdata.silver_reader import FundObservations, Release, open_release

_CHUNK = 200
_LEADING = ("period_start", "period_end")
_FACTOR_SERIES_COLUMNS = (
    "factor_id",
    "spec_version",
    "build_id",
    "period_start",
    "period_end",
    "measure",
    "value",
)


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _create(con: duckdb.DuckDBPyConnection, table: str, columns: Sequence[str]) -> None:
    listed = ", ".join(f"{_quote(c)} VARCHAR" for c in columns)
    con.execute(f"CREATE TABLE {_quote(table)} ({listed})")


def _insert(con: duckdb.DuckDBPyConnection, table: str, rows: list[tuple[str, ...]]) -> None:
    if not rows:
        return
    marks = "(" + ",".join(["?"] * len(rows[0])) + ")"
    for start in range(0, len(rows), _CHUNK):
        chunk = rows[start : start + _CHUNK]
        con.execute(
            f"INSERT INTO {_quote(table)} VALUES " + ",".join([marks] * len(chunk)),
            [cell for row in chunk for cell in row],
        )


class SilverView:
    """A verified silver release and one of its selections (§9). Obtain one with `ResearchStore.silver`."""

    def __init__(self, release: Release, selection_id: str) -> None:
        self._release = release
        self.release_id: str = release.release_id
        self.selection_id: str = selection_id

    def table(self, name: str) -> list[dict[str, str]]:
        """The rows of a silver table in file order, as dicts of text; an unknown table is refused.
        The file is checked against the manifest when it is first read."""
        return [dict(row) for row in self._release.table(name)]

    def fund_observations(self, source_symbol: str) -> FundObservations:
        """A member instrument's selected rows with the version 1 column names; the instrument
        must be a member of this selection."""
        return self._release.fund_observations(self.selection_id, source_symbol)

    def selected(self, fact_table: str) -> list[dict[str, str]]:
        """The rows of a fact table whose vintage the selection marks `selected`, in file order.

        A vintage the selection excludes, and a vintage the selection does not name (such as the
        older value of a revised observation), is absent.
        """
        if fact_table not in silver.FACT_TABLES:
            raise ValueError(f"not a silver fact table: {fact_table!r}")
        chosen = {
            row["vintage_id"]
            for row in self._release.selection_rows(self.selection_id)
            if row["fact_table"] == fact_table and row["disposition"] == "selected"
        }
        return [dict(row) for row in self._release.table(fact_table) if row["vintage_id"] in chosen]


class ResearchStore:
    """Opens pinned silver, factor series and gold bundles, and nothing else (§9)."""

    def __init__(
        self,
        silver_root: Path | str | None = None,
        factor_store: Path | str | None = None,
        gold_root: Path | str | None = None,
    ) -> None:
        self._silver_root = None if silver_root is None else Path(silver_root)
        self._factor_store = None if factor_store is None else Path(factor_store)
        self._gold_root = None if gold_root is None else Path(gold_root)
        self._releases: dict[str, Release] = {}
        self._selections: dict[tuple[str, str], None] = {}
        self._series: dict[tuple[str, str, str], FactorSeries] = {}
        self._bundles: dict[tuple[str, str], Bundle] = {}

    def silver(self, release_id: str, selection: str) -> SilverView:
        """Verify silver release `release_id` and resolve `selection` (a name or an id) in it."""
        if self._silver_root is None:
            raise ValueError("this store was given no silver_root")
        release = open_release(self._silver_root, release_id)
        selection_id = release.selection_id(selection)
        release.selection_rows(selection_id)  # reads the selection file, checked against the manifest
        self._releases.setdefault(release.release_id, release)
        self._selections[(release.release_id, selection_id)] = None
        return SilverView(self._releases[release.release_id], selection_id)

    def factor_series(
        self,
        factor_id: str,
        spec_version: str,
        build_id: str,
        *,
        series_sha256: str | None = None,
    ) -> FactorSeries:
        """Read and verify one factor build (`read_factor_series`); `series_sha256`, when given, pins
        the series bytes and a different one is refused."""
        if self._factor_store is None:
            raise ValueError("this store was given no factor_store")
        series = read_factor_series(
            self._factor_store, factor_id, spec_version, build_id, series_sha256=series_sha256
        )
        self._series[(factor_id, spec_version, build_id)] = series
        return series

    def bundle(self, kind: str, build_id: str) -> Bundle:
        """Verify and open gold bundle `build_id` of `kind` (`open_bundle`); a full 64-hex id only."""
        if self._gold_root is None:
            raise ValueError("this store was given no gold_root")
        opened = open_bundle(self._gold_root, kind, build_id)
        self._bundles[(opened.kind, opened.build_id)] = opened
        return opened

    def connect(self) -> duckdb.DuckDBPyConnection:
        """A new in-memory DuckDB holding one VARCHAR table for everything opened so far.

        See the module docstring for the table names. Cast in SQL for numeric work. The caller owns
        the connection; calling again builds another, with whatever has been opened by then.
        """
        con = duckdb.connect(":memory:")
        try:
            self._register_silver(con)
            self._register_series(con)
            self._register_bundles(con)
        except BaseException:
            con.close()
            raise
        return con

    def _register_silver(self, con: duckdb.DuckDBPyConnection) -> None:
        if not self._releases:
            return
        for name, columns in silver.TABLES.items():
            table = f"silver_{name}"
            _create(con, table, ("release_id", *columns))
            rows = [
                (release_id, *(row[c] for c in columns))
                for release_id, release in self._releases.items()
                for row in release.table(name)
            ]
            _insert(con, table, rows)
        _create(con, "silver_selection", ("release_id", "selection_id", *silver.SELECTION_COLUMNS))
        _insert(
            con,
            "silver_selection",
            [
                (release_id, selection_id, *(row[c] for c in silver.SELECTION_COLUMNS))
                for release_id, selection_id in self._selections
                for row in self._releases[release_id].selection_rows(selection_id)
            ],
        )

    def _register_series(self, con: duckdb.DuckDBPyConnection) -> None:
        if not self._series:
            return
        _create(con, "factor_series", _FACTOR_SERIES_COLUMNS)
        rows: list[tuple[str, ...]] = []
        for series in self._series.values():
            measures = [c for c in series.columns if c not in _LEADING]
            for row in series.rows:
                for measure in measures:
                    rows.append(
                        (
                            series.factor_id,
                            series.spec_version,
                            series.build_id,
                            row["period_start"],
                            row["period_end"],
                            measure,
                            row[measure],
                        )
                    )
        _insert(con, "factor_series", rows)

    def _register_bundles(self, con: duckdb.DuckDBPyConnection) -> None:
        kinds = [kind for kind in gold.KINDS if any(k == kind for k, _ in self._bundles)]
        for kind in kinds:
            for name, columns in gold.TABLES[kind].items():
                table = f"{kind}_{name}"
                _create(con, table, columns)
                rows: list[tuple[str, ...]] = []
                for (bundle_kind, _build_id), opened in self._bundles.items():
                    if bundle_kind == kind:
                        rows.extend(tuple(row[c] for c in columns) for row in opened.table(name))
                _insert(con, table, rows)


__all__ = ["ResearchStore", "SilverView"]
