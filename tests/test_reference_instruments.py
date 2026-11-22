"""The instrument register loader (silver v2 contract §3). Invented registers only, plus the real file."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from hio.reference.instruments import Instrument, Listing, Register, SourceMapping, load_register

REPO = Path(__file__).resolve().parents[1]

GOOD = """\
status: proposed
instruments:
  - instrument_code: example-fund
    name: "Example Fund"
    issuer_code: example-issuer
    vehicle_type: etf
    domicile: US
    listings:
      - {mic: XXXX, ticker: ZZZ, quote_currency: USD, valid_from: null}
    source_mappings:
      - {source_id: some.source, source_symbol: ZZZ.US, mic: XXXX, ticker: ZZZ}
  - instrument_code: other-fund2
    name: "Other, Fund"
    issuer_code: other-issuer
    vehicle_type: etf
    domicile: AU
    listings:
      - {mic: XASX, ticker: OTH, quote_currency: AUD, valid_from: "2020-01-02"}
    source_mappings:
      - {source_id: some.source, source_symbol: OTH.AU, mic: XASX, ticker: OTH}
"""


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "instruments.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def _bad(tmp_path: Path, old: str, new: str, match: str, text: str = GOOD) -> None:
    assert old in text
    path = _write(tmp_path, text.replace(old, new, 1))
    with pytest.raises(ValueError, match=match):
        load_register(path)


def test_loads_invented_register(tmp_path: Path) -> None:
    path = _write(tmp_path, GOOD)
    reg = load_register(path)
    assert isinstance(reg, Register)
    assert reg.status == "proposed"
    assert reg.sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    first, second = reg.instruments
    assert first == Instrument(
        "example-fund",
        "Example Fund",
        "example-issuer",
        "etf",
        "US",
        (Listing("XXXX", "ZZZ", "USD", ""),),
        (SourceMapping("some.source", "ZZZ.US", "XXXX", "ZZZ"),),
    )
    assert second.listings[0].valid_from == "2020-01-02"
    assert reg.resolve("some.source", "OTH.AU") == (second, second.listings[0])


def test_unquoted_yaml_date_is_accepted_as_iso_text(tmp_path: Path) -> None:
    text = GOOD.replace('valid_from: "2020-01-02"', "valid_from: 2020-01-02")
    reg = load_register(_write(tmp_path, text))
    assert reg.instruments[1].listings[0].valid_from == "2020-01-02"


def test_resolve_refuses_unmapped_symbol(tmp_path: Path) -> None:
    reg = load_register(_write(tmp_path, GOOD))
    with pytest.raises(ValueError, match="no register mapping"):
        reg.resolve("some.source", "ZZZ.AU")
    with pytest.raises(ValueError, match="no register mapping"):
        reg.resolve("some.source", "ZZZ")  # a bare ticker is never guessed
    with pytest.raises(ValueError, match="no register mapping"):
        reg.resolve("other.source", "ZZZ.US")


def test_real_register_loads_and_resolves() -> None:
    reg = load_register(REPO / "registers" / "instruments.yaml")
    assert len(reg.instruments) == 9
    assert reg.sha256 == hashlib.sha256((REPO / "registers" / "instruments.yaml").read_bytes()).hexdigest()
    mappings = [(m.source_id, m.source_symbol) for i in reg.instruments for m in i.source_mappings]
    assert len(mappings) == 9
    for source_id, symbol in mappings:
        instrument, listing = reg.resolve(source_id, symbol)
        assert instrument.listings and listing in instrument.listings
        assert f"{listing.ticker}." in symbol


def test_unknown_or_missing_keys_refused(tmp_path: Path) -> None:
    _bad(tmp_path, "status: proposed\n", "status: proposed\nextra: 1\n", "register")
    _bad(tmp_path, "status: proposed\n", "", "register")
    _bad(tmp_path, "    domicile: US\n", "    domicile: US\n    colour: red\n", "example-fund")
    _bad(tmp_path, "    issuer_code: example-issuer\n", "", "example-fund")
    _bad(
        tmp_path,
        "{mic: XXXX, ticker: ZZZ, quote_currency: USD, valid_from: null}",
        "{mic: XXXX, ticker: ZZZ, quote_currency: USD}",
        "example-fund",
    )
    _bad(
        tmp_path,
        "quote_currency: USD, valid_from: null}",
        "quote_currency: USD, valid_from: null, x: 1}",
        "example-fund",
    )
    _bad(tmp_path, "mic: XXXX, ticker: ZZZ}", "mic: XXXX}", "example-fund")
    _bad(tmp_path, "mic: XXXX, ticker: ZZZ}", "mic: XXXX, ticker: ZZZ, x: 1}", "example-fund")


@pytest.mark.parametrize("code", ["Example", "-a", "a-", "a--b", "a_b", "a b", "''"])
def test_instrument_code_must_be_slug(tmp_path: Path, code: str) -> None:
    _bad(tmp_path, "instrument_code: example-fund", f"instrument_code: {code}", "instrument_code")


def test_codes_unique(tmp_path: Path) -> None:
    _bad(
        tmp_path, "instrument_code: other-fund2", "instrument_code: example-fund", "duplicate instrument_code"
    )


@pytest.mark.parametrize("field", ["name", "issuer_code", "vehicle_type", "domicile"])
@pytest.mark.parametrize("value", ["''", "null", "'  '", "5"])
def test_text_fields_non_empty_strings(tmp_path: Path, field: str, value: str) -> None:
    first_line = next(line for line in GOOD.splitlines() if line.startswith(f"    {field}:"))
    _bad(tmp_path, first_line, f"    {field}: {value}", f"example-fund.*{field}")


@pytest.mark.parametrize("mic", ["xxxx", "XXX", "XXXXX", "XX-X", "''"])
def test_mic_four_upper_case_alphanumerics(tmp_path: Path, mic: str) -> None:
    _bad(tmp_path, "{mic: XXXX, ticker: ZZZ, quote", f"{{mic: {mic}, ticker: ZZZ, quote", "mic")


def test_mic_with_digits_accepted(tmp_path: Path) -> None:
    text = GOOD.replace("{mic: XXXX, ticker: ZZZ, quote", "{mic: X1X2, ticker: ZZZ, quote").replace(
        "mic: XXXX, ticker: ZZZ}", "mic: X1X2, ticker: ZZZ}"
    )
    assert load_register(_write(tmp_path, text)).instruments[0].listings[0].mic == "X1X2"


@pytest.mark.parametrize("currency", ["usd", "US", "USDD", "U$D", "''"])
def test_quote_currency_three_upper_case_letters(tmp_path: Path, currency: str) -> None:
    _bad(tmp_path, "quote_currency: USD", f"quote_currency: {currency}", "quote_currency")


@pytest.mark.parametrize(
    "value", ["''", "2020-13-01", "2020-1-2", "20200102", "yesterday", "2020-01-02T00:00:00", "5"]
)
def test_valid_from_null_or_iso_date(tmp_path: Path, value: str) -> None:
    # YAML itself refuses an unquoted impossible date such as 2020-13-01 before the loader sees it.
    _bad(tmp_path, "valid_from: null", f"valid_from: {value}", "valid_from|YAML")


def test_at_least_one_listing(tmp_path: Path) -> None:
    listing = "      - {mic: XXXX, ticker: ZZZ, quote_currency: USD, valid_from: null}\n"
    mapping = "      - {source_id: some.source, source_symbol: ZZZ.US, mic: XXXX, ticker: ZZZ}\n"
    text = GOOD.replace(
        f"    listings:\n{listing}    source_mappings:\n{mapping}",
        "    listings: []\n    source_mappings: []\n",
    )
    with pytest.raises(ValueError, match=r"example-fund.*listings"):
        load_register(_write(tmp_path, text))


def test_listing_keys_unique_within_instrument(tmp_path: Path) -> None:
    dup = "      - {mic: XXXX, ticker: ZZZ, quote_currency: USD, valid_from: null}\n"
    _bad(tmp_path, dup, dup + dup, "example-fund.*duplicate listing")
    # The same (mic, ticker) with a different valid_from is a distinct listing key, but a mapping naming
    # (mic, ticker) then matches two listings and is refused.
    two = dup + "      - {mic: XXXX, ticker: ZZZ, quote_currency: USD, valid_from: '2021-01-01'}\n"
    _bad(tmp_path, dup, two, "exactly one listing")


def test_mapping_names_exactly_one_listing(tmp_path: Path) -> None:
    _bad(
        tmp_path,
        "source_symbol: ZZZ.US, mic: XXXX, ticker: ZZZ}",
        "source_symbol: ZZZ.US, mic: XXXX, ticker: YYY}",
        "exactly one listing",
    )
    _bad(
        tmp_path,
        "source_symbol: ZZZ.US, mic: XXXX, ticker: ZZZ}",
        "source_symbol: ZZZ.US, mic: XASX, ticker: ZZZ}",
        "exactly one listing",
    )
    # A mapping may not borrow another instrument's listing.
    _bad(
        tmp_path,
        "source_symbol: ZZZ.US, mic: XXXX, ticker: ZZZ}",
        "source_symbol: ZZZ.US, mic: XASX, ticker: OTH}",
        "example-fund",
    )


def test_source_symbol_pairs_unique_across_register(tmp_path: Path) -> None:
    _bad(tmp_path, "source_symbol: OTH.AU", "source_symbol: ZZZ.US", "already used")


def test_same_symbol_under_two_sources_is_allowed(tmp_path: Path) -> None:
    text = GOOD.replace(
        "source_id: some.source, source_symbol: OTH.AU", "source_id: another.source, source_symbol: ZZZ.US"
    )
    reg = load_register(_write(tmp_path, text))
    assert reg.resolve("another.source", "ZZZ.US")[0].instrument_code == "other-fund2"
    assert reg.resolve("some.source", "ZZZ.US")[0].instrument_code == "example-fund"


def test_source_symbol_contains_dot(tmp_path: Path) -> None:
    _bad(tmp_path, "source_symbol: ZZZ.US", "source_symbol: ZZZ", "example-fund.*dot")


def test_malformed_yaml_and_wrong_shapes_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="YAML"):
        load_register(_write(tmp_path, "status: [unclosed\n"))
    with pytest.raises(ValueError, match="register"):
        load_register(_write(tmp_path, "- a\n- b\n"))
    with pytest.raises(ValueError, match="instruments"):
        load_register(_write(tmp_path, "status: proposed\ninstruments: nope\n"))
    with pytest.raises(ValueError, match="instrument #0"):
        load_register(_write(tmp_path, "status: proposed\ninstruments: [1]\n"))


def test_dataclasses_are_frozen(tmp_path: Path) -> None:
    reg = load_register(_write(tmp_path, GOOD))
    with pytest.raises(AttributeError):
        reg.instruments[0].name = "x"  # type: ignore[misc]
    with pytest.raises(AttributeError):
        reg.status = "approved"  # type: ignore[misc]
