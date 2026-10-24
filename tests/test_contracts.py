"""Contracts: canonical rendering, manifest core, status events (releases standard §1–§5, §6.1)."""

from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from hio.contracts.canonical import canonical_json, decimal_str, instant_str
from hio.contracts.manifest import ManifestSchemaError, content_sha256, validate_manifest_core
from hio.contracts.status import Status, StatusError, StatusEvent, effective_status
from hio.contracts.temporal import KnowableBasis, weakest

AT = datetime(2026, 10, 24, tzinfo=UTC)


def core(**over):
    c = {
        "dataset_id": "synthetic.ds",
        "version": "0.2.0",
        "spec_ref": "x@0.2.0",
        "code_ref": {"commit": "c", "lock_sha256": "l"},
        "inputs": [],
        "knowledge_mode": "as_captured_by_hio",
        "knowledge_cutoff": "2026-01-01T00:00:00.000000Z",
        "weakest_knowable_basis": "captured_on_schedule",
        "rights": {},
        "invariant_results": {},
        "quality_summary": {},
        "files": [{"path": "data.csv", "sha256": "0" * 64, "rendering": "csv"}],
        "supersedes": None,
    }
    c.update(over)
    return c


def test_canonical_json_is_sorted_compact_utf8():
    assert canonical_json({"b": 1, "a": "−"}) == '{"a":"−","b":1}'.encode()


def test_decimals_render_in_plain_notation():
    assert decimal_str(Decimal("1E-7")) == "0.0000001"
    assert decimal_str(Decimal("0.000358333333333333333333")) == "0.000358333333333333333333"
    assert decimal_str(Decimal("-0.0")) == "0"
    assert decimal_str(Decimal("100.00")) == "100"


def test_instants_must_be_aware_and_render_in_utc():
    assert instant_str(datetime(2026, 1, 1, 10, tzinfo=timezone(timedelta(hours=10)))) == (
        "2026-01-01T00:00:00.000000Z"
    )
    with pytest.raises(ValueError):
        instant_str(datetime(2026, 1, 1))  # noqa: DTZ001 (deliberately naive)


def test_knowable_basis_order_and_market_support():
    assert [b.supports_market_knowledge for b in KnowableBasis] == [True, True, True, True, False, False]
    assert (
        weakest([KnowableBasis.PUBLISHER_VINTAGE, KnowableBasis.SCHEDULE_ONLY]) is KnowableBasis.SCHEDULE_ONLY
    )


def test_manifest_core_refuses_self_reference():
    """Releases standard §6.1 fixture 4: adding content_sha256 to the core fails the schema."""
    validate_manifest_core(core())
    with pytest.raises(ManifestSchemaError, match="content_sha256"):
        validate_manifest_core(core(content_sha256="abc"))
    with pytest.raises(ManifestSchemaError, match="created_at"):
        validate_manifest_core(core(created_at="2026-10-24"))
    with pytest.raises(ManifestSchemaError, match="status"):
        validate_manifest_core(core(status="validated"))


def test_manifest_hash_is_deterministic_and_input_order_is_enforced():
    assert content_sha256(core()) == content_sha256(dict(reversed(list(core().items()))))
    with pytest.raises(ManifestSchemaError, match="sorted"):
        validate_manifest_core(core(inputs=[{"a": 2}, {"a": 1}]))


def ev(seq, status, consumer=None):
    return StatusEvent("h", seq, status, "owner", "e", AT, consumer)


def test_effective_status_is_highest_seq_and_withdrawn_is_terminal():
    assert effective_status([ev(1, Status.EXPLORATORY), ev(2, Status.VALIDATED)]).status is Status.VALIDATED
    with pytest.raises(StatusError, match="terminal"):
        effective_status([ev(1, Status.WITHDRAWN), ev(2, Status.VALIDATED)])


def test_status_seq_gap_or_duplicate_fails():
    with pytest.raises(StatusError):
        effective_status([ev(1, Status.EXPLORATORY), ev(3, Status.VALIDATED)])
    with pytest.raises(StatusError):
        effective_status([ev(1, Status.EXPLORATORY), ev(1, Status.VALIDATED)])


def test_consumer_class_only_for_approval():
    ev(1, Status.APPROVED_FOR_CONSUMER, "hio_internal")
    with pytest.raises(StatusError):
        ev(1, Status.APPROVED_FOR_CONSUMER)
    with pytest.raises(StatusError):
        ev(1, Status.VALIDATED, "hio_internal")


def test_dates_serialise_as_iso_dates_not_instants():
    assert canonical_json({"d": date(2020, 2, 1)}) == b'{"d":"2020-02-01"}'


def test_obs_inv_005_a_vintage_refuses_an_instant_as_valid_time():
    from hio.contracts.observation import Vintage
    from hio.contracts.temporal import QualityStatus

    with pytest.raises(TypeError, match="OBS-INV-005"):
        Vintage(
            "synthetic.s",
            AT,
            1,
            Decimal(1),
            "r" * 64,
            AT,
            AT,
            KnowableBasis.SCHEDULE_ONLY,
            "UTC",
            QualityStatus.VALID,
        )
