"""Release manifest core (releases standard §2) and its content identity.

The core holds exactly the fields below. It never contains its own hash, created_at or any
status (§2; §6.1 fixture 4): validate_manifest_core refuses any other field.
"""

from __future__ import annotations

from typing import Any

from hio.contracts.canonical import canonical_json, sha256_hex

MANIFEST_CORE_FIELDS = frozenset(
    {
        "dataset_id",
        "version",
        "spec_ref",
        "code_ref",
        "inputs",
        "knowledge_mode",
        "knowledge_cutoff",
        "weakest_knowable_basis",
        "rights",
        "invariant_results",
        "quality_summary",
        "files",
        "supersedes",
    }
)


class ManifestSchemaError(ValueError):
    pass


def validate_manifest_core(core: dict[str, Any]) -> None:
    keys = set(core)
    extra = keys - MANIFEST_CORE_FIELDS
    missing = MANIFEST_CORE_FIELDS - keys
    if extra:
        raise ManifestSchemaError(f"fields not allowed in the manifest core: {sorted(extra)}")
    if missing:
        raise ManifestSchemaError(f"manifest core is missing: {sorted(missing)}")
    if not isinstance(core["files"], list) or not core["files"]:
        raise ManifestSchemaError("files must be a non-empty list")
    for f in core["files"]:
        if set(f) != {"path", "sha256", "rendering"}:
            raise ManifestSchemaError(f"file entry fields must be path, sha256, rendering: {f}")
    if core["inputs"] != sorted(core["inputs"], key=canonical_json):
        raise ManifestSchemaError("inputs must be sorted canonically")


def content_sha256(core: dict[str, Any]) -> str:
    validate_manifest_core(core)
    return sha256_hex(canonical_json(core))


def release_id(content_hash: str) -> str:
    return f"rel-{content_hash}"
