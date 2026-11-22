"""The verified silver version 2 reader and the version 1 compatibility export (OD-0233).

Built to `docs/decisions/silver-v2-contract.md` (proposed). Section numbers below are that
document's. `open_release` verifies the whole release with `hio.contracts.silver.verify_release`
before it returns anything; a table or selection file is checked against the manifest's sha256 again
when it is read, so a file changed after opening is refused rather than trusted. Every key, table
parse and release read goes through `hio.contracts.silver`: no formula is repeated here.

Where the contract is silent (choices made here):

- `Release.table` returns the cached list itself: callers must not change it.
- `selection_id` takes an id first; a name that is also another selection's id is therefore read as
  the id. A name shared by two selections is refused.
- `FundObservations.corrections` follow the `row_index` order of the excluded rows.
- A selected row whose fact row has another `series_id` or `observation_id` than the selection's
  is refused, as is an excluded row with no matching correction application, a bar with no
  adjusted-close row for the same `source_record_id` (or the reverse), and a repeated `row_index`.
- Every refusal is a `ValueError`; messages hold ids, counts and table names, never a data value.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hio.contracts import silver as contract

CLOSES_FILE = "closes.csv"
DISTRIBUTIONS_FILE = "distributions.csv"
SPLITS_FILE = "splits.csv"
COMPAT_FILES: tuple[str, ...] = (CLOSES_FILE, DISTRIBUTIONS_FILE, SPLITS_FILE)

# §7: the version 1 headers.
CLOSES_HEADER: tuple[str, ...] = ("date", "close", "adjusted_close")
DISTRIBUTIONS_HEADER: tuple[str, ...] = (
    "ex_date",
    "amount",
    "split_adjusted_amount",
    "currency",
    "payment_date",
    "record_date",
    "declaration_date",
    "period",
)
SPLITS_HEADER: tuple[str, ...] = ("date", "ratio")

# Version 1 column -> the fact column it is read from (§7).
_DISTRIBUTION_COLUMNS: tuple[tuple[str, str], ...] = (
    ("ex_date", "ex_date"),
    ("amount", "amount_unadjusted"),
    ("split_adjusted_amount", "amount_split_adjusted"),
    ("currency", "currency"),
    ("payment_date", "payment_date"),
    ("record_date", "record_date"),
    ("declaration_date", "declaration_date"),
    ("period", "period_label"),
)

_BAR = "fact_listing_bar_day"
_ADJUSTED = "fact_vendor_adjusted_close_day"
_DISTRIBUTION = "fact_distribution_event"
_SPLIT = "fact_split_event"

_SHA256 = re.compile(r"[0-9a-f]{64}")
_UNSIGNED = re.compile(r"[0-9]+")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class FundObservations:
    """One member instrument's rows of a selection, with the version 1 column names (§7).

    Rows are in `row_index` order with excluded rows left out. `corrections` describes the
    excluded rows: `{"action", "ex_date", "record_sha256"}`.
    """

    source_symbol: str
    source_id: str
    quote_currency: str
    snapshot_id: str
    snapshot_name: str
    closes: list[dict[str, str]]
    distributions: list[dict[str, str]]
    splits: list[dict[str, str]]
    corrections: list[dict[str, str]]


@dataclass(frozen=True)
class Release:
    """A verified silver version 2 release. Obtain one with `open_release`."""

    core: dict[str, Any]
    release_id: str
    manifest_sha256: str
    directory: Path
    _cache: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    # -- tables and selections ---------------------------------------------------------

    def table(self, name: str) -> list[dict[str, str]]:
        """The rows of a table in file order, parsed on first use and cached.

        The file is checked against the manifest's sha256 when read. Do not change the result.
        """
        key = f"table:{name}"
        if key not in self._cache:
            entry = next((e for e in self.core["tables"] if e["name"] == name), None)
            if entry is None:
                raise ValueError(f"unknown silver table: {name!r}")
            data = _read_file(self.directory / "tables" / f"{name}.csv")
            if _sha256(data) != entry["file_sha256"]:
                raise ValueError(f"table {name}: file sha256 differs from the manifest")
            self._cache[key] = contract.parse_table(name, data)
        return self._cache[key]

    def selections(self) -> list[tuple[str, str]]:
        """`(selection_id, name)` for every selection, in the manifest's order."""
        return [(e["selection_id"], e["name"]) for e in self.core["selections"]]

    def selection_id(self, name_or_id: str) -> str:
        """The id of the selection with this id or name; an unknown or ambiguous name is refused."""
        listed = self.selections()
        for sid, _name in listed:
            if sid == name_or_id:
                return sid
        found = [sid for sid, name in listed if name == name_or_id]
        if not found:
            raise ValueError("unknown selection")
        if len(found) > 1:
            raise ValueError(f"the selection name is ambiguous ({len(found)} selections)")
        return found[0]

    def selection_rows(self, selection_id: str) -> list[dict[str, str]]:
        """The rows of a selection's CSV in file order; an unknown id is refused."""
        entry = self._selection_entry(selection_id)
        key = f"selection:{selection_id}"
        if key not in self._cache:
            data = _read_file(self.directory / "selections" / f"{selection_id}.csv")
            if _sha256(data) != entry["file_sha256"]:
                raise ValueError(f"selection {selection_id}: file sha256 differs from the manifest")
            self._cache[key] = contract.parse_selection(data)
        return self._cache[key]

    def _selection_entry(self, selection_id: str) -> dict[str, Any]:
        for entry in self.core["selections"]:
            if entry["selection_id"] == selection_id:
                return entry
        raise ValueError("unknown selection")

    def _selection_members(self, selection_id: str) -> dict[str, str]:
        """The policy's `{source_symbol: snapshot_id}`, read from the verified policy file."""
        entry = self._selection_entry(selection_id)
        data = _read_file(self.directory / "selections" / f"{selection_id}.json")
        if _sha256(data) != entry["policy_sha256"]:
            raise ValueError(f"selection {selection_id}: policy sha256 differs from the manifest")
        members = json.loads(data)["members"]
        if not isinstance(members, dict):
            raise ValueError(f"selection {selection_id}: members is not a mapping")
        return members

    # -- the fund path -------------------------------------------------------------------

    def fund_observations(self, selection_id: str, source_symbol: str) -> FundObservations:
        """A member instrument's selected rows, with the version 1 column names (§7)."""
        members = self._selection_members(selection_id)
        if source_symbol not in members:
            raise ValueError("the source symbol is not a member of the selection")
        snapshot_id = members[source_symbol]
        snapshot = _only([r for r in self.table("snapshot") if r["snapshot_id"] == snapshot_id], "snapshot")
        mapping = _only(
            [r for r in self.table("source_identity_mapping") if r["source_symbol"] == source_symbol],
            "source_identity_mapping",
        )
        listing = _only(
            [r for r in self.table("dim_listing") if r["listing_sk"] == mapping["listing_sk"]],
            "dim_listing",
        )
        selected = self.selection_rows(selection_id)

        bars = self._series_rows(selected, _BAR, f"{source_symbol}.bar_day")
        adjusted = self._series_rows(selected, _ADJUSTED, f"{source_symbol}.adjusted_close_day")
        distributions = self._series_rows(selected, _DISTRIBUTION, f"{source_symbol}.distribution")
        splits = self._series_rows(selected, _SPLIT, f"{source_symbol}.split")

        adjusted_by_record: dict[str, str] = {}
        for sel, fact in adjusted:
            if sel["disposition"] != "selected":
                raise ValueError("an adjusted close cannot be excluded")
            if sel["source_record_id"] in adjusted_by_record:
                raise ValueError("two adjusted-close rows share a source record")
            adjusted_by_record[sel["source_record_id"]] = fact["adjusted_close"]

        closes: list[dict[str, str]] = []
        for sel, fact in bars:
            if sel["disposition"] != "selected":
                raise ValueError("a bar cannot be excluded")
            record = sel["source_record_id"]
            if record not in adjusted_by_record:
                raise ValueError("a selected bar has no adjusted-close row for its source record")
            closes.append(
                {
                    "date": fact["trade_date"],
                    "close": fact["close"],
                    "adjusted_close": adjusted_by_record.pop(record),
                }
            )
        if adjusted_by_record:
            raise ValueError("an adjusted-close row has no selected bar for its source record")

        kept: list[dict[str, str]] = []
        excluded: list[tuple[dict[str, str], dict[str, str]]] = []
        for sel, fact in distributions:
            if sel["disposition"] == "selected":
                kept.append({column: fact[source] for column, source in _DISTRIBUTION_COLUMNS})
            elif sel["disposition"] == "excluded":
                excluded.append((sel, fact))
            else:
                raise ValueError("a selection row has an unknown disposition")
        for sel, _fact in (*bars, *adjusted, *splits):
            if sel["disposition"] != "selected":
                raise ValueError("only a distribution can be excluded")

        return FundObservations(
            source_symbol=source_symbol,
            source_id=mapping["source_id"],
            quote_currency=listing["quote_currency"],
            snapshot_id=snapshot_id,
            snapshot_name=snapshot["name"],
            closes=closes,
            distributions=kept,
            splits=[{"date": fact["effective_date"], "ratio": fact["ratio"]} for _sel, fact in splits],
            corrections=[self._correction(sel, snapshot_id) for sel, _fact in excluded],
        )

    def _series_rows(
        self, selected: Sequence[Mapping[str, str]], fact_table: str, series_id: str
    ) -> list[tuple[dict[str, str], dict[str, str]]]:
        """The selection rows of one series, each with its fact row, in numeric `row_index` order."""
        rows = [dict(r) for r in selected if r["fact_table"] == fact_table and r["series_id"] == series_id]
        for row in rows:
            if not _UNSIGNED.fullmatch(row["row_index"]):
                raise ValueError("a selection row_index is not an unsigned integer")
        rows.sort(key=lambda r: int(r["row_index"]))
        indexes = [int(r["row_index"]) for r in rows]
        if len(set(indexes)) != len(indexes):
            raise ValueError(f"{fact_table}: a row_index is repeated in the selection")
        facts: dict[str, dict[str, str]] = {}
        for fact in self.table(fact_table):
            facts[fact["vintage_id"]] = fact
        out = []
        for row in rows:
            fact = facts.get(row["vintage_id"])
            if fact is None:
                raise ValueError(f"{fact_table}: a selected vintage_id is not in the fact table")
            if fact["series_id"] != series_id or fact["observation_id"] != row["observation_id"]:
                raise ValueError(f"{fact_table}: a selected row disagrees with its fact row")
            out.append((row, fact))
        return out

    def _correction(self, row: Mapping[str, str], snapshot_id: str) -> dict[str, str]:
        """`{"action", "ex_date", "record_sha256"}` of an excluded selection row."""
        correction_id = row["reason"]
        applications = [
            a
            for a in self.table("fact_correction_application")
            if a["correction_id"] == correction_id
            and a["snapshot_id"] == snapshot_id
            and a["target_source_record_id"] == row["source_record_id"]
        ]
        if len(applications) != 1:
            raise ValueError("an excluded row has no matching correction application")
        rule = _only(
            [r for r in self.table("correction_rule") if r["correction_id"] == correction_id],
            "correction_rule",
        )
        record = _only(
            [r for r in self.table("source_record") if r["source_record_id"] == row["source_record_id"]],
            "source_record",
        )
        return {
            "action": rule["action"],
            "ex_date": rule["ex_date"],
            "record_sha256": record["record_sha256"],
        }

    # -- the version 1 export (§7) -------------------------------------------------------

    def compat_files(self, selection_id: str, source_symbol: str) -> dict[str, bytes]:
        """The bytes of `closes.csv`, `distributions.csv` and `splits.csv` for a member instrument."""
        observed = self.fund_observations(selection_id, source_symbol)
        return {
            CLOSES_FILE: _csv_bytes(CLOSES_HEADER, observed.closes),
            DISTRIBUTIONS_FILE: _csv_bytes(DISTRIBUTIONS_HEADER, observed.distributions),
            SPLITS_FILE: _csv_bytes(SPLITS_HEADER, observed.splits),
        }


def _only(rows: Sequence[dict[str, str]], table: str) -> dict[str, str]:
    if len(rows) != 1:
        raise ValueError(f"{table}: expected exactly one matching row, found {len(rows)}")
    return rows[0]


def _csv_bytes(header: Sequence[str], rows: Sequence[Mapping[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        writer.writerow([row[column] for column in header])
    return buffer.getvalue().encode("utf-8")


def _read_file(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"missing file: {path.parent.name}/{path.name}")
    return path.read_bytes()


def open_release(silver_root: Path | str, release_id: str) -> Release:
    """Verify `<silver_root>/v2/<release_id>/` with `verify_release` and return it.

    Refuses (`ValueError`) a release id that is not a sha256, a missing release, and any release
    `verify_release` refuses (including one whose directory name is not its own id).
    """
    if not isinstance(release_id, str) or not _SHA256.fullmatch(release_id):
        raise ValueError("release_id must be a lower-case sha256")
    directory = Path(silver_root) / "v2" / release_id
    core = contract.verify_release(directory)
    manifest = _read_file(directory / "manifest.json")
    return Release(
        core=core,
        release_id=release_id,
        manifest_sha256=_sha256(manifest),
        directory=directory,
    )
