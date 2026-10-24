"""Rights-gate contract (rights standard §3). The implementation is in hio.rights.

Every operation that touches source data takes a gate and calls it *before* doing anything, so
a refusal leaves no partial output.
"""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum
from typing import Protocol


class Operation(StrEnum):
    FETCH = "fetch"
    STORE_RAW = "store_raw"
    BUILD = "build"
    STORE_DERIVED = "store_derived"
    REBUILD = "rebuild"
    PUBLISH = "publish"


class RightsRefused(Exception):
    def __init__(self, operation: Operation, reasons: list[str]) -> None:
        self.operation = operation
        self.reasons = reasons
        super().__init__(f"{operation.value} refused: " + "; ".join(reasons))


class RightsGate(Protocol):
    def authorise(
        self, operation: Operation, source_ids: Iterable[str], consumer_class: str | None = None
    ) -> None:
        """Return if every source grants every permission the operation needs; else raise
        RightsRefused."""
        ...
