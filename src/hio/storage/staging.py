"""One way to stage a group of writes for any object store (T-0009, OD-0065).

The local store has an all-or-nothing journalled transaction. A cloud object store has none, so it
supplies its own `staged()` with an explicit commit order and idempotent resume. Callers use
`staged_writes(store)`; for the local store this is exactly `StagedWrites(store)`.
"""

from __future__ import annotations

from typing import Any

from hio.storage.objectstore import StagedWrites


def staged_writes(store: Any) -> Any:
    factory = getattr(store, "staged", None)
    return factory() if factory is not None else StagedWrites(store)
