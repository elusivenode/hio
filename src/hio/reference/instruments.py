"""The instrument register loader (silver version 2 contract §3, "Instrument register").

HIO mints its own instrument identities; this module only reads and validates the register file
`registers/instruments.yaml`. It is pure and deterministic: it reads one file and nothing else.
Every refusal is a `ValueError` that names the instrument it concerns.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from hio.contracts.canonical import sha256_hex

_CODE = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
_MIC = re.compile(r"[A-Z0-9]{4}")
_CURRENCY = re.compile(r"[A-Z]{3}")
_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")

_REGISTER_KEYS = {"status", "instruments"}
_INSTRUMENT_KEYS = {
    "instrument_code",
    "name",
    "issuer_code",
    "vehicle_type",
    "domicile",
    "listings",
    "source_mappings",
}
_LISTING_KEYS = {"mic", "ticker", "quote_currency", "valid_from"}
_MAPPING_KEYS = {"source_id", "source_symbol", "mic", "ticker"}


@dataclass(frozen=True)
class Listing:
    """One listing of an instrument. `valid_from` is an ISO date, or "" when not established."""

    mic: str
    ticker: str
    quote_currency: str
    valid_from: str


@dataclass(frozen=True)
class SourceMapping:
    """A vendor symbol mapped to exactly one listing of its instrument, by (mic, ticker)."""

    source_id: str
    source_symbol: str
    mic: str
    ticker: str


@dataclass(frozen=True)
class Instrument:
    """One HIO instrument identity with its listings and its source mappings."""

    instrument_code: str
    name: str
    issuer_code: str
    vehicle_type: str
    domicile: str
    listings: tuple[Listing, ...]
    source_mappings: tuple[SourceMapping, ...]


@dataclass(frozen=True)
class Register:
    """A validated register. `sha256` is the lower-case hex sha256 of the file's bytes."""

    status: str
    instruments: tuple[Instrument, ...]
    sha256: str

    def resolve(self, source_id: str, source_symbol: str) -> tuple[Instrument, Listing]:
        """Contract §3: a (source, symbol) pair resolves only through a mapping.

        An unmapped pair is refused with `ValueError`; a symbol is never guessed from a ticker.
        """
        for instrument in self.instruments:
            for mapping in instrument.source_mappings:
                if mapping.source_id == source_id and mapping.source_symbol == source_symbol:
                    for listing in instrument.listings:
                        if listing.mic == mapping.mic and listing.ticker == mapping.ticker:
                            return instrument, listing
        raise ValueError(f"no register mapping for source {source_id!r} symbol {source_symbol!r}")


def _exact_keys(obj: Any, keys: set[str], where: str) -> dict[str, Any]:
    if not isinstance(obj, dict):
        raise ValueError(f"{where}: expected a mapping, got {type(obj).__name__}")
    missing = sorted(keys - set(obj))
    extra = sorted(str(k) for k in set(obj) - keys)
    if missing or extra:
        raise ValueError(f"{where}: keys must be exactly {sorted(keys)} (missing {missing}, extra {extra})")
    return obj


def _text(value: Any, field: str, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where}: {field} must be a non-empty string, got {value!r}")
    return value


def _pattern(value: Any, field: str, where: str, pattern: re.Pattern[str], rule: str) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise ValueError(f"{where}: {field} must be {rule}, got {value!r}")
    return value


def _valid_from(value: Any, where: str) -> str:
    if value is None:
        return ""
    # YAML reads an unquoted 2020-01-01 as a date object; accept it as the same ISO date.
    if type(value) is date:
        return value.isoformat()
    if isinstance(value, str) and _ISO_DATE.fullmatch(value):
        try:
            date.fromisoformat(value)
        except ValueError:
            pass
        else:
            return value
    raise ValueError(f"{where}: valid_from must be null or an ISO date (YYYY-MM-DD), got {value!r}")


def _listing(raw: Any, where: str) -> Listing:
    obj = _exact_keys(raw, _LISTING_KEYS, where)
    return Listing(
        mic=_pattern(obj["mic"], "mic", where, _MIC, "four upper-case letters or digits"),
        ticker=_text(obj["ticker"], "ticker", where),
        quote_currency=_pattern(
            obj["quote_currency"], "quote_currency", where, _CURRENCY, "three upper-case letters"
        ),
        valid_from=_valid_from(obj["valid_from"], where),
    )


def _mapping(raw: Any, where: str) -> SourceMapping:
    obj = _exact_keys(raw, _MAPPING_KEYS, where)
    symbol = _text(obj["source_symbol"], "source_symbol", where)
    if "." not in symbol:
        raise ValueError(f"{where}: source_symbol must contain a dot, got {symbol!r}")
    return SourceMapping(
        source_id=_text(obj["source_id"], "source_id", where),
        source_symbol=symbol,
        mic=_text(obj["mic"], "mic", where),
        ticker=_text(obj["ticker"], "ticker", where),
    )


def _instrument(raw: Any, index: int) -> Instrument:
    where = f"instrument #{index}"
    if isinstance(raw, dict) and isinstance(raw.get("instrument_code"), str):
        where = f"instrument {raw['instrument_code']!r}"
    obj = _exact_keys(raw, _INSTRUMENT_KEYS, where)
    code = _pattern(obj["instrument_code"], "instrument_code", where, _CODE, "a lower-case slug")
    where = f"instrument {code!r}"
    name = _text(obj["name"], "name", where)
    issuer_code = _text(obj["issuer_code"], "issuer_code", where)
    vehicle_type = _text(obj["vehicle_type"], "vehicle_type", where)
    domicile = _text(obj["domicile"], "domicile", where)

    raw_listings = obj["listings"]
    if not isinstance(raw_listings, list) or not raw_listings:
        raise ValueError(f"{where}: listings must be a non-empty list")
    listings = tuple(_listing(item, f"{where} listing #{i}") for i, item in enumerate(raw_listings))
    seen_listings: set[tuple[str, str, str]] = set()
    for listing in listings:
        key = (listing.mic, listing.ticker, listing.valid_from)
        if key in seen_listings:
            raise ValueError(f"{where}: duplicate listing {key}")
        seen_listings.add(key)

    raw_mappings = obj["source_mappings"]
    if not isinstance(raw_mappings, list):
        raise ValueError(f"{where}: source_mappings must be a list")
    mappings = tuple(_mapping(item, f"{where} mapping #{i}") for i, item in enumerate(raw_mappings))
    for mapping in mappings:
        matches = [x for x in listings if (x.mic, x.ticker) == (mapping.mic, mapping.ticker)]
        if len(matches) != 1:
            raise ValueError(
                f"{where}: mapping {mapping.source_symbol!r} must name exactly one listing "
                f"by (mic, ticker) {(mapping.mic, mapping.ticker)}, found {len(matches)}"
            )

    return Instrument(code, name, issuer_code, vehicle_type, domicile, listings, mappings)


def load_register(path: Path) -> Register:
    """Contract §3: read and validate the instrument register at `path`.

    Refuses (`ValueError` naming the instrument) any key set other than the exact one at every
    level, a code that is not a lower-case slug or is not unique, an empty name, issuer, vehicle
    type or domicile, a `mic` that is not four upper-case letters or digits, a `quote_currency`
    that is not three upper-case letters, a `valid_from` that is neither null nor an ISO date, an
    instrument with no listing, a repeated (mic, ticker, valid_from) within an instrument, a
    mapping that does not name exactly one listing of its instrument by (mic, ticker), a repeated
    (source_id, source_symbol) across the register, and a `source_symbol` without a dot.
    `Register.sha256` is the sha256 of the file's bytes.
    """
    data = Path(path).read_bytes()
    try:
        doc = yaml.safe_load(data)
    except (yaml.YAMLError, ValueError) as exc:  # ValueError: YAML's own date parse, e.g. 2020-13-01
        raise ValueError(f"register is not valid YAML: {exc}") from exc
    obj = _exact_keys(doc, _REGISTER_KEYS, "register")
    status = _text(obj["status"], "status", "register")
    raw_instruments = obj["instruments"]
    if not isinstance(raw_instruments, list):
        raise ValueError("register: instruments must be a list")

    instruments = tuple(_instrument(item, i) for i, item in enumerate(raw_instruments))
    codes: set[str] = set()
    pairs: dict[tuple[str, str], str] = {}
    for instrument in instruments:
        if instrument.instrument_code in codes:
            raise ValueError(f"instrument {instrument.instrument_code!r}: duplicate instrument_code")
        codes.add(instrument.instrument_code)
        for mapping in instrument.source_mappings:
            pair = (mapping.source_id, mapping.source_symbol)
            if pair in pairs:
                raise ValueError(
                    f"instrument {instrument.instrument_code!r}: mapping {pair} is already used by "
                    f"instrument {pairs[pair]!r}"
                )
            pairs[pair] = instrument.instrument_code
    return Register(status=status, instruments=instruments, sha256=sha256_hex(data))
