"""Silver version 2: bronze snapshots to a dimensional release (OD-0233).

Built to `docs/decisions/silver-v2-contract.md` (proposed). Section numbers in the docstrings are that
document's. This module reads a release spec, the instrument register, one observation spec for each
instrument and the pinned bronze snapshots, and writes one release under `<silver_root>/v2/<release_id>/`
through `hio.contracts.silver`: every key, every table's bytes and the release write come from that module.

Nothing here reads a clock, the environment or git: the code commit is a parameter. Bronze is only read.
Messages of refusals name symbols, snapshots and counts, never a date, a price or an amount from the data.

Where the contract is silent (choices made here):

- A snapshot manifest that names a `source_id` must equal the release's; one that records a `stopped`
  value is refused (a partial snapshot). A manifest's `retrieved_at` values must be timezone-aware ISO
  instants; capture order must be strictly ascending by the earliest of them. `snapshot.first_retrieved_at`
  and `last_retrieved_at` are the earliest and latest over every file the manifest lists.
- Only the files of the release's instruments and their exchange lists are read, and only those are
  verified against the manifest. Two entries for one (symbol, kind) in a manifest are refused.
- An exchange-list entry is the one whose `Code` equals the part of the source symbol before its last dot;
  two such entries in one list are refused. Its `Currency` must equal the listing's quote currency in
  every snapshot where it is present.
- Dates that are coordinates (`date` of eod, distribution and split records) must be ISO dates; a
  distribution's declaration, record and payment dates may be empty, else must be ISO dates.
- A split ratio that is not `<new>/<old>` gives empty `new_units` and `old_units`.
- Every instrument gets the four series of §4 in `dim_series`, whether or not facts exist; `dim_instrument`
  and `dim_listing` hold the release's instruments and all their register listings; `dim_date` and
  `dim_currency` hold what facts, listings and the vendor's listing rows refer to, plus the sentinel.
  Date parts are unpadded integers as text. `attributes_sha256` covers every column except the key's
  surrogate and durable-key columns.
- A selection may name only some of the release's instruments.
"""

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

from hio.contracts import silver as s
from hio.contracts.canonical import canonical_json, sha256_hex
from hio.reference.instruments import Listing, load_register

REPO_ROOT = Path(__file__).resolve().parents[3]

KINDS = ("eod", "div", "splits")
CORRECTION_ACTION = "exclude_distribution"  # the only action (OD-0230, OD-0231)

BAR = "fact_listing_bar_day"
ADJUSTED = "fact_vendor_adjusted_close_day"
DISTRIBUTION = "fact_distribution_event"
SPLIT = "fact_split_event"
_QUANTITY = {BAR: "bar_day", ADJUSTED: "adjusted_close_day", DISTRIBUTION: "distribution", SPLIT: "split"}
_FACTS_OF_KIND = {"eod": (BAR, ADJUSTED), "div": (DISTRIBUTION,), "splits": (SPLIT,)}

_RELEASE_KEYS = frozenset({"identity", "schema", "source_id", "snapshots", "instruments", "selections"})
_RELEASE_IDENTITY_KEYS = frozenset({"release_name", "version", "status"})
_SNAPSHOT_KEYS = frozenset({"name", "manifest_sha256"})
_SELECTION_KEYS = frozenset({"name", "members"})
_OBSERVATION_KEYS = frozenset({"identity", "source", "corrections", "changelog"})
_OBSERVATION_IDENTITY_KEYS = frozenset({"instrument", "version", "status"})
_OBSERVATION_SOURCE_KEYS = frozenset({"source_id", "quote_currency"})
_CORRECTION_KEYS = frozenset({"action", "ex_date", "reason", "evidence"})
_SYMBOL = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*(\.[A-Za-z0-9_-]+)+")
_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")
_HEX = re.compile(r"[0-9a-f]{64}")
_SENTINEL = {"sentinel": "not_recorded"}

# Vendor field -> column, for each kind of record (§4).
_BAR_MEASURES = ("open", "high", "low", "close", "volume")
_DISTRIBUTION_FIELDS = (
    ("declaration_date", "declarationDate"),
    ("record_date", "recordDate"),
    ("payment_date", "paymentDate"),
    ("amount_unadjusted", "unadjustedValue"),
    ("amount_split_adjusted", "value"),
    ("currency", "currency"),
    ("period_label", "period"),
    ("franking", "franking"),
)
_LISTING_FIELDS = (
    ("vendor_code", "Code"),
    ("name", "Name"),
    ("country", "Country"),
    ("exchange", "Exchange"),
    ("currency", "Currency"),
    ("isin", "Isin"),
    ("type", "Type"),
)


# --------------------------------------------------------------------------------------
# Small checks
# --------------------------------------------------------------------------------------


def _is_iso_date(value: object) -> bool:
    try:
        return isinstance(value, str) and date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _exact_keys(obj: object, keys: frozenset[str], where: str) -> dict[str, Any]:
    if not isinstance(obj, dict) or set(obj) != keys:
        raise ValueError(f"{where} must have exactly the keys {', '.join(sorted(keys))}")
    return obj


def _load_yaml(path: Path, what: str) -> tuple[Any, bytes]:
    try:
        raw = Path(path).read_bytes()
    except OSError:
        raise ValueError(f"the {what} cannot be read") from None
    try:
        return yaml.safe_load(raw), raw
    except (yaml.YAMLError, ValueError):
        raise ValueError(f"the {what} is not valid YAML") from None


def check_output_path(path: Path, repo_root: Path = REPO_ROOT) -> Path:
    """§6: refuse (`ValueError`) a path inside the repository; return it resolved."""
    resolved = Path(path).resolve()
    root = Path(repo_root).resolve()
    if resolved == root or root in resolved.parents:
        raise ValueError("the silver root must lie outside the repository")
    return resolved


# --------------------------------------------------------------------------------------
# Specs (§3)
# --------------------------------------------------------------------------------------


def read_release_spec(path: Path) -> dict[str, Any]:
    """§3: the fields of a release spec, validated, with the file's sha256. Refuses with `ValueError`.

    Returns `release_name`, `version`, `status`, `schema`, `source_id`, `snapshots` (a list of
    `{name, manifest_sha256}` in the order written), `instruments` (source symbols), `selections` (a list
    of `{name, members}`) and `sha256`.
    """
    doc, raw = _load_yaml(path, "release spec")
    spec = _exact_keys(doc, _RELEASE_KEYS, "the release spec")
    identity = _exact_keys(spec["identity"], _RELEASE_IDENTITY_KEYS, "identity")
    for key in sorted(_RELEASE_IDENTITY_KEYS):
        if not _nonempty(identity[key]):
            raise ValueError(f"identity.{key} must be a non-empty string")
    if spec["schema"] != s.SCHEMA:
        raise ValueError(f"schema must be {s.SCHEMA}")
    if not _nonempty(spec["source_id"]):
        raise ValueError("source_id must be a non-empty string")

    snapshots = spec["snapshots"]
    if not isinstance(snapshots, list) or not snapshots:
        raise ValueError("snapshots must be a non-empty list")
    names: list[str] = []
    for item in snapshots:
        entry = _exact_keys(item, _SNAPSHOT_KEYS, "each snapshot")
        if not isinstance(entry["name"], str) or not _NAME.fullmatch(entry["name"]):
            raise ValueError("a snapshot name must be letters, digits, hyphens or underscores")
        if not isinstance(entry["manifest_sha256"], str) or not _HEX.fullmatch(entry["manifest_sha256"]):
            raise ValueError("a snapshot manifest_sha256 must be 64 lower-case hex characters")
        names.append(entry["name"])
    if len(set(names)) != len(names):
        raise ValueError("snapshot names must be unique")
    if len({e["manifest_sha256"] for e in snapshots}) != len(snapshots):
        raise ValueError("two snapshots share a manifest_sha256")

    instruments = spec["instruments"]
    if not isinstance(instruments, list) or not instruments:
        raise ValueError("instruments must be a non-empty list")
    for symbol in instruments:
        if not isinstance(symbol, str) or not _SYMBOL.fullmatch(symbol) or ".." in symbol:
            raise ValueError("an instrument must be a source symbol <SYMBOL>.<EXCHANGE>")
    if len(set(instruments)) != len(instruments):
        raise ValueError("instruments must be unique")

    selections = spec["selections"]
    if not isinstance(selections, list):
        raise ValueError("selections must be a list")
    selection_names: list[str] = []
    for item in selections:
        entry = _exact_keys(item, _SELECTION_KEYS, "each selection")
        if not _nonempty(entry["name"]):
            raise ValueError("a selection name must be a non-empty string")
        members = entry["members"]
        if not isinstance(members, dict) or not members:
            raise ValueError("a selection's members must be a non-empty mapping")
        for symbol, snapshot in members.items():
            if symbol not in instruments:
                raise ValueError(f"selection {entry['name']}: member {symbol} is not a release instrument")
            if snapshot not in names:
                raise ValueError(f"selection {entry['name']}: member {symbol} names an unknown snapshot")
        selection_names.append(entry["name"])
    if len(set(selection_names)) != len(selection_names):
        raise ValueError("selection names must be unique")

    return {
        "release_name": identity["release_name"],
        "version": identity["version"],
        "status": identity["status"],
        "schema": spec["schema"],
        "source_id": spec["source_id"],
        "snapshots": [{"name": e["name"], "manifest_sha256": e["manifest_sha256"]} for e in snapshots],
        "instruments": list(instruments),
        "selections": [{"name": e["name"], "members": dict(e["members"])} for e in selections],
        "sha256": sha256_hex(raw),
    }


def read_observation_spec(path: Path) -> dict[str, Any]:
    """§3: the fields of an observation spec (version 1 format), validated, with the file's sha256.

    Returns `instrument`, `version`, `status`, `source_id`, `quote_currency`, `corrections` (each with
    `action`, `ex_date`, `reason`, `evidence`), `changelog` and `sha256`. Refuses with `ValueError`.
    """
    doc, raw = _load_yaml(path, "observation spec")
    spec = _exact_keys(doc, _OBSERVATION_KEYS, "the observation spec")
    identity = _exact_keys(spec["identity"], _OBSERVATION_IDENTITY_KEYS, "identity")
    source = _exact_keys(spec["source"], _OBSERVATION_SOURCE_KEYS, "source")
    for owner, keys in ((identity, _OBSERVATION_IDENTITY_KEYS), (source, _OBSERVATION_SOURCE_KEYS)):
        for key in sorted(keys):
            if not _nonempty(owner[key]):
                raise ValueError(f"{key} must be a non-empty string")
    instrument = identity["instrument"]
    if not _SYMBOL.fullmatch(instrument) or ".." in instrument:
        raise ValueError("instrument must be <SYMBOL>.<EXCHANGE> and a safe file name")
    changelog = spec["changelog"]
    if not isinstance(changelog, list) or not all(isinstance(line, str) for line in changelog):
        raise ValueError("changelog must be a list of strings")
    corrections = spec["corrections"]
    if not isinstance(corrections, list):
        raise ValueError("corrections must be a list")
    seen: set[str] = set()
    for item in corrections:
        correction = _exact_keys(item, _CORRECTION_KEYS, "each correction")
        if correction["action"] != CORRECTION_ACTION:
            raise ValueError(f"a correction's action must be {CORRECTION_ACTION}")
        if not _is_iso_date(correction["ex_date"]):
            raise ValueError("a correction's ex_date must be an ISO date string")
        for key in ("reason", "evidence"):
            if not _nonempty(correction[key]):
                raise ValueError(f"a correction's {key} must be a non-empty string")
        if correction["ex_date"] in seen:
            raise ValueError("two corrections share an ex_date")
        seen.add(correction["ex_date"])
    return {
        "instrument": instrument,
        "version": identity["version"],
        "status": identity["status"],
        "source_id": source["source_id"],
        "quote_currency": source["quote_currency"],
        "corrections": [dict(c) for c in corrections],
        "changelog": list(changelog),
        "sha256": sha256_hex(raw),
    }


# --------------------------------------------------------------------------------------
# Bronze (§3)
# --------------------------------------------------------------------------------------


def _instant(text: object) -> datetime:
    if not isinstance(text, str):
        raise ValueError("a retrieved_at must be an ISO instant")
    try:
        value = datetime.fromisoformat(text)
    except ValueError:
        raise ValueError("a retrieved_at must be an ISO instant") from None
    if value.tzinfo is None:
        raise ValueError("a retrieved_at must carry a time zone")
    return value


@dataclass
class _Snapshot:
    name: str
    snapshot_id: str
    order: int
    first: str
    last: str
    files: dict[tuple[str, str], dict[str, str]]  # (symbol, kind) -> manifest entry, relevant files only


class _Bronze:
    """Reads and verifies the pinned snapshots; never writes."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.parsed: dict[str, Any] = {}  # file sha256 -> parsed JSON

    def _read(self, relative: object) -> bytes:
        if not isinstance(relative, str) or not relative:
            raise ValueError("a manifest path must be text")
        rel = Path(relative)
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("a manifest path must stay inside the bronze root")
        resolved = (self.root / rel).resolve()
        if self.root not in resolved.parents:
            raise ValueError("a manifest path must stay inside the bronze root")
        if not resolved.is_file():
            raise ValueError("a bronze file named by a manifest is missing")
        return resolved.read_bytes()

    def load(
        self, pins: list[dict[str, str]], source_id: str, symbols: list[str], exchanges: set[str]
    ) -> list[_Snapshot]:
        snapshots: list[_Snapshot] = []
        earliest: list[datetime] = []
        for order, pin in enumerate(pins, start=1):
            name = pin["name"]
            manifest_path = self.root / "raw" / name / "manifest.json"
            if not manifest_path.resolve().is_file() or self.root not in manifest_path.resolve().parents:
                raise ValueError(f"snapshot {name}: manifest.json is missing")
            data = manifest_path.resolve().read_bytes()
            if sha256_hex(data) != pin["manifest_sha256"]:
                raise ValueError(f"snapshot {name}: the manifest does not match its pin")
            try:
                manifest = s.load_json_exact(data)
            except ValueError:
                raise ValueError(f"snapshot {name}: the manifest is not JSON") from None
            snapshots.append(
                self._snapshot(name, pin["manifest_sha256"], order, manifest, source_id, symbols, exchanges)
            )
            earliest.append(_instant(snapshots[-1].first))
        for before, after in itertools.pairwise(earliest):
            if not before < after:
                raise ValueError("snapshots are not in ascending capture order")
        return snapshots

    def _snapshot(
        self,
        name: str,
        snapshot_id: str,
        order: int,
        manifest: Any,
        source_id: str,
        symbols: list[str],
        exchanges: set[str],
    ) -> _Snapshot:
        if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
            raise ValueError(f"snapshot {name}: the manifest must hold a files list")
        if manifest.get("stopped") is not None:
            raise ValueError(f"snapshot {name}: the snapshot stopped early")
        if "source_id" in manifest and manifest["source_id"] != source_id:
            raise ValueError(f"snapshot {name}: the manifest's source_id differs from the release's")
        wanted = {(symbol, kind) for symbol in symbols for kind in KINDS}
        wanted |= {(exchange, "symbols") for exchange in exchanges}
        instants: list[tuple[datetime, str]] = []
        files: dict[tuple[str, str], dict[str, str]] = {}
        for entry in manifest["files"]:
            if not isinstance(entry, dict):
                raise ValueError(f"snapshot {name}: a file entry must be a mapping")
            for key in ("path", "sha256", "kind", "symbol", "retrieved_at"):
                if not isinstance(entry.get(key), str):
                    raise ValueError(f"snapshot {name}: a file entry lacks {key}")
            instants.append((_instant(entry["retrieved_at"]), entry["retrieved_at"]))
            key = (entry["symbol"], entry["kind"])
            if key not in wanted:
                continue
            if key in files:
                raise ValueError(f"snapshot {name}: two entries for one symbol and kind")
            if not _HEX.fullmatch(entry["sha256"]):
                raise ValueError(f"snapshot {name}: a file entry's sha256 is not a lower-case sha256")
            files[key] = {k: entry[k] for k in ("path", "sha256", "kind", "symbol", "retrieved_at")}
        if not instants:
            raise ValueError(f"snapshot {name}: the manifest lists no files")
        for entry in files.values():
            data = self._read(entry["path"])
            if sha256_hex(data) != entry["sha256"]:
                raise ValueError(f"snapshot {name}: a file does not match its manifest entry")
            if entry["sha256"] not in self.parsed:
                try:
                    self.parsed[entry["sha256"]] = s.load_json_exact(data)
                except ValueError:
                    raise ValueError(f"snapshot {name}: a bronze file is not JSON") from None
        return _Snapshot(
            name=name,
            snapshot_id=snapshot_id,
            order=order,
            first=min(instants, key=lambda pair: pair[0])[1],
            last=max(instants, key=lambda pair: pair[0])[1],
            files=files,
        )


# --------------------------------------------------------------------------------------
# Records
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class _Rec:
    index: int
    record: dict[str, Any]
    sha: str
    record_id: str


def _records(parsed: Any, file_sha: str, what: str) -> list[_Rec]:
    if not isinstance(parsed, list) or not all(isinstance(r, dict) for r in parsed):
        raise ValueError(f"{what}: a file must be a list of records")
    return [
        _Rec(i, record, s.record_sha256(record), s.source_record_id(file_sha, i))
        for i, record in enumerate(parsed)
    ]


def _cell(record: dict[str, Any], key: str) -> str:
    try:
        return s.exact_text(record.get(key))
    except (TypeError, ValueError):
        raise ValueError(f"a vendor field {key} is neither a finite number, a string nor null") from None


def _occurrences(records: list[_Rec], what: str) -> dict[int, int]:
    """§4: the 0-based position of a record among the file's records of the same date, by sha."""
    by_date: dict[str, list[_Rec]] = {}
    for rec in records:
        day = rec.record.get("date")
        if not _is_iso_date(day):
            raise ValueError(f"{what}: every record needs an ISO date")
        by_date.setdefault(day, []).append(rec)
    out: dict[int, int] = {}
    for group in by_date.values():
        for position, rec in enumerate(sorted(group, key=lambda r: (r.sha, r.index))):
            out[rec.index] = position
    return out


def _check_eod(records: list[_Rec], what: str) -> None:
    previous: str | None = None
    for rec in records:
        day = rec.record.get("date")
        if not _is_iso_date(day):
            raise ValueError(f"{what}: every record needs an ISO date")
        if previous is not None and day <= previous:
            raise ValueError(f"{what}: eod dates must be unique and ascending")
        previous = day
        close = rec.record.get("close")
        if not isinstance(close, Decimal) or not close.is_finite() or close <= 0:
            raise ValueError(f"{what}: a close must be a positive number")


def _positive(record: dict[str, Any]) -> bool:
    raw = record.get("unadjustedValue")
    if raw is None:
        return False
    try:
        return Decimal(str(raw)) > 0
    except ArithmeticError:
        return False


# --------------------------------------------------------------------------------------
# Facts: vintages (§4)
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class _Item:
    coordinate: dict[str, str | int]
    measures: dict[str, str]
    record_id: str
    extra: dict[str, str]


@dataclass
class _Out:
    facts: dict[str, list[dict[str, str]]] = field(default_factory=lambda: {t: [] for t in _QUANTITY})
    bridge: list[dict[str, str]] = field(default_factory=list)
    # (fact table, source_record_id, snapshot_id) -> (vintage_id, observation_id)
    support: dict[tuple[str, str, str], tuple[str, str]] = field(default_factory=dict)


def _run_series(
    out: _Out,
    fact: str,
    series_id: str,
    common: dict[str, str],
    steps: list[tuple[_Snapshot, str, list[_Item]]],
) -> None:
    """§4 "Vintages": walk the snapshots in capture order; a record equal in value to the newest vintage
    of its observation supports it, any other starts a new vintage anchored at this snapshot."""
    newest: dict[str, tuple[str, str]] = {}
    for snapshot, captured, items in steps:
        for item in items:
            obs = s.observation_id(series_id, item.coordinate)
            fingerprint = s.value_fingerprint(item.measures)
            current = newest.get(obs)
            if current is not None and current[1] == fingerprint:
                vid = current[0]
            else:
                vid = s.vintage_id(obs, fingerprint, snapshot.snapshot_id)
                newest[obs] = (vid, fingerprint)
                out.facts[fact].append(
                    {
                        **common,
                        "vintage_id": vid,
                        "observation_id": obs,
                        "series_id": series_id,
                        "origin_source_record_id": item.record_id,
                        "anchor_snapshot_id": snapshot.snapshot_id,
                        "first_captured_at": captured,
                        **item.extra,
                        **item.measures,
                    }
                )
            out.bridge.append(
                {"vintage_id": vid, "source_record_id": item.record_id, "snapshot_id": snapshot.snapshot_id}
            )
            out.support[(fact, item.record_id, snapshot.snapshot_id)] = (vid, obs)


@dataclass
class _Ctx:
    """Dimension keys and the dates and currencies the rows refer to."""

    dates: set[str] = field(default_factory=set)
    currencies: set[str] = field(default_factory=set)

    def date_sk(self, day: str) -> str:
        if not day:
            return s.sk("date", _SENTINEL)
        self.dates.add(day)
        return s.sk("date", {"date": day})

    def currency_sk(self, code: str) -> str:
        if not code:
            return s.sk("currency", _SENTINEL)
        self.currencies.add(code)
        return s.sk("currency", {"code": code})


def _optional_date(record: dict[str, Any], key: str) -> str:
    text = _cell(record, key)
    if text and not _is_iso_date(text):
        raise ValueError(f"a vendor field {key} must be empty or an ISO date")
    return text


# --------------------------------------------------------------------------------------
# The build (§3 to §6)
# --------------------------------------------------------------------------------------


def build_release(
    spec_path: Path,
    register_path: Path,
    observations_dir: Path,
    bronze_root: Path,
    silver_root: Path,
    *,
    commit: str,
) -> tuple[Path, dict[str, Any], bool]:
    """Build the release the spec names and write it under `<silver_root>/v2/<release_id>/`.

    Returns `(release_dir, core, existed)`; `existed` is true when the identical release was already
    there. `commit` is the code commit, given by the caller. Refuses with `ValueError` on every §6
    refusal. Bronze is read only.
    """
    check_output_path(silver_root)
    if not isinstance(commit, str) or not commit.strip():
        raise ValueError("the code commit must be a non-empty string")
    spec = read_release_spec(Path(spec_path))
    register = load_register(Path(register_path))
    source_id = spec["source_id"]
    symbols = sorted(spec["instruments"])

    # Identity: the register mapping and the observation spec of every instrument.
    resolved: dict[str, tuple[Any, Listing]] = {}
    observation: dict[str, dict[str, Any]] = {}
    for symbol in symbols:
        resolved[symbol] = register.resolve(source_id, symbol)
        path = Path(observations_dir) / f"{symbol}.yaml"
        if not path.is_file():
            raise ValueError(f"{symbol}: no observation spec")
        ospec = read_observation_spec(path)
        if ospec["instrument"] != symbol:
            raise ValueError(f"{symbol}: the observation spec names another instrument")
        if ospec["source_id"] != source_id:
            raise ValueError(f"{symbol}: the observation spec's source_id differs from the release's")
        if ospec["quote_currency"] != resolved[symbol][1].quote_currency:
            raise ValueError(f"{symbol}: the observation spec's quote currency differs from the listing's")
        observation[symbol] = ospec

    exchange_symbol = {symbol: "EXCHANGE." + symbol.rsplit(".", 1)[1] for symbol in symbols}
    bronze = _Bronze(Path(bronze_root))
    snapshots = bronze.load(spec["snapshots"], source_id, symbols, set(exchange_symbol.values()))
    capture_order = {snap.snapshot_id: snap.order for snap in snapshots}
    snapshot_by_name = {snap.name: snap for snap in snapshots}

    # Keys shared by every row.
    spec_hashes = sorted(observation[symbol]["sha256"] for symbol in symbols)
    audit = {
        "schema": s.SCHEMA,
        "code_commit": commit,
        "release_spec_sha256": spec["sha256"],
        "register_sha256": register.sha256,
        "observation_specs_sha256": sha256_hex(canonical_json(spec_hashes)),
    }
    audit_sk = s.sk("audit", audit)
    source_sk = s.sk("source", {"source_id": source_id})
    ctx = _Ctx()
    out = _Out()
    tables: dict[str, list[dict[str, str]]] = {name: [] for name in s.TABLES}

    # Dimensions that come from the register.
    instrument_rows: dict[str, dict[str, str]] = {}
    listing_rows: dict[str, dict[str, str]] = {}
    for symbol in symbols:
        instrument, listing = resolved[symbol]
        code = instrument.instrument_code
        if code not in instrument_rows:
            attributes = {
                "name": instrument.name,
                "issuer_code": instrument.issuer_code,
                "vehicle_type": instrument.vehicle_type,
                "domicile": instrument.domicile,
            }
            instrument_rows[code] = {
                "instrument_sk": s.sk(
                    "instrument",
                    {"instrument_code": code},
                    {"attributes_sha256": s.attributes_sha256(attributes)},
                ),
                "instrument_code": code,
                **attributes,
            }
            for each in instrument.listings:
                ctx.currency_sk(each.quote_currency)
                key = _listing_sk(code, each)
                listing_rows[key] = {
                    "listing_sk": key,
                    "instrument_code": code,
                    "instrument_sk": instrument_rows[code]["instrument_sk"],
                    "mic": each.mic,
                    "ticker": each.ticker,
                    "valid_from": each.valid_from,
                    "quote_currency": each.quote_currency,
                }
    tables["dim_instrument"] = list(instrument_rows.values())
    tables["dim_listing"] = list(listing_rows.values())
    tables["dim_source"] = [{"source_sk": source_sk, "source_id": source_id}]
    tables["dim_audit"] = [{"audit_sk": audit_sk, **audit}]
    for symbol in symbols:
        instrument, listing = resolved[symbol]
        tables["source_identity_mapping"].append(
            {
                "source_id": source_id,
                "source_symbol": symbol,
                "instrument_code": instrument.instrument_code,
                "listing_sk": _listing_sk(instrument.instrument_code, listing),
            }
        )
        for quantity in _QUANTITY.values():
            series_id = f"{symbol}.{quantity}"
            tables["dim_series"].append(
                {
                    "series_sk": s.sk("series", {"series_id": series_id}, {"definition": "1"}),
                    "series_id": series_id,
                    "source_id": source_id,
                    "source_symbol": symbol,
                    "quantity": quantity,
                }
            )

    # Provenance: snapshots and their members.
    for snap in snapshots:
        tables["snapshot"].append(
            {
                "snapshot_id": snap.snapshot_id,
                "name": snap.name,
                "source_id": source_id,
                "capture_order": str(snap.order),
                "first_retrieved_at": snap.first,
                "last_retrieved_at": snap.last,
            }
        )
        for entry in snap.files.values():
            tables["snapshot_member"].append(
                {
                    "snapshot_id": snap.snapshot_id,
                    "path": entry["path"],
                    "file_sha256": entry["sha256"],
                    "kind": entry["kind"],
                    "source_symbol": entry["symbol"],
                    "retrieved_at": entry["retrieved_at"],
                }
            )

    # Records of every file, once each.
    source_records: dict[str, dict[str, str]] = {}
    records: dict[tuple[str, str, str], list[_Rec]] = {}  # (symbol, snapshot name, kind)
    for symbol in symbols:
        for snap in snapshots:
            for kind in KINDS:
                entry = snap.files.get((symbol, kind))
                if entry is None:
                    continue
                recs = _records(bronze.parsed[entry["sha256"]], entry["sha256"], f"{symbol} {kind}")
                records[(symbol, snap.name, kind)] = recs
                for rec in recs:
                    row = {
                        "source_record_id": rec.record_id,
                        "file_sha256": entry["sha256"],
                        "row_index": str(rec.index),
                        "record_sha256": rec.sha,
                    }
                    source_records[rec.record_id] = row
    tables["source_record"] = list(source_records.values())

    # Vendor listings and presence.
    source_listings: dict[str, dict[str, str]] = {}
    for symbol in symbols:
        instrument, listing = resolved[symbol]
        code = symbol.rsplit(".", 1)[0]
        present = 0
        for snap in snapshots:
            entry = snap.files.get((exchange_symbol[symbol], "symbols"))
            if entry is None:
                continue
            parsed = bronze.parsed[entry["sha256"]]
            if not isinstance(parsed, list) or not all(isinstance(r, dict) for r in parsed):
                raise ValueError(f"snapshot {snap.name}: an exchange list must be a list of records")
            matches = [r for r in parsed if r.get("Code") == code]
            if not matches:
                continue
            if len(matches) > 1:
                raise ValueError(f"{symbol}: two entries in snapshot {snap.name}'s exchange list")
            vendor = matches[0]
            attributes = {"vendor_exchange": symbol.rsplit(".", 1)[1]}
            attributes.update({column: _cell(vendor, field_name) for column, field_name in _LISTING_FIELDS})
            if attributes["currency"] != listing.quote_currency:
                raise ValueError(
                    f"{symbol}: the vendor's listing currency differs from the listing's in {snap.name}"
                )
            present += 1
            listing_key = s.sk(
                "source_listing",
                {"source_id": source_id, "source_symbol": symbol},
                {"attributes_sha256": s.attributes_sha256(attributes)},
            )
            source_listings[listing_key] = {
                "source_listing_sk": listing_key,
                "source_id": source_id,
                "source_symbol": symbol,
                **attributes,
            }
            tables["fact_listing_presence"].append(
                {
                    "source_listing_sk": listing_key,
                    "snapshot_id": snap.snapshot_id,
                    "instrument_sk": instrument_rows[instrument.instrument_code]["instrument_sk"],
                    "listing_sk": _listing_sk(instrument.instrument_code, listing),
                    "currency_sk": ctx.currency_sk(attributes["currency"]),
                }
            )
        if not present:
            raise ValueError(f"{symbol}: not present in any snapshot's exchange list")
        if not any((symbol, snap.name, kind) in records for snap in snapshots for kind in KINDS):
            raise ValueError(f"{symbol}: no file in any snapshot")
    tables["dim_source_listing"] = list(source_listings.values())

    # Facts.
    for symbol in symbols:
        instrument, listing = resolved[symbol]
        code = instrument.instrument_code
        instrument_sk = instrument_rows[code]["instrument_sk"]
        listing_sk = _listing_sk(code, listing)
        quote_sk = ctx.currency_sk(listing.quote_currency)

        def common(fact: str, symbol: str = symbol) -> dict[str, str]:
            series_id = f"{symbol}.{_QUANTITY[fact]}"
            return {
                "series_sk": s.sk("series", {"series_id": series_id}, {"definition": "1"}),
                "source_sk": source_sk,
                "audit_sk": audit_sk,
            }

        steps: dict[str, list[tuple[_Snapshot, str, list[_Item]]]] = {t: [] for t in _QUANTITY}
        for snap in snapshots:
            for kind in KINDS:
                recs = records.get((symbol, snap.name, kind))
                if recs is None:
                    continue
                what = f"{symbol} {kind} in snapshot {snap.name}"
                captured = snap.files[(symbol, kind)]["retrieved_at"]
                if kind == "eod":
                    _check_eod(recs, what)
                    bars, adjusted = [], []
                    for rec in recs:
                        day = rec.record["date"]
                        extra = {
                            "listing_sk": listing_sk,
                            "instrument_sk": instrument_sk,
                            "trade_date_sk": ctx.date_sk(day),
                            "trade_date": day,
                            "quote_currency_sk": quote_sk,
                        }
                        bar = {name: _cell(rec.record, name) for name in _BAR_MEASURES}
                        adj = {"adjusted_close": _cell(rec.record, "adjusted_close")}
                        coordinate: dict[str, str | int] = {"trade_date": day}
                        bars.append(_Item(coordinate, bar, rec.record_id, extra))
                        adjusted.append(_Item(coordinate, adj, rec.record_id, extra))
                    steps[BAR].append((snap, captured, bars))
                    steps[ADJUSTED].append((snap, captured, adjusted))
                elif kind == "div":
                    steps[DISTRIBUTION].append(
                        (snap, captured, _distribution_items(recs, what, instrument_sk, ctx))
                    )
                else:
                    steps[SPLIT].append((snap, captured, _split_items(recs, what, instrument_sk, ctx)))
        for fact in _QUANTITY:
            if steps[fact]:
                _run_series(out, fact, f"{symbol}.{_QUANTITY[fact]}", common(fact), steps[fact])
    for fact in _QUANTITY:
        tables[fact] = out.facts[fact]
    tables["bridge_vintage_support"] = out.bridge

    # Corrections: rules, then the applications in every snapshot holding the distributions.
    applications: dict[tuple[str, str], dict[str, str]] = {}
    rules: dict[str, list[str]] = {}  # symbol -> correction ids
    for symbol in symbols:
        ospec = observation[symbol]
        for correction in ospec["corrections"]:
            cid = s.correction_id(ospec["sha256"], correction["action"], correction["ex_date"])
            rules.setdefault(symbol, []).append(cid)
            tables["correction_rule"].append(
                {
                    "correction_id": cid,
                    "observation_spec_sha256": ospec["sha256"],
                    "source_symbol": symbol,
                    "action": correction["action"],
                    "ex_date": correction["ex_date"],
                    "reason": correction["reason"],
                    "evidence": correction["evidence"],
                }
            )
            for snap in snapshots:
                recs = records.get((symbol, snap.name, "div"))
                if recs is None:
                    continue
                hits = [
                    r for r in recs if r.record.get("date") == correction["ex_date"] and _positive(r.record)
                ]
                if len(hits) > 1:
                    raise ValueError(
                        f"{symbol}: a correction matches {len(hits)} distribution records in {snap.name}"
                    )
                if not hits:
                    continue
                target = hits[0]
                applications[(cid, snap.snapshot_id)] = {
                    "application_id": s.application_id(cid, snap.snapshot_id, target.record_id),
                    "correction_id": cid,
                    "snapshot_id": snap.snapshot_id,
                    "target_source_record_id": target.record_id,
                    "target_vintage_id": out.support[(DISTRIBUTION, target.record_id, snap.snapshot_id)][0],
                    "disposition": "excluded",
                }
    tables["fact_correction_application"] = list(applications.values())

    # Dimensions that come from the facts.
    tables["dim_date"] = [
        {
            "date_sk": s.sk("date", {"date": day}),
            "date": day,
            "year": str(date.fromisoformat(day).year),
            "month": str(date.fromisoformat(day).month),
            "day": str(date.fromisoformat(day).day),
            "iso_weekday": str(date.fromisoformat(day).isoweekday()),
        }
        for day in sorted(ctx.dates)
    ]
    tables["dim_date"].append(
        {
            "date_sk": s.sk("date", _SENTINEL),
            "date": "",
            "year": "",
            "month": "",
            "day": "",
            "iso_weekday": "",
        }
    )
    tables["dim_currency"] = [
        {"currency_sk": s.sk("currency", {"code": code}), "code": code} for code in sorted(ctx.currencies)
    ]
    tables["dim_currency"].append({"currency_sk": s.sk("currency", _SENTINEL), "code": ""})

    # Selections (§5).
    selections: dict[str, tuple[bytes, bytes]] = {}
    for selection in spec["selections"]:
        members = {
            symbol: snapshot_by_name[name].snapshot_id for symbol, name in selection["members"].items()
        }
        corrections: set[str] = set()
        rows: list[dict[str, str]] = []
        for symbol in sorted(members):
            snap = snapshot_by_name[selection["members"][symbol]]
            for kind in KINDS:
                if (symbol, snap.name, kind) not in records:
                    raise ValueError(
                        f"selection {selection['name']}: {symbol} lacks its {kind} file in {snap.name}"
                    )
            excluded: dict[str, str] = {}
            for cid in rules.get(symbol, []):
                application = applications.get((cid, snap.snapshot_id))
                if application is None:
                    raise ValueError(
                        f"selection {selection['name']}: a correction of {symbol} has no application "
                        f"in {snap.name}"
                    )
                corrections.add(cid)
                excluded[application["target_source_record_id"]] = cid
            for kind in KINDS:
                for rec in records[(symbol, snap.name, kind)]:
                    for fact in _FACTS_OF_KIND[kind]:
                        vid, obs = out.support[(fact, rec.record_id, snap.snapshot_id)]
                        cid = excluded.get(rec.record_id) if fact == DISTRIBUTION else None
                        rows.append(
                            {
                                "fact_table": fact,
                                "series_id": f"{symbol}.{_QUANTITY[fact]}",
                                "observation_id": obs,
                                "vintage_id": vid,
                                "source_record_id": rec.record_id,
                                "row_index": str(rec.index),
                                "disposition": "excluded" if cid else "selected",
                                "reason": cid or "",
                            }
                        )
        policy = s.selection_policy_bytes(selection["name"], members, corrections)
        selections[s.selection_id(policy)] = (policy, s.selection_bytes(rows))

    # Release (§6).
    table_data = {name: s.table_bytes(name, rows, capture_order) for name, rows in tables.items()}
    core = s.manifest_core(
        release_spec={"name": spec["release_name"], "version": spec["version"], "sha256": spec["sha256"]},
        register_sha256=register.sha256,
        observation_specs=[{"source_symbol": sym, "sha256": observation[sym]["sha256"]} for sym in symbols],
        snapshots=spec["snapshots"],
        code_commit=commit,
        tables=table_data,
        selections=selections,
    )
    release_dir, existed = s.write_release(Path(silver_root), core, table_data, selections)
    return release_dir, core, existed


def _listing_sk(instrument_code: str, listing: Listing) -> str:
    return s.sk(
        "listing",
        {
            "instrument_code": instrument_code,
            "mic": listing.mic,
            "ticker": listing.ticker,
            "valid_from": listing.valid_from,
        },
    )


def _distribution_items(recs: list[_Rec], what: str, instrument_sk: str, ctx: _Ctx) -> list[_Item]:
    occurrence = _occurrences(recs, what)
    items = []
    for rec in recs:
        record = rec.record
        measures = {
            column: (
                _optional_date(record, field_name) if column.endswith("_date") else _cell(record, field_name)
            )
            for column, field_name in _DISTRIBUTION_FIELDS
        }
        ex_date = record["date"]
        extra = {
            "instrument_sk": instrument_sk,
            "currency_sk": ctx.currency_sk(measures["currency"]),
            "ex_date_sk": ctx.date_sk(ex_date),
            "declaration_date_sk": ctx.date_sk(measures["declaration_date"]),
            "record_date_sk": ctx.date_sk(measures["record_date"]),
            "payment_date_sk": ctx.date_sk(measures["payment_date"]),
            "ex_date": ex_date,
            "occurrence": str(occurrence[rec.index]),
        }
        coordinate: dict[str, str | int] = {"ex_date": ex_date, "occurrence": occurrence[rec.index]}
        items.append(_Item(coordinate, measures, rec.record_id, extra))
    return items


def _split_items(recs: list[_Rec], what: str, instrument_sk: str, ctx: _Ctx) -> list[_Item]:
    occurrence = _occurrences(recs, what)
    items = []
    for rec in recs:
        ratio = _cell(rec.record, "split")
        sides = ratio.split("/")
        new_units, old_units = (sides[0], sides[1]) if len(sides) == 2 else ("", "")
        day = rec.record["date"]
        extra = {
            "instrument_sk": instrument_sk,
            "effective_date_sk": ctx.date_sk(day),
            "effective_date": day,
            "occurrence": str(occurrence[rec.index]),
            "new_units": new_units,
            "old_units": old_units,
        }
        coordinate: dict[str, str | int] = {"date": day, "occurrence": occurrence[rec.index]}
        items.append(_Item(coordinate, {"ratio": ratio}, rec.record_id, extra))
    return items
