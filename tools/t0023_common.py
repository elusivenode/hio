"""What T-0023's corroboration tools share (OD-0178): the frozen panel, read and checked, and a comparison
with one thing changed. Values stay under ~/.hio-research/T-0023; callers print only hashes, counts and
classes.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from itertools import pairwise
from pathlib import Path
from typing import Any

import numpy as np

import e0003_aud_cash as base
import e0003_extended as ext
import e0003_panel as panel_tool
import eodhd_eval as ev
from hio.portfolio import fixed_allocation as fa


@dataclass(frozen=True)
class FrozenPanel:
    months: list[date]
    returns: fa.Floats  # in AUD, columns as base.SLEEVES
    usd_bills: fa.Floats
    s: fa.Floats


def parse_panel(text: str) -> FrozenPanel:
    rows = list(csv.DictReader(text.splitlines()))
    if not rows:
        raise ev.Stop("an empty panel")
    months = [
        date.fromisoformat(rows[0]["period_start"]),
        *(date.fromisoformat(r["period_end"]) for r in rows),
    ]
    returns = np.array([[float(r[c]) for c in base.SLEEVES] for r in rows], dtype=np.float64)
    usd_bills = np.array([float(r["usd_bills"]) for r in rows], dtype=np.float64)
    s = np.array([float(r["fx_return"]) for r in rows], dtype=np.float64)
    return FrozenPanel(months, returns, usd_bills, s)


def load_frozen(root: Path, panel_id: str | None = panel_tool.FROZEN_PANEL_ID) -> tuple[FrozenPanel, Path]:
    """The newest rebuild whose id is the frozen one, with its panel text checked against its own record."""
    for run_dir in sorted((root / "runs").glob("*"), reverse=True):
        if not (run_dir / "run.json").is_file():
            continue
        record = json.loads((run_dir / "run.json").read_text())
        if record["panel_id"] != panel_id:
            continue
        text = (run_dir / "panel.csv").read_bytes()
        if hashlib.sha256(text).hexdigest() != record["panel_sha256"]:
            raise ev.Stop(f"{run_dir.name}'s panel doesn't match its record")
        return parse_panel(text.decode()), run_dir
    raise ev.Stop("no rebuild holds the frozen panel id")


def usd_columns(panel: FrozenPanel) -> dict[str, fa.Floats]:
    """Each USD sleeve's USD return, undoing RA 4.1. Bills are stored; the others are recovered from AUD."""
    equity = (1 + panel.returns[:, base.SLEEVES.index("equity")]) / (1 + panel.s) - 1
    treasury = (1 + panel.returns[:, base.SLEEVES.index("treasury")]) / (1 + panel.s) - 1
    return {"equity": equity, "bills": panel.usd_bills, "treasury": treasury}


def with_changes(
    panel: FrozenPanel,
    *,
    usd: Mapping[str, fa.Floats] | None = None,
    cash: fa.Floats | None = None,
    s: fa.Floats | None = None,
) -> FrozenPanel:
    """The panel with named USD sleeves, AUD cash or the FX return replaced, with RA 4.1 applied again."""
    columns = usd_columns(panel) | dict(usd or {})
    fx = panel.s if s is None else s
    aud_cash = panel.returns[:, base.SLEEVES.index("cash")] if cash is None else cash
    for name, values in [*columns.items(), ("cash", aud_cash), ("fx", fx)]:
        if len(values) != panel.returns.shape[0]:
            raise ev.Stop(f"{name} doesn't cover the panel")
    returns = np.column_stack([*((1 + columns[x]) * (1 + fx) - 1 for x in base.SLEEVES[:3]), aud_cash])
    return replace(panel, returns=returns, usd_bills=columns["bills"], s=fx)


def classes_of(panel: FrozenPanel) -> dict[str, Any]:
    return base.interval_classes(
        base.evaluate(panel.months, panel.returns, panel.usd_bills, panel.s, ext.WINDOWS)
    )


def class_changes(frozen: Mapping[str, Any], other: Mapping[str, Any]) -> list[str]:
    """Which effect and metric pairs change class. Empty means the conclusion holds under this sensitivity."""
    return [
        f"{effect}.{metric}: {frozen[effect][metric]['class']} -> {other[effect][metric]['class']}"
        for effect in sorted(frozen)
        for metric in sorted(frozen[effect])
        if frozen[effect][metric]["class"] != other[effect][metric]["class"]
    ]


def compound_between(periods: Sequence[tuple[date, date, float]], months: Sequence[date]) -> fa.Floats:
    """Daily period returns compounded over each pair of month ends. A gap in coverage stops."""
    out, i = [], 0
    ordered = sorted(periods)
    for a, b in pairwise(months):
        while i < len(ordered) and ordered[i][1] <= a:
            i += 1
        if i == len(ordered) or ordered[i][0] > a:
            raise ev.Stop(f"no period starts by {a}")
        wealth, last = 1.0, a
        while i < len(ordered) and ordered[i][1] <= b:
            if ordered[i][0] != last:
                raise ev.Stop(f"a gap in coverage at {last}")
            wealth *= 1 + ordered[i][2]
            last = ordered[i][1]
            i += 1
        if last != b:
            raise ev.Stop(f"coverage stops short of {b}")
        out.append(wealth - 1)
    return np.array(out, dtype=np.float64)


def new_output(root: Path, step: str, commit: str, now: datetime | None = None) -> Path:
    """A new private directory for one tool's run. Nothing is overwritten."""
    stamp = (now or datetime.now(UTC)).strftime("%Y%m%dT%H%M%SZ")
    out = root / "corroboration" / step / f"{stamp}-{commit[:8]}"
    out.mkdir(mode=0o700, parents=True)
    return out


def write_outputs(out: Path, report: str, summary: Mapping[str, Any]) -> None:
    ev.private_write(out / "report.md", report.encode())
    ev.private_write(out / "summary.json", (json.dumps(summary, indent=1, sort_keys=True) + "\n").encode())
