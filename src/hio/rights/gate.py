"""The operation-to-permission gate, fail closed (rights standard §3).

Before an operation, every input source must grant every permission the operation needs:
- deny and unknown refuse;
- conditional(c) refuses unless c is recorded as satisfied, with evidence;
- verification must be owner_verified or contract.
A refusal names every failing (source, permission) and happens before any output is written.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from hio.contracts.rights import Operation, RightsRefused
from hio.rights.model import Kind, RightsRecord

BASE_REQUIREMENTS: dict[Operation, tuple[str, ...]] = {
    Operation.FETCH: ("automated_retrieval",),
    Operation.STORE_RAW: ("raw_retention",),
    Operation.BUILD: ("internal_compute", "derivation"),
    Operation.STORE_DERIVED: ("derived_storage",),
    Operation.REBUILD: ("internal_compute", "derivation", "derived_storage", "raw_retention"),
    Operation.PUBLISH: (),  # plus distribution.<class>
}


@dataclass(frozen=True)
class GateContext:
    """external_processing is required when the operation runs on a CI runner or a cloud host,
    or stores to a cloud bucket. S1a runs locally or on CI with a local store."""

    on_external_host: bool = False
    quotes_values_in_documents: bool = False


def required_permissions(
    operation: Operation, context: GateContext, consumer_class: str | None = None
) -> tuple[str, ...]:
    perms = list(BASE_REQUIREMENTS[operation])
    if context.on_external_host:
        perms.append("external_processing")
    if operation is Operation.PUBLISH:
        if consumer_class is None:
            raise ValueError("publish needs a consumer class")
        perms.append(f"distribution.{consumer_class}")
        if context.quotes_values_in_documents:
            perms.append("quotation_in_documents")
    return tuple(perms)


class RightsGate:
    def __init__(self, records: Mapping[str, RightsRecord], context: GateContext | None = None) -> None:
        self.records = records
        self.context = context or GateContext()

    def authorise(
        self, operation: Operation, source_ids: Iterable[str], consumer_class: str | None = None
    ) -> None:
        sources = sorted(set(source_ids))
        if not sources:
            raise RightsRefused(operation, ["no input sources declared"])
        reasons = []
        needed = required_permissions(operation, self.context, consumer_class)
        for sid in sources:
            record = self.records.get(sid)
            if record is None:
                reasons.append(f"{sid}: no rights record (unknown means deny)")
                continue
            if not record.verification.sufficient:
                reasons.append(f"{sid}: verification is {record.verification.value}")
            for perm in needed:
                p = record.get(perm)
                if p.kind is Kind.ALLOW:
                    continue
                if p.kind is Kind.CONDITIONAL and record.satisfied_conditions.get(perm):
                    continue
                reasons.append(
                    f"{sid}: {perm} is {p}"
                    + (" (not recorded as satisfied)" if p.kind is Kind.CONDITIONAL else "")
                )
        if reasons:
            raise RightsRefused(operation, reasons)
