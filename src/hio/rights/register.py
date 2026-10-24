"""Loading rights registers, read-only.

Two kinds, never mixed (OD-0020 item 3):
- the genuine register, registers/sources.yaml: no 'synthetic.' source may appear in it;
- synthetic fixtures under tests/fixtures/synthetic/: every source id starts with 'synthetic.',
  and line 1 declares SYNTHETIC. Synthetic owner_verified metadata therefore lives only in
  fixture files and can never change a genuine record. This module has no writer.
"""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType
from typing import Any

import yaml

from hio.rights.model import ALL_PERMISSIONS, Permission, RightsRecord, Verification


class RegisterError(ValueError):
    pass


def load_genuine(path: str | Path) -> MappingProxyType[str, RightsRecord]:
    data = yaml.safe_load(Path(path).read_text())
    out = {}
    for src in data.get("sources", []):
        sid = src["id"]
        if sid.startswith("synthetic"):
            raise RegisterError(f"synthetic source {sid!r} in the genuine register")
        out[sid] = _record(sid, src)
    return MappingProxyType(out)


def load_synthetic(path: str | Path) -> MappingProxyType[str, RightsRecord]:
    p = Path(path)
    if "SYNTHETIC" not in p.read_text().splitlines()[0]:
        raise RegisterError(f"{p}: line 1 must declare SYNTHETIC")
    if p.resolve().parent.name != "synthetic":
        raise RegisterError(f"{p}: synthetic rights fixtures live in a 'synthetic' fixtures directory")
    data = yaml.safe_load(p.read_text())
    out = {}
    for src in data["sources"]:
        sid = src["id"]
        if not sid.startswith("synthetic."):
            raise RegisterError(f"{p}: fixture source ids must start with 'synthetic.': {sid!r}")
        out[sid] = _record(sid, src)
    return MappingProxyType(out)


def _record(sid: str, src: dict[str, Any]) -> RightsRecord:
    rights = src.get("rights") or {}
    flat: dict[str, Any] = {}
    for key, value in rights.items():
        if key == "distribution" and isinstance(value, dict):
            for cls, v in value.items():
                flat[f"distribution.{cls}"] = v
        elif key != "attribution_required":
            flat[key] = value
    # A genuine record's research proposals (rights_proposed, dataset notes) are notes, not
    # rights values, and are ignored here (OD-0013).
    permissions = {perm: Permission.parse(flat.get(perm)) for perm in ALL_PERMISSIONS}
    return RightsRecord(
        source_id=sid,
        verification=Verification(src.get("verification", "unverified")),
        permissions=permissions,
        satisfied_conditions=src.get("satisfied_conditions") or {},
    )
