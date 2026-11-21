"""E-0003 (OD-0170): an AUD investor's 60% unhedged US equity, 40% in AUD cash, USD bills or Treasuries.

Monthly, from retained RBA data, so from 2011, with no 2008. AUD cash is the RBA Cash Rate TRI, by level.
USD sleeves are translated under RA 4.1 on H.10's noon New York rate. `retained` reads the newest F1 receipt
from the evidence store, read-only. `run` evaluates. Values go only to reports/ for the owner; stdout and
summary.json hold counts and pass or fail. Descriptive: no recommendation or forecast, and no consumer use.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import zipfile
from bisect import bisect_right
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal
from itertools import pairwise
from pathlib import Path
from typing import Any

import numpy as np

import e0002_aud as aud_tool
import eodhd_eval as ev
from hio.contracts.observation import parse_instant
from hio.contracts.rights import Operation
from hio.contracts.temporal import KnowledgeMode
from hio.library.numeric import CTX
from hio.portfolio import fixed_allocation as fa
from hio.rights.gate import RightsGate
from hio.sources.datasets import MalformedPayload, parse_rba_f1
from hio.storage.objectstore import LocalObjectStore
from research_reader import Pin, read_panel

RBA_SOURCE = "rba.cash_rate_tri"
RBA_PUBLICATION = "rba.f1"
TRI_SERIES = "FIRMMCTRI"
MAX_STALE_DAYS = 5
SLEEVES = ("equity", "bills", "treasury", "cash")
PORTFOLIOS = {
    "aud_cash": {"equity": 0.6, "cash": 0.4},
    "usd_bills": {"equity": 0.6, "bills": 0.4},
    "us_treasury": {"equity": 0.6, "treasury": 0.4},
}
EFFECTS = {
    "cash_rate_and_currency": ("aud_cash", "usd_bills"),
    "treasury_duration": ("usd_bills", "us_treasury"),
    "total": ("aud_cash", "us_treasury"),
}
WINDOWS = {
    "full": (date.min, date.max),
    "before_2020": (date.min, date(2019, 12, 31)),
    "from_2020": (date(2019, 12, 31), date.max),
    "q1_2020": (date(2019, 12, 31), date(2020, 3, 31)),
    "2022": (date(2021, 12, 31), date(2022, 12, 31)),
}
EARLIER_HISTORY_WINDOWS = ("full", "q1_2020", "2022")
EARLIER_HISTORY_DRAWDOWN = 0.02
NOTICES = (
    "Source: Reserve Bank of Australia. No endorsement by the RBA is implied.",
    aud_tool.NOTICE,
    ev.NOTICE,
)


def weights_vector(name: str) -> fa.Floats:
    return np.array([PORTFOLIOS[name].get(s, 0.0) for s in SLEEVES], dtype=np.float64)


def parse_tri(body: bytes) -> dict[date, Decimal]:
    try:
        parsed = parse_rba_f1({TRI_SERIES: "tri"})(body)
    except MalformedPayload as exc:
        raise ev.Stop("the F1 receipt doesn't hold the Cash Rate TRI") from exc
    levels = {row.valid_time: row.value for row in parsed.rows}
    if not levels or min(levels.values()) <= 0:
        raise ev.Stop("no usable TRI level")
    return levels


def level_on(levels: Mapping[date, Decimal], ordered: Sequence[date], day: date) -> Decimal:
    """The latest level on or before `day`. Too stale stops, and nothing is interpolated."""
    index = bisect_right(ordered, day) - 1
    if index < 0 or (day - ordered[index]).days > MAX_STALE_DAYS:
        raise ev.Stop(f"no TRI level within {MAX_STALE_DAYS} days of {day}")
    return levels[ordered[index]]


def common_months(months: Sequence[date], first_tri: date) -> list[int]:
    """The same window for every allocation: month ends from the first with a TRI level on or before it."""
    return [i for i, day in enumerate(months) if day >= first_tri]


def cash_returns(months: Sequence[date], levels: Mapping[date, Decimal]) -> fa.Floats:
    ordered = sorted(levels)
    marks = [level_on(levels, ordered, day) for day in months]
    return np.array(
        [float(CTX.subtract(CTX.divide(b, a), Decimal(1))) for a, b in pairwise(marks)],
        dtype=np.float64,
    )


def matrix(usd: fa.Floats, sleeves: Sequence[str], s: fa.Floats, cash: fa.Floats) -> fa.Floats:
    """AUD returns: equity, bills and Treasuries translated; cash already in AUD."""
    index = {
        "equity": sleeves.index("equity"),
        "bills": sleeves.index("cash"),
        "treasury": sleeves.index("treasury"),
    }
    columns = [(1 + usd[:, index[x]]) * (1 + s) - 1 for x in ("equity", "bills", "treasury")]
    return np.column_stack((*columns, cash))


def bills_against_cash(usd_bills: fa.Floats, s: fa.Floats, cash: fa.Floats) -> dict[str, float]:
    """Compounded AUD return of USD bills less AUD cash, split into the rate gap, the currency move and the
    cross term left. So the combined effect is shown, and its parts labelled as such."""
    bills_aud = float(np.prod((1 + usd_bills) * (1 + s)) - 1)
    bills_usd, currency = float(np.prod(1 + usd_bills) - 1), float(np.prod(1 + s) - 1)
    cash_total = float(np.prod(1 + cash) - 1)
    return {
        "bills_in_aud": bills_aud,
        "aud_cash": cash_total,
        "difference": bills_aud - cash_total,
        "rate_gap": bills_usd - cash_total,
        "currency": currency,
        "cross": bills_aud - bills_usd - currency,
    }


def evaluate(
    months: Sequence[date],
    returns: fa.Floats,
    usd_bills: fa.Floats,
    s: fa.Floats,
    windows: Mapping[str, tuple[date, date]] = WINDOWS,
) -> dict[str, Any]:
    results: dict[str, Any] = {"windows": {}, "bootstrap": {}}
    for name, (start, end) in windows.items():
        kept = [i for i in range(returns.shape[0]) if start <= months[i] and months[i + 1] <= end]
        if len(kept) < 3:
            results["windows"][name] = {"available": False}
            continue
        dates = [months[kept[0]], *(months[i + 1] for i in kept)]
        part = returns[kept]
        stats = {p: aud_tool._path_stats(dates, part @ weights_vector(p)) for p in PORTFOLIOS}
        results["windows"][name] = {
            "available": True,
            "start": dates[0].isoformat(),
            "end": dates[-1].isoformat(),
            "months": len(kept),
            "portfolios": stats,
            "effects": {
                effect: {
                    m: stats[b][m] - stats[a][m] for m in ("annualised_return", "volatility", "max_drawdown")
                }
                for effect, (a, b) in EFFECTS.items()
            },
            "bills_against_cash": bills_against_cash(
                usd_bills[kept], s[kept], part[:, SLEEVES.index("cash")]
            ),
            "correlations": np.corrcoef(part, rowvar=False).tolist(),
        }
    for effect, (a, b) in EFFECTS.items():
        results["bootstrap"][effect] = {}
        for size in ev.BLOCKS:
            boot = fa.paired_block_bootstrap(
                returns,
                weights_vector(a),
                weights_vector(b),
                block_months=size,
                replications=ev.REPLICATIONS,
                seed=ev.SEED,
            )
            results["bootstrap"][effect][str(size)] = {
                m: vars(getattr(boot, m)) for m in ("volatility", "annualised_return", "max_drawdown")
            }
    return results


def earlier_history_indicated(results: Mapping[str, Any]) -> bool:
    """The pre-registered test: the cash-rate and currency effect moves maximum drawdown by 2 "
    "points or more."""
    for name in EARLIER_HISTORY_WINDOWS:
        window = results["windows"][name]
        if window["available"]:
            size = abs(window["effects"]["cash_rate_and_currency"]["max_drawdown"])
            if size >= EARLIER_HISTORY_DRAWDOWN:
                return True
    return False


def interval_classes(results: Mapping[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    """Per effect and metric, which block lengths' intervals exclude zero, and the class that follows. Counts
    and block lengths only, so it's safe for stdout."""
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for effect, blocks in results["bootstrap"].items():
        if not blocks:
            raise ev.Stop(f"no block lengths for {effect}")
        out[effect] = {}
        for m in ("volatility", "annualised_return", "max_drawdown"):
            excludes = {
                int(size) for size, block in blocks.items() if not block[m]["low"] <= 0 <= block[m]["high"]
            }
            spans = {int(size) for size in blocks} - excludes
            kind = "mixed" if excludes and spans else "distinguished" if excludes else "not_distinguished"
            out[effect][m] = {"class": kind, "excludes_zero": sorted(excludes), "spans_zero": sorted(spans)}
    return out


def verdict_words(entry: Mapping[str, Any]) -> str:
    """ "Every block length" is said only when it's true; a mixed result names the lengths on each side."""
    if entry["class"] == "not_distinguished":
        return "not distinguished"
    if entry["class"] == "distinguished":
        return "distinguished at every block length"
    excludes = ", ".join(map(str, entry["excludes_zero"]))
    spans = ", ".join(map(str, entry["spans_zero"]))
    return f"mixed: distinguished at {excludes}-month blocks, not at {spans}-month blocks"


def conclusion(results: Mapping[str, Any]) -> list[str]:
    """Built from the pre-registered tests only, so it reads the same to anyone who holds the same results."""
    classes = interval_classes(results)

    def verdict(effect: str) -> str:
        metrics = ("annualised_return", "volatility", "max_drawdown")
        return "; ".join(f"{m.replace('_', ' ')}: {verdict_words(classes[effect][m])}" for m in metrics)

    if earlier_history_indicated(results):
        earlier = (
            "**indicated by the pre-registered test.** The cash-rate and currency effect moved maximum "
            "drawdown by 2 points or more in a named window, so the missing 2008 matters. That prompts "
            "your own rights decision."
        )
    else:
        earlier = (
            "**not indicated by the pre-registered test.** The cash-rate and currency effect moved maximum "
            "drawdown by under 2 points in every named window. This says nothing about 2008 itself."
        )
    return [
        "\n## Conclusion\n",
        f"- **Cash rate and currency (USD bills against AUD cash).** {verdict('cash_rate_and_currency')}.",
        f"- **Treasury duration (Treasuries against USD bills).** {verdict('treasury_duration')}.",
        f"- **Total (Treasuries against AUD cash).** {verdict('total')}.",
        "- **Establishes:** what these hypothetical sleeves did from 2011, separating currency and rate "
        "from duration. Read the direction and size from the tables above.",
        "- **Doesn't establish:** anything about 2008, a forecast, or a recommendation. About five "
        "non-overlapping three-year periods, few stress episodes, one history; intervals rest on it.",
        "- **Unresolved:** SPY, IEF and BIL have no independent check; EODHD's prices; costs, tax, hedging.",
        f"- **Earlier AUD cash history:** {earlier}",
    ]


def render(results: Mapping[str, Any]) -> str:
    lines = [
        "# E-0003: for the owner and HIO's agents. Licensed-derived: don't commit or share.",
        "",
        "AUD, monthly, unhedged, no costs or tax. Equity is SPY; USD bills are BIL, a bill ETF; "
        "Treasuries are IEF.",
        "**2008 isn't in the sample:** retained RBA cash data starts in 2011. Hypothetical and "
        "descriptive: no",
        "recommendation or forecast. " + " ".join(NOTICES),
    ]
    for name, window in results["windows"].items():
        lines.append(f"\n## Window: {name}\n")
        if not window["available"]:
            lines.append("Not available.")
            continue
        lines.append(f"{window['start']} to {window['end']}, {window['months']} months.\n")
        lines.append(
            "| 60% equity with 40% in | Wealth | Return p.a. | Vol | Max drawdown | Recovery | Under "
            "water (days) |"
        )
        lines.append("|---|---:|---:|---:|---:|---|---:|")
        for p, d in window["portfolios"].items():
            lines.append(
                f"| {p} | {d['final_wealth']:.3f} | {d['annualised_return']:.2%} | {d['volatility']:.2%} | "
                f"{d['max_drawdown']:.2%} | {d['recovery'] or 'not recovered'} | "
                f"{d['longest_underwater_days']} |"
            )
        lines.append("\n| Effect | Return p.a. | Vol | Max drawdown |\n|---|---:|---:|---:|")
        for effect, d in window["effects"].items():
            lines.append(
                f"| {effect} | {d['annualised_return']:+.2%} | {d['volatility']:+.2%} | "
                f"{d['max_drawdown']:+.2%} |"
            )
        b = window["bills_against_cash"]
        lines.append(
            f"\nUSD bills in AUD against AUD cash, compounded: {b['difference']:+.2%} = rate gap "
            f"{b['rate_gap']:+.2%}, "
            f"currency {b['currency']:+.2%}, cross {b['cross']:+.2%}."
        )
    lines.append("\n## Paired block bootstrap, later minus earlier sleeve (this history only)\n")
    lines.append("| Effect | Block | Metric | Observed | 2.5% | 97.5% |\n|---|---:|---|---:|---:|---:|")
    for effect, blocks in results["bootstrap"].items():
        for block, metrics in blocks.items():
            for m, v in metrics.items():
                lines.append(
                    f"| {effect} | {block} | {m} | {v['estimate']:+.2%} | {v['low']:+.2%} | {v['high']:+.2%} "
                    f"|"
                )
    lines += conclusion(results)
    return "\n".join(lines) + "\n"


def retained(root: Path, environ: Mapping[str, str]) -> dict[str, Any]:
    """Read the newest F1 receipt from the evidence store, read-only."""
    from azure.identity import DefaultAzureCredential

    from hio.contracts.layout import receipt_key
    from hio.storage.azure_blob import AzureBlobBackend, container_client
    from hio.storage.blobstore import BlobObjectStore

    ev.check_root(root)
    gate = ev.make_gate()
    gate.authorise(Operation.STORE_RAW, [RBA_SOURCE])
    source = BlobObjectStore(
        AzureBlobBackend(
            container_client(
                environ["HIO_STORAGE_ACCOUNT_URL"], environ["HIO_STORAGE_CONTAINER"], DefaultAzureCredential()
            )
        )
    )
    records = sorted(source.list(f"catalogue/captures/{RBA_PUBLICATION}/"))
    if not records:
        raise ev.Stop("no retained F1 receipt")
    record = json.loads(source.get(records[-1]))
    body = source.get(
        receipt_key(RBA_PUBLICATION, parse_instant(record["captured_at"]), record["receipt_id"])
    )
    digest = hashlib.sha256(body).hexdigest()
    if digest != record["receipt_id"]:
        raise ev.Stop("the receipt doesn't match its id")
    raw = root / "raw"
    raw.mkdir(mode=0o700, exist_ok=True)
    ev.private_write(raw / "rba_f1.csv", body)
    manifest = {
        "publication": RBA_PUBLICATION,
        "receipt_id": digest,
        "captured_at": record["captured_at"],
        "bytes": len(body),
        "notice": NOTICES[0],
    }
    ev.private_write(raw / "manifest.json", (json.dumps(manifest, indent=1, sort_keys=True) + "\n").encode())
    return manifest


def run(root: Path, e0002_root: Path, h10_root: Path, snapshot: str, *, gate: RightsGate) -> dict[str, Any]:
    ev.check_root(root)
    ev.check_root(e0002_root)
    for source in (RBA_SOURCE, aud_tool.H10_SOURCE, ev.SOURCE_ID):
        gate.authorise(Operation.BUILD, [source])
    manifest = json.loads((root / "raw" / "manifest.json").read_text())
    body = (root / "raw" / "rba_f1.csv").read_bytes()
    if hashlib.sha256(body).hexdigest() != manifest["receipt_id"]:
        raise ev.Stop("the retained F1 bytes don't match their manifest")
    levels = parse_tri(body)
    summary = json.loads((e0002_root / "summary.json").read_text())
    if summary.get("snapshot") != snapshot or not summary.get("comparison_ran"):
        raise ev.Stop("the USD run for this snapshot hasn't passed")
    hashes = summary["releases"]
    core = json.loads(
        (
            e0002_root / "store" / "releases" / ev.SLEEVES["equity"][1] / hashes["equity"] / "manifest.json"
        ).read_text()
    )
    panel, _ = read_panel(
        LocalObjectStore(e0002_root / "store"),
        [Pin(s, ev.SLEEVES[s][1], sha) for s, sha in hashes.items()],
        mode=KnowledgeMode.LATEST,
        cutoff=parse_instant(core["knowledge_cutoff"]),
        gate=gate,
    )
    with zipfile.ZipFile(h10_root / "FRB_h10_xml.zip") as archive:
        rates, _ = aud_tool.parse_h10(archive.read("H10_data.xml"))
    all_months, all_usd = aud_tool.monthly_usd(panel)
    keep = common_months(all_months, min(levels))
    months = [all_months[i] for i in keep]
    usd = all_usd[keep[0] : keep[-1]]
    _, s, facts = aud_tool.translate(months, usd, rates)
    cash = cash_returns(months, levels)
    returns = matrix(usd, panel.sleeves, s, cash)
    results = evaluate(months, returns, usd[:, panel.sleeves.index("cash")], s)
    reports = root / "reports"
    reports.mkdir(mode=0o700, exist_ok=True)
    ev.private_write(reports / "owner-report.md", render(results).encode())
    ev.private_write(
        reports / "owner-values.json", (json.dumps(results, indent=1, sort_keys=True) + "\n").encode()
    )
    out = {
        "first_month": months[0].isoformat(),
        "last_month": months[-1].isoformat(),
        "months": int(returns.shape[0]),
        "tri_levels": len(levels),
        "tri_first": min(levels).isoformat(),
        "receipt": manifest["receipt_id"],
        **{k: facts[k] for k in ("rates_not_on_the_day", "oldest_rate_days")},
        "windows_available": {k: v["available"] for k, v in results["windows"].items()},
        "interval_classes": interval_classes(results),
        "earlier_history_indicated": earlier_history_indicated(results),
    }
    ev.private_write(root / "summary.json", (json.dumps(out, indent=1, sort_keys=True) + "\n").encode())
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["retained", "run"])
    parser.add_argument("--root", type=Path, default=Path.home() / ".hio-research" / "E-0003")
    parser.add_argument("--e0002", type=Path, default=Path.home() / ".hio-research" / "E-0002-eodhd")
    parser.add_argument("--h10", type=Path, default=Path.home() / ".hio-research" / "H10")
    parser.add_argument("--snapshot", default="s2")
    args = parser.parse_args(argv)
    try:
        ev.code_commit()
        if args.command == "retained":
            out = retained(args.root, os.environ)
            out = {k: out[k] for k in ("publication", "bytes", "captured_at")}
        else:
            out = run(args.root, args.e0002, args.h10, args.snapshot, gate=ev.make_gate())
    except Exception as exc:
        print(f"stopped: {type(exc).__name__}: {exc if isinstance(exc, ev.Stop) else ''}", file=sys.stderr)
        return 2
    print(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
