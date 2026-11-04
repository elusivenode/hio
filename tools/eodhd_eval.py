"""The one-month EODHD evaluation (T-0022, OD-0162, OD-0163): snapshots, profile, returns, and E-0002.

`whoami` prints the plan's name. `fetch --snapshot NAME` retains one snapshot of the raw responses. `run`
profiles and evaluates them. All of it runs locally under a rights record that denies agent use, so stdout and
summary.json hold only counts, hashes and pass or fail. Values go to reports/ under --root, for the owner. The
key comes from the HIO key vault, and never enters a file, a log, a manifest or an error. A CI environment
refuses. Qualification says nothing about consumer use, and no series here is a validated factor.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from itertools import pairwise
from pathlib import Path
from typing import Any

import numpy as np

from hio.contracts.canonical import canonical_json, instant_str
from hio.contracts.layout import capture_record_key, receipt_key
from hio.contracts.observation import Receipt, parse_instant
from hio.contracts.rights import Operation
from hio.contracts.status import Status
from hio.contracts.temporal import KnowledgeMode
from hio.library.numeric import CTX
from hio.library.vehicle_return import VehicleDay, VehiclePeriod, vehicle_series
from hio.portfolio import fixed_allocation as fa
from hio.publish.release import make_release, render_csv, write_release
from hio.publish.status import append_status
from hio.rights.gate import GateContext, RightsGate
from hio.rights.model import propagate
from hio.rights.register import load_genuine
from hio.storage.objectstore import LocalObjectStore
from research_reader import Pin, read_panel

REPO = Path(__file__).resolve().parent.parent
SOURCE_ID = "eodhd.personal_evaluation"
BASE = "https://eodhd.com/api"
KEY_VAULT_SUBSCRIPTION = "hnf-prod"
KEY_VAULT_SECRET = "eodhd-api-key"
ETFS = {
    "SPY.US": "USD",
    "VTI.US": "USD",
    "IEF.US": "USD",
    "BIL.US": "USD",
    "VAS.AU": "AUD",
    "IVV.AU": "AUD",
    "BGBL.AU": "AUD",
}
FOREX = "AUDUSD.FOREX"
EXCHANGES = ("US", "AU")
WORKSPACE_PARTS = ("raw", "reports", "store", "reference")
SNAPSHOT_NAME = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
KINDS = ("eod", "div", "splits")
MAX_REQUESTS_PER_SNAPSHOT = 40
PAUSE_SECONDS = 0.5
SLEEVES = {
    "equity": ("SPY.US", "equity.us.spy.market_total_return"),
    "treasury": ("IEF.US", "rates.us.ief.market_total_return"),
    "cash": ("BIL.US", "cash.us.bil.market_total_return"),
}
SPEC_VERSION = "0.1.0"
ALLOCATIONS = {
    "100_equity": {"equity": 1.0, "treasury": 0.0, "cash": 0.0},
    "60_equity_40_cash": {"equity": 0.6, "treasury": 0.0, "cash": 0.4},
    "60_equity_40_treasury": {"equity": 0.6, "treasury": 0.4, "cash": 0.0},
}
WINDOWS = {
    "full": (date.min, date.max),
    "before_2020": (date.min, date(2019, 12, 31)),
    "from_2020": (date(2019, 12, 31), date.max),
    "2008": (date(2007, 12, 31), date(2008, 12, 31)),
    "q1_2020": (date(2019, 12, 31), date(2020, 3, 31)),
    "2022": (date(2021, 12, 31), date(2022, 12, 31)),
}
SEED, REPLICATIONS, BLOCKS = 20260002, 10_000, (12, 6, 24)
BP = Decimal("0.0001")
MAX_GAP_DAYS = 7
NOTICE = "Data: EODHD, under the owner's personal plan. No endorsement is implied. Not for redistribution."
LIMITATION = (
    "Exploratory: reconstructed(T), a market-price return of a named fund, no trading costs or tax. Internal "
    "consistency isn't validation. Results for the owner only; no SMSF use."
)
Getter = Callable[[str], tuple[int, bytes]]


class Stop(ValueError):
    """Evidence integrity failed, or a limit was reached. Nothing further runs."""


def make_gate(environ: Mapping[str, str] = os.environ) -> RightsGate:
    """A CI or cloud host needs external_processing, which this record denies."""
    external = any(environ.get(name) for name in ("CI", "GITHUB_ACTIONS", "AZURE_HTTP_USER_AGENT"))
    return RightsGate(
        load_genuine(REPO / "registers" / "sources.yaml"), GateContext(on_external_host=external)
    )


def vault_key(root: Path) -> str:
    """The key from the HIO vault (OD-0164), by the signed-in owner's identity. Nothing from az is shown."""
    name = root / "vault-name"
    if not name.is_file():
        raise Stop("no vault name in the workspace")
    done = subprocess.run(
        [
            "az",
            "keyvault",
            "secret",
            "show",
            "--subscription",
            KEY_VAULT_SUBSCRIPTION,
            "--vault-name",
            name.read_text().strip(),
            "-n",
            KEY_VAULT_SECRET,
            "--query",
            "value",
            "-o",
            "tsv",
        ],
        capture_output=True,
        text=True,
    )
    if done.returncode != 0 or not done.stdout.strip():
        raise Stop("the EODHD key could not be read from the vault")
    return done.stdout.strip()


def http_getter(key: str) -> Getter:
    def get(path_and_query: str) -> tuple[int, bytes]:
        separator = "&" if "?" in path_and_query else "?"
        token = urllib.parse.quote(key, safe="")
        request = urllib.request.Request(
            f"{BASE}{path_and_query}{separator}api_token={token}",
            headers={"User-Agent": "HIO-research/0.1 (personal evaluation)"},
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, b""
        except urllib.error.URLError as exc:
            raise Stop(f"network error: {type(exc.reason).__name__}") from None

    return get


def requests_for() -> list[tuple[str, str, str]]:
    out = []
    for symbol in ETFS:
        out.append((symbol, "eod", f"/eod/{symbol}?fmt=json&period=d"))
        out.append((symbol, "div", f"/div/{symbol}?fmt=json"))
        out.append((symbol, "splits", f"/splits/{symbol}?fmt=json"))
    out.append((FOREX, "eod", f"/eod/{FOREX}?fmt=json&period=d"))
    for exchange in EXCHANGES:  # the listing's quote currency (F-REVIEW-2026-11-04-t0022-1-1)
        out.append((f"EXCHANGE.{exchange}", "symbols", f"/exchange-symbol-list/{exchange}?fmt=json"))
    return out


def check_root(root: Path) -> None:
    """The workspace must be outside the repository and private, and everything created under it stays private
    (F-REVIEW-2026-11-04-t0022-1-4)."""
    resolved = root.resolve()
    if resolved == REPO or REPO in resolved.parents:
        raise Stop("--root must lie outside the repository")
    if not resolved.is_dir():
        raise Stop("--root must be an existing directory")
    if resolved.stat().st_mode & 0o077:
        raise Stop("--root must be mode 700")
    os.umask(0o077)
    for (
        name
    ) in WORKSPACE_PARTS:  # a link or an open part would carry data out of the workspace (VERIFY ...-1-1)
        part = root / name
        if part.is_symlink():
            raise Stop(f"{name} must not be a link")
        if part.exists() and part.stat().st_mode & 0o077:
            raise Stop(f"{name} must be private")


def private_write(path: Path, data: bytes) -> None:
    """Private, and always a new file swapped into place, so no link of any kind is written through."""
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")  # mode 600
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(data)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def make_private(path: Path) -> None:
    """The object store marks its files world-readable and read-only; here they stay read-only and private."""
    for item in path.rglob("*"):
        item.chmod(0o700 if item.is_dir() else 0o400)


def snapshot_dir(root: Path, snapshot: str) -> Path:
    """A snapshot is one safe name directly under raw/ (F-REVIEW-2026-11-04-t0022-1-3)."""
    if not SNAPSHOT_NAME.fullmatch(snapshot):
        raise Stop("a snapshot name must be letters, digits, hyphens or underscores")
    raw = root.resolve() / "raw"
    target = raw / snapshot
    if raw.is_symlink() or target.is_symlink() or raw.resolve() != raw or target.resolve().parent != raw:
        raise Stop("a snapshot must stay under raw/ in the workspace")
    return target


def quote_currency(rows: Sequence[Mapping[str, Any]], symbol: str) -> str | None:
    """The listing's own quote currency, or None if the listing doesn't settle it."""
    code = symbol.rsplit(".", 1)[0]
    found = {str(row.get("Currency")) for row in rows if row.get("Code") == code and row.get("Currency")}
    return found.pop() if len(found) == 1 else None


def fetch(
    root: Path, snapshot: str, *, gate: RightsGate, commit: str, get: Getter, pause: float = PAUSE_SECONDS
) -> dict:
    """One snapshot. It stops at the first surprise, keeps what it has, and never overwrites a snapshot."""
    check_root(root)
    gate.authorise(Operation.FETCH, [SOURCE_ID])
    gate.authorise(Operation.STORE_RAW, [SOURCE_ID])
    target = snapshot_dir(root, snapshot)
    if target.exists():
        raise Stop(f"snapshot {snapshot} already exists")
    planned = requests_for()
    if len(planned) > MAX_REQUESTS_PER_SNAPSHOT:
        raise Stop("too many requests")
    target.mkdir(parents=True, mode=0o700)
    files, stopped = [], None
    for index, (symbol, kind, request) in enumerate(planned):
        if index:
            time.sleep(pause)
        at = datetime.now(UTC).isoformat()
        status, body = get(request)
        if status != 200:
            stopped = f"{symbol} {kind}: HTTP {status}"
            break
        try:
            json.loads(body)
        except ValueError:
            stopped = f"{symbol} {kind}: not JSON"
            break
        name = f"{symbol}.{kind}.json"
        private_write(target / name, body)
        files.append(
            {
                "symbol": symbol,
                "kind": kind,
                "request": request,  # never the key
                "retrieved_at": at,
                "path": f"raw/{snapshot}/{name}",
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
            }
        )
    manifest = {
        "evaluation": "T-0022",
        "source_id": SOURCE_ID,
        "snapshot": snapshot,
        "notice": NOTICE,
        "code_commit": commit,
        "files": files,
        "stopped": stopped,
    }
    private_write(target / "manifest.json", (json.dumps(manifest, indent=1, sort_keys=True) + "\n").encode())
    return manifest


def load_snapshot(root: Path, snapshot: str) -> dict[str, Any]:
    manifest = json.loads((snapshot_dir(root, snapshot) / "manifest.json").read_text())
    if manifest["stopped"] is not None:
        raise Stop(f"snapshot {snapshot} stopped early: {manifest['stopped']}")
    for entry in manifest["files"]:
        if hashlib.sha256((root / entry["path"]).read_bytes()).hexdigest() != entry["sha256"]:
            raise Stop(f"retained bytes don't match the manifest: {entry['path']}")
    return manifest


def _read(root: Path, manifest: Mapping[str, Any], symbol: str, kind: str) -> list[dict[str, Any]]:
    entry = next(f for f in manifest["files"] if f["symbol"] == symbol and f["kind"] == kind)
    return json.loads((root / entry["path"]).read_bytes(), parse_float=Decimal, parse_int=Decimal)


def parse_split(text: str) -> Decimal:
    new, old = str(text).split("/")
    factor = CTX.divide(Decimal(new), Decimal(old))
    if factor <= 0:
        raise ValueError("a split factor must be positive")
    return factor


@dataclass
class Series:
    symbol: str
    periods: list[VehiclePeriod]
    adjusted_returns: dict[date, Decimal]
    days: list[date]
    profile: dict[str, Any]
    qualified: dict[str, bool]


def analyse(
    symbol: str,
    expected_currency: str,
    listed_currency: str | None,
    eod: Sequence[Mapping[str, Any]],
    dividends: Sequence[Mapping[str, Any]],
    splits: Sequence[Mapping[str, Any]],
) -> Series:
    """Profile one fund and build its return, from raw closes and actions, not from its adjusted close."""
    counts: Counter = Counter()
    days = [date.fromisoformat(str(row["date"])) for row in eod]
    counts["rows"] = len(eod)
    counts["duplicate_dates"] = len(days) - len(set(days))
    counts["unordered_dates"] = sum(1 for a, b in pairwise(days) if b <= a)
    counts["non_positive_closes"] = sum(1 for row in eod if Decimal(row["close"]) <= 0)
    counts["missing_adjusted"] = sum(1 for row in eod if row.get("adjusted_close") is None)
    gaps = [(b - a).days for a, b in pairwise(days) if b > a]
    counts["gaps_over_7_days"] = sum(1 for g in gaps if g > MAX_GAP_DAYS)
    counts["weekday_dates_absent"] = sum(
        1
        for a, b in pairwise(days)
        if b > a
        for n in range(1, (b - a).days)
        if (a + timedelta(days=n)).weekday() < 5
    )
    counts["quote_currency_unconfirmed"] = int(listed_currency != expected_currency)
    identity_ok = bool(eod) and not (
        counts["quote_currency_unconfirmed"]
        or counts["duplicate_dates"]
        or counts["unordered_dates"]
        or counts["non_positive_closes"]
        or counts["gaps_over_7_days"]
    )
    if not identity_ok:
        return Series(symbol, [], {}, days, {"counts": dict(counts)}, {"Q1": False, "Q2": False, "Q3": False})

    observed = set(days)
    paid: dict[date, Decimal] = {}
    factors: dict[date, Decimal] = {}
    actions_ok = True

    def place(day: date) -> date | None:
        if day in observed:
            return day
        later = [d for d in days if d > day]
        if not later:
            return None
        counts["actions_moved_to_next_day"] += 1
        return later[0]

    for record in dividends:
        counts["distributions"] += 1
        raw = record.get("unadjustedValue")
        if raw is None:
            counts["distributions_missing_unadjusted"] += 1
            actions_ok = False
            continue
        currency = record.get("currency")
        if currency != expected_currency:
            counts["distributions_other_currency"] += 1
            actions_ok = False
        for field in ("paymentDate", "recordDate", "declarationDate"):
            counts[f"distributions_missing_{field}"] += int(not record.get(field))
        if record.get("value") is not None and Decimal(record["value"]) != Decimal(raw):
            counts["distributions_split_adjusted_value_differs"] += 1
        day = place(date.fromisoformat(str(record["date"])))
        if day is None:
            counts["actions_after_the_last_close"] += 1
            continue
        paid[day] = paid.get(day, Decimal(0)) + Decimal(raw)
    for record in splits:
        counts["splits"] += 1
        try:
            factor = parse_split(record["split"])
        except (ValueError, ArithmeticError, KeyError):
            counts["splits_unparseable"] += 1
            actions_ok = False
            continue
        day = place(date.fromisoformat(str(record["date"])))
        if day is None:
            counts["actions_after_the_last_close"] += 1
            continue
        factors[day] = CTX.multiply(factors.get(day, Decimal(1)), factor)

    bars = [
        VehicleDay(d, Decimal(row["close"]), paid.get(d, Decimal(0)), factors.get(d, Decimal(1)))
        for d, row in zip(days, eod, strict=True)
    ]
    periods = vehicle_series(bars)
    adjusted: dict[date, Decimal] = {}
    for (a, b), period in zip(pairwise(eod), periods, strict=True):
        if a.get("adjusted_close") and b.get("adjusted_close"):
            adjusted[period.end] = CTX.subtract(
                CTX.divide(Decimal(b["adjusted_close"]), Decimal(a["adjusted_close"])), Decimal(1)
            )
    compared = [abs(adjusted[p.end] - p.total_return) for p in periods if p.end in adjusted]
    within = sum(1 for g in compared if g <= BP)
    counts["internal_periods_compared"] = len(compared)
    counts["internal_periods_within_1bp"] = within
    # Which periods differ, and whether a factor-style adjustment explains them. A diagnostic only: it
    # compares EODHD with itself and changes no return. HIO's TR reinvests at the ex-date close (RA 3.1).
    for (a, b), period in zip(pairwise(bars), periods, strict=True):
        if period.end not in adjusted or abs(adjusted[period.end] - period.total_return) <= BP:
            continue
        key = "on_action_dates" if b.distribution or b.split_factor != 1 else "off_action_dates"
        counts[f"internal_differences_{key}"] += 1
        denominator = CTX.subtract(a.close, CTX.multiply(b.split_factor, b.distribution))
        if denominator > 0:
            factor_style = CTX.subtract(
                CTX.divide(CTX.multiply(b.split_factor, b.close), denominator), Decimal(1)
            )
            counts["internal_differences_explained_by_factor_formula"] += int(
                abs(adjusted[period.end] - factor_style) <= BP
            )
    # Every period is in the denominator: one without an adjusted close can't agree (F-...-t0022-1-2).
    counts["internal_periods_without_adjusted"] = len(periods) - len(compared)
    internal_ok = bool(periods) and Decimal(within) / Decimal(len(periods)) >= Decimal("0.99")
    by_year = Counter(str(record["date"])[:4] for record in dividends)
    return Series(
        symbol,
        periods,
        adjusted,
        days,
        {
            "counts": dict(counts),
            "first": days[0].isoformat(),
            "last": days[-1].isoformat(),
            "distributions_by_year": dict(sorted(by_year.items())),
        },
        {"Q1": True, "Q2": actions_ok, "Q3": internal_ok},
    )


def _agrees(vendor: Any, issuer: Decimal) -> bool:
    """Equal once the issuer's figure is rounded to the vendor's decimals, which is all the vendor carries."""
    if vendor is None:
        return False
    value = Decimal(vendor)
    return issuer.quantize(Decimal(1).scaleb(value.as_tuple().exponent)) == value


def check_reference(root: Path, symbol: str, dividends: Sequence[Mapping[str, Any]]) -> dict[str, int] | None:
    """Q5: the issuer's distributions, read by hand into reference/SYMBOL.csv, against the vendor's, as
    counts. A reference covering a shorter span counts the rest as extra, so read the counts with it."""
    path = root / "reference" / f"{symbol}.csv"
    if not path.is_file():
        return None
    issuer = {row["ex_date"]: Decimal(row["amount"]) for row in csv.DictReader(path.open())}
    vendor = {str(r["date"]): r.get("unadjustedValue") for r in dividends}
    both = issuer.keys() & vendor.keys()
    differs = sum(1 for d in both if not _agrees(vendor[d], issuer[d]))
    return {
        "issuer_rows": len(issuer),
        "matched": len(both) - differs,
        "amount_differs": differs,
        "missing_from_vendor": len(issuer.keys() - vendor.keys()),
        "only_in_vendor": len(vendor.keys() - issuer.keys()),
    }


def compare_snapshots(
    root: Path, first: Mapping[str, Any], second: Mapping[str, Any]
) -> dict[str, dict[str, int]]:
    """Q4: raw closes and distribution amounts changed between snapshots, as counts. Adjusted closes are
    expected to change, so they aren't compared."""
    out = {}
    for symbol in ETFS:
        old = {str(r["date"]): r["close"] for r in _read(root, first, symbol, "eod")}
        new = {str(r["date"]): r["close"] for r in _read(root, second, symbol, "eod")}
        old_d = {str(r["date"]): r.get("unadjustedValue") for r in _read(root, first, symbol, "div")}
        new_d = {str(r["date"]): r.get("unadjustedValue") for r in _read(root, second, symbol, "div")}
        out[symbol] = {
            "closes_changed": sum(1 for d in old.keys() & new.keys() if old[d] != new[d]),
            "closes_removed": len(old.keys() - new.keys()),
            "distributions_changed": sum(1 for d in old_d.keys() & new_d.keys() if old_d[d] != new_d[d]),
            "distributions_removed": len(old_d.keys() - new_d.keys()),
        }
    return out


def write_releases(
    root: Path,
    store: LocalObjectStore,
    manifest: Mapping[str, Any],
    series: Mapping[str, Series],
    *,
    gate: RightsGate,
    code: Mapping[str, str],
) -> tuple[dict[str, str], datetime]:
    """Each sleeve becomes a local exploratory release with real lineage, for the reader's checks."""
    cutoff = max(datetime.fromisoformat(f["retrieved_at"]) for f in manifest["files"]).astimezone(UTC)
    gate.authorise(Operation.BUILD, [SOURCE_ID])
    hashes = {}
    for sleeve, (symbol, factor) in SLEEVES.items():
        receipts = []
        for entry in (f for f in manifest["files"] if f["symbol"] == symbol):
            data = (root / entry["path"]).read_bytes()
            at = datetime.fromisoformat(entry["retrieved_at"]).astimezone(UTC)
            receipt = Receipt(entry["sha256"], SOURCE_ID, at, {"request": entry["request"]}, len(data))
            key = receipt_key(SOURCE_ID, at, entry["sha256"])
            if not store.exists(key):  # identical bytes, such as an empty list, are one receipt
                store.put(key, data)
            record = capture_record_key(SOURCE_ID, at, entry["sha256"])
            if not store.exists(record):
                store.put(record, canonical_json(receipt.as_record()))
            receipts.append(entry["sha256"])
        rows = [
            [
                p.start.isoformat(),
                p.end.isoformat(),
                str(p.total_return),
                str(p.price_return),
                str(p.income_return),
            ]
            for p in series[symbol].periods
        ]
        release = make_release(
            {
                "dataset_id": factor,
                "version": "e0002-0",
                "spec_ref": f"{factor}@{SPEC_VERSION}",
                "code_ref": dict(code),
                "inputs": [{"series_id": symbol, "receipts": sorted(receipts)}],
                "knowledge_mode": KnowledgeMode.LATEST.value,
                "knowledge_cutoff": instant_str(cutoff),
                "weakest_knowable_basis": "rule_inferred",
                "rights": propagate([gate.records[SOURCE_ID]]),
                "invariant_results": {"RA-INV-001": "pass; checked per period", "RA-INV-020": "pass; tests"},
                "quality_summary": {"periods": len(rows), "notices": [NOTICE], "limitations": LIMITATION},
                "supersedes": None,
            },
            {
                "data.csv": render_csv(
                    ["period_start", "period_end", "r", "price_return", "income_return"], rows
                )
            },
        )
        write_release(store, gate, release)
        append_status(
            store, release.content_sha256, Status.EXPLORATORY, "job:e0002", "Q1 to Q3 passed", cutoff
        )
        hashes[sleeve] = release.content_sha256
    return hashes, cutoff


def describe(panel: fa.Panel, weights: Mapping[str, float], *, closed: bool = False) -> dict[str, Any]:
    """`closed`: the span ends on a window's stated month end, so its last month counts (V3). A
    final week is left out either way, because a window's end date rarely ends a week."""
    path = fa.wealth_path(panel, weights)
    fa.reconcile(panel, weights, path)
    dd = fa.drawdown(path.dates, path.wealth)
    out = {
        "start": path.dates[0].isoformat(),
        "end": path.dates[-1].isoformat(),
        "final_wealth": float(path.wealth[-1]),
        "annualised_return": fa.annualised_return(path),
        "max_drawdown": dd.max_drawdown,
        "peak": dd.peak.isoformat(),
        "trough": dd.trough.isoformat(),
        "recovery": dd.recovery.isoformat() if dd.recovery else None,
        "longest_underwater_days": dd.longest_underwater_days,
        "underwater_fraction": dd.underwater_fraction,
    }
    for frequency in ("monthly", "weekly"):
        try:
            final = closed and frequency == "monthly"
            returns = fa.period_returns(path.dates, path.wealth, frequency, include_final=final)
            out[f"volatility_{frequency}"] = fa.annualised_volatility(returns, frequency)
        except ValueError:
            out[f"volatility_{frequency}"] = None
    return out


def dependence(panel: fa.Panel, *, closed: bool = False) -> dict[str, Any]:
    levels = fa.sleeve_levels(panel)
    out = {"sleeves": list(panel.sleeves)}
    for frequency in ("monthly", "weekly"):
        try:
            final = closed and frequency == "monthly"
            returns = fa.period_returns(panel.dates, levels, frequency, include_final=final)
            cov, corr = fa.covariance(returns)
            out[frequency] = {"covariance": cov.tolist(), "correlation": corr.tolist()}
        except ValueError:
            out[frequency] = None
    return out


def compare(panel: fa.Panel) -> dict[str, Any]:
    results: dict[str, Any] = {"windows": {}}
    for name, (start, end) in WINDOWS.items():
        low, high = max(start, panel.dates[0]), min(end, panel.dates[-1])
        if start != date.min and start < panel.dates[0]:
            results["windows"][name] = {"available": False}
            continue
        try:
            part = fa.window(panel, low, high)
        except fa.AlignmentError:
            results["windows"][name] = {"available": False}
            continue
        results["windows"][name] = {
            "available": True,
            "allocations": {a: describe(part, w, closed=end != date.max) for a, w in ALLOCATIONS.items()},
            "dependence": dependence(part, closed=end != date.max),
        }
    monthly = fa.period_returns(panel.dates, fa.sleeve_levels(panel), "monthly")
    weights = {a: np.array([w[s] for s in panel.sleeves]) for a, w in ALLOCATIONS.items()}
    results["bootstrap_treasury_minus_cash"] = {}
    for block in BLOCKS:
        boot = fa.paired_block_bootstrap(
            monthly,
            weights["60_equity_40_cash"],
            weights["60_equity_40_treasury"],
            block_months=block,
            replications=REPLICATIONS,
            seed=SEED,
        )
        results["bootstrap_treasury_minus_cash"][str(block)] = {
            metric: vars(getattr(boot, metric))
            for metric in ("volatility", "annualised_return", "max_drawdown")
        }
    return results


def _table(results: Mapping[str, Any]) -> list[str]:
    lines = []
    for name, window in results["windows"].items():
        lines.append(f"\n## Window: {name}\n")
        if not window["available"]:
            lines.append("Not available in the common history.")
            continue
        lines.append(
            "| Allocation | Wealth | Return p.a. | Vol (monthly) | Vol (weekly) | Max drawdown | Trough "
            "| Recovery "
            "| Longest under water (days) |"
        )
        lines.append("|---|---:|---:|---:|---:|---:|---|---|---:|")
        for allocation, d in window["allocations"].items():
            monthly = "n/a" if d["volatility_monthly"] is None else f"{d['volatility_monthly']:.2%}"
            weekly = "n/a" if d["volatility_weekly"] is None else f"{d['volatility_weekly']:.2%}"
            lines.append(
                f"| {allocation} | {d['final_wealth']:.3f} | {d['annualised_return']:.2%} | {monthly} | "
                f"{weekly} | "
                f"{d['max_drawdown']:.2%} | {d['trough']} | {d['recovery'] or 'not recovered'} | "
                f"{d['longest_underwater_days']} |"
            )
        sleeves = window["dependence"]["sleeves"]
        for frequency in ("monthly", "weekly"):
            block = window["dependence"][frequency]
            if block:
                a, b = sleeves.index("equity"), sleeves.index("treasury")
                lines.append(
                    f"\nEquity-Treasury, {frequency}: correlation {block['correlation'][a][b]:.3f}, "
                    f"covariance {block['covariance'][a][b]:.6f}."
                )
    lines.append(
        "\n## 60/40 Treasury minus 60/40 cash, paired block bootstrap (descriptive; this history only)\n"
    )
    lines.append("| Block (months) | Metric | Observed | 2.5% | 97.5% |")
    lines.append("|---:|---|---:|---:|---:|")
    for block, metrics in results["bootstrap_treasury_minus_cash"].items():
        for metric, v in metrics.items():
            lines.append(f"| {block} | {metric} | {v['estimate']:.2%} | {v['low']:.2%} | {v['high']:.2%} |")
    return lines


def reference_detail(root: Path, symbol: str, dividends: Sequence[Mapping[str, Any]]) -> list[str]:
    """For the owner only: each date where the vendor's distribution differs from the issuer's."""
    path = root / "reference" / f"{symbol}.csv"
    if not path.is_file():
        return []
    vendor = {str(r["date"]): r.get("unadjustedValue") for r in dividends}
    lines = []
    for row in csv.DictReader(path.open()):
        amount = Decimal(row["amount"])
        if row["ex_date"] in vendor and not _agrees(vendor[row["ex_date"]], amount):
            lines.append(f"- {symbol} {row['ex_date']}: vendor {vendor[row['ex_date']]}, issuer {amount}.")
    return lines


def render_owner_report(results: Mapping[str, Any] | None, differences: Sequence[str] = ()) -> str:
    lines = [
        "# E-0002: for the owner only. Holds licensed-derived values: don't commit, share or paste into AI.",
        "",
        "Descriptive. Three named funds, one history, no trading costs or tax. No recommendation or "
        "forecast.",
        "IEF is a vehicle and validates no synthetic factor. BIL is a bill-ETF sleeve, not overnight cash.",
    ]
    if results is None:
        lines.append("\nThe comparison didn't run: Q1 to Q3 didn't pass for all three sleeves.")
    else:
        lines += _table(results)
    if differences:
        lines += ["\n## Distributions that differ from the issuer's\n", *differences]
    return "\n".join(lines) + "\n"


def run(
    root: Path, snapshot: str, *, gate: RightsGate, code: Mapping[str, str], compare_to: str | None = None
) -> dict:
    """Stdout-safe summary returned: counts and pass or fail. Values go only to reports/."""
    check_root(root)
    manifest = load_snapshot(root, snapshot)
    series: dict[str, Series] = {}
    fx_rows = _read(root, manifest, FOREX, "eod")
    for symbol, currency in ETFS.items():
        series[symbol] = analyse(
            symbol,
            currency,
            quote_currency(_read(root, manifest, f"EXCHANGE.{symbol.rsplit('.', 1)[1]}", "symbols"), symbol),
            _read(root, manifest, symbol, "eod"),
            _read(root, manifest, symbol, "div"),
            _read(root, manifest, symbol, "splits"),
        )
    gate_ok = all(series[s].qualified[q] for s, _ in SLEEVES.values() for q in ("Q1", "Q2", "Q3"))
    summary: dict[str, Any] = {
        "snapshot": snapshot,
        "code": dict(code),
        "instruments": {s: {"qualified": v.qualified, **v.profile} for s, v in series.items()},
        "forex": {"symbol": FOREX, "rows": len(fx_rows)},
        "comparison_ran": gate_ok,
    }
    references = {s: check_reference(root, s, _read(root, manifest, s, "div")) for s in ETFS}
    summary["independent_reference"] = {
        s: r if r else "not read: no independent check" for s, r in references.items()
    }
    if compare_to:
        summary["snapshot_changes"] = compare_snapshots(root, load_snapshot(root, compare_to), manifest)
    results = None
    if gate_ok:
        store_dir = root / "store"
        if store_dir.exists():
            shutil.rmtree(store_dir)
        store = LocalObjectStore(store_dir)
        hashes, cutoff = write_releases(root, store, manifest, series, gate=gate, code=code)
        pins = [Pin(sleeve, SLEEVES[sleeve][1], sha) for sleeve, sha in hashes.items()]
        panel, read = read_panel(
            store, pins, mode=KnowledgeMode.LATEST, cutoff=parse_instant(instant_str(cutoff)), gate=gate
        )
        results = compare(panel)
        summary["releases"] = hashes
        summary["common_periods"] = len(panel.dates) - 1
        summary["common_first"] = panel.dates[0].isoformat()
        summary["common_last"] = panel.dates[-1].isoformat()
        summary["omitted_dates"] = dict(panel.omitted_dates)
        summary["windows_available"] = {k: v["available"] for k, v in results["windows"].items()}
        summary["inputs_read"] = [r["content_sha256"] for r in read]
    if (root / "store").exists():
        make_private(root / "store")
    reports = root / "reports"
    reports.mkdir(mode=0o700, exist_ok=True)
    differences = [line for s in ETFS for line in reference_detail(root, s, _read(root, manifest, s, "div"))]
    private_write(reports / "owner-report.md", render_owner_report(results, differences).encode())
    if results is not None:
        private_write(
            reports / "owner-values.json", (json.dumps(results, indent=1, sort_keys=True) + "\n").encode()
        )
    private_write(root / "summary.json", (json.dumps(summary, indent=1, sort_keys=True) + "\n").encode())
    return summary


def code_commit() -> dict[str, str]:
    git = ("git", "-C", str(REPO))
    status = subprocess.run((*git, "status", "--porcelain"), capture_output=True, text=True, check=True)
    if status.stdout.strip():
        raise Stop("the working tree has uncommitted changes")
    commit = subprocess.run(
        (*git, "rev-parse", "HEAD"), capture_output=True, text=True, check=True
    ).stdout.strip()
    return {"commit": commit, "lock_sha256": hashlib.sha256((REPO / "uv.lock").read_bytes()).hexdigest()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["whoami", "fetch", "run"])
    parser.add_argument("--root", type=Path, default=Path.home() / ".hio-research" / "E-0002-eodhd")
    parser.add_argument("--snapshot", default="s1")
    parser.add_argument("--compare-to")
    args = parser.parse_args(argv)
    try:
        gate = make_gate()
        gate.authorise(Operation.FETCH if args.command != "run" else Operation.BUILD, [SOURCE_ID])
        if args.command == "whoami":
            status, body = http_getter(vault_key(args.root))("/user?fmt=json")
            if status != 200:
                raise Stop(f"HTTP {status}")
            print(json.dumps({"subscriptionType": json.loads(body).get("subscriptionType")}))
        elif args.command == "fetch":
            manifest = fetch(
                args.root,
                args.snapshot,
                gate=gate,
                commit=code_commit()["commit"],
                get=http_getter(vault_key(args.root)),
            )
            print(json.dumps({"files": len(manifest["files"]), "stopped": manifest["stopped"]}))
        else:
            summary = run(args.root, args.snapshot, gate=gate, code=code_commit(), compare_to=args.compare_to)
            print(
                json.dumps(
                    {
                        "comparison_ran": summary["comparison_ran"],
                        "qualified": {s: v["qualified"] for s, v in summary["instruments"].items()},
                    },
                    sort_keys=True,
                )
            )
    except Exception as exc:  # the type only: a message could hold a URL with the key, or a value
        print(f"stopped: {type(exc).__name__}: {exc if isinstance(exc, Stop) else ''}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
