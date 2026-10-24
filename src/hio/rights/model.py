"""Rights records and propagation (rights standard §1–§2).

Records are immutable once loaded. Nothing in HIO writes a rights register: the genuine
register is edited only by people, through owner actions (OD-0020 item 3).
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType

PERMISSIONS = (
    "automated_retrieval",
    "raw_retention",
    "internal_compute",
    "derivation",
    "derived_storage",
    "post_termination_raw",
    "post_termination_derived",
    "quotation_in_documents",
    "agent_context",
    "external_processing",
    "audit_retention",
)
CONSUMER_CLASSES = ("hio_internal", "smsf_app", "smsf_trustee_pack", "smsf_auditor", "third_party")
ALL_PERMISSIONS = PERMISSIONS + tuple(f"distribution.{c}" for c in CONSUMER_CLASSES)


class Verification(StrEnum):
    UNVERIFIED = "unverified"
    VENDOR_ASSERTED = "vendor_asserted"
    OWNER_VERIFIED = "owner_verified"
    CONTRACT = "contract"

    @property
    def sufficient(self) -> bool:
        """Only owner_verified or contract may support an operation (§3)."""
        return self in {Verification.OWNER_VERIFIED, Verification.CONTRACT}


class Kind(StrEnum):
    DENY = "deny"
    UNKNOWN = "unknown"
    CONDITIONAL = "conditional"
    ALLOW = "allow"


_RANK = {Kind.DENY: 0, Kind.UNKNOWN: 1, Kind.CONDITIONAL: 2, Kind.ALLOW: 3}  # §2 ordering


@dataclass(frozen=True)
class Permission:
    kind: Kind
    condition: str | None = None

    @classmethod
    def parse(cls, text: object) -> Permission:
        if text is None:
            return cls(Kind.UNKNOWN)  # a missing permission is unknown, and unknown means deny
        s = str(text).strip()
        m = re.fullmatch(r"conditional\((.+)\)", s)
        if m:
            return cls(Kind.CONDITIONAL, m.group(1))
        try:
            return cls(Kind(s))
        except ValueError:
            raise ValueError(f"not a permission value: {s!r}") from None

    def __str__(self) -> str:
        return f"conditional({self.condition})" if self.kind is Kind.CONDITIONAL else self.kind.value


@dataclass(frozen=True)
class RightsRecord:
    source_id: str
    verification: Verification
    permissions: Mapping[str, Permission]
    satisfied_conditions: Mapping[str, str] = field(default_factory=dict)  # permission -> evidence

    def __post_init__(self) -> None:
        missing = set(ALL_PERMISSIONS) - set(self.permissions)
        if missing:
            raise ValueError(f"{self.source_id}: permissions not stated: {sorted(missing)}")
        object.__setattr__(self, "permissions", MappingProxyType(dict(self.permissions)))
        object.__setattr__(self, "satisfied_conditions", MappingProxyType(dict(self.satisfied_conditions)))

    def get(self, permission: str) -> Permission:
        return self.permissions[permission]


def propagate(records: Iterable[RightsRecord]) -> dict[str, str]:
    """A derived dataset's rights: per permission, the most restrictive value across its inputs;
    conditional values carry their conditions forward, concatenated (§2). Overrides are not
    supported in S1a. Returned as plain strings for the manifest snapshot."""
    recs = sorted(records, key=lambda r: r.source_id)
    if not recs:
        raise ValueError("no input rights")
    out: dict[str, str] = {}
    for perm in ALL_PERMISSIONS:
        values = [r.get(perm) for r in recs]
        worst = min(values, key=lambda p: _RANK[p.kind])
        if worst.kind is Kind.CONDITIONAL:
            conditions = "; ".join(
                sorted({p.condition for p in values if p.kind is Kind.CONDITIONAL and p.condition})
            )
            out[perm] = f"conditional({conditions})"
        else:
            out[perm] = worst.kind.value
    out["verification"] = min((r.verification for r in recs), key=lambda v: list(Verification).index(v)).value
    return out
