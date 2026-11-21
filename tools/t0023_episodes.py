"""T-0023 step 6 (OD-0180, preregistration 2): three stress episodes, robustness and the decision rule.

For each episode (2008, q1_2020, 2022) and the three allocations: compounded return and month-end maximum
drawdown, the three effects on both, each sleeve's return, the FX return and the bills-against-cash split.
Each effect is recomputed under S1 to S9 of preregistration-1, built by the step 3, 4 and 5 tools. No
bootstrap. Values go only to report.md and summary.json under the output directory; stdout holds each
effect's robustness and sign, the sensitivity status and the decision row. Retrospective description only:
three hand-named episodes confirm nothing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np

import e0001_run as e1
import e0002_aud as aud_tool
import e0003_aud_cash as base
import e0003_extended as ext
import e0003_panel as panel_tool
import eodhd_eval as ev
import t0023_basis as basis
import t0023_common as common
import t0023_seam as seam
import t0023_sleeves as sl
from hio.contracts.rights import Operation
from hio.rights.gate import RightsGate

# The preregistration's episodes: window, and the number of months it must hold.
EPISODES: dict[str, tuple[tuple[date, date], int]] = {
    "2008": ((date(2007, 12, 31), date(2008, 12, 31)), 12),
    "q1_2020": ((date(2019, 12, 31), date(2020, 3, 31)), 3),
    "2022": ((date(2021, 12, 31), date(2022, 12, 31)), 12),
}
SIZE_BAR = 0.02  # two percentage points, as a fraction: the size E-0003 already used
ZERO = 1e-12  # below this a value is zero, and a zero has no sign
SENSITIVITY_IDS = tuple(f"S{i}" for i in range(1, 10))
MEASURES = ("compounded_return", "max_drawdown")
PRIMARY_EFFECTS = ("cash_rate_and_currency", "treasury_duration")
DECISION_MEASURE = "compounded_return"
SLEEVE_NAMES = ("equity", "bills", "treasury", "cash")
USD_SLEEVES = ("equity", "bills", "treasury")
ROWS = {
    1: (
        "One conditional-diversification experiment may be warranted: the contrast exists to be studied, "
        "and the recommendation must name what it needs."
    ),
    2: (
        "Not warranted as conditional: there's no contrast. Report the consistent direction, as three "
        "episodes only."
    ),
    3: "Not warranted. The evidence can't support it.",
}
WORDS = (
    "Retrospective description only: three hand-named episodes confirm nothing. This isn't a regime model or "
    "a forecast. Declared before the comparison ran, and not blind."
)
RECOMMENDATION_NOTE = (
    "Whichever row applies, the recommendation states the C1 to C5 failures and gaps it rests on, and that a "
    "contrast across three hand-named episodes is a reason to design a test, not evidence of a relationship. "
    "The architect is consulted before it's put to the owner."
)


@dataclass(frozen=True)
class Variant:
    """A sensitivity's panel, or why it couldn't be built."""

    panel: common.FrozenPanel | None
    why: str = ""


# --- the measures


def sign_of(value: float) -> int:
    return 0 if abs(value) < ZERO else (1 if value > 0 else -1)


def episode_measures(panel: common.FrozenPanel, window: tuple[date, date], months: int) -> dict[str, Any]:
    """One episode on one panel. All its months must be there; one missing stops. No bootstrap.

    Compounded return is final wealth less 1 of the allocation's monthly path. Months are chosen as
    base.evaluate chooses them.
    """
    start, end = window
    kept = [
        i for i in range(panel.returns.shape[0]) if start <= panel.months[i] and panel.months[i + 1] <= end
    ]
    if len(kept) != months:
        raise ev.Stop(f"the episode {start} to {end} holds {len(kept)} months, not {months}")
    dates = [panel.months[kept[0]], *(panel.months[i + 1] for i in kept)]
    if (dates[0] - start).days > base.MAX_STALE_DAYS or (end - dates[-1]).days > base.MAX_STALE_DAYS:
        raise ev.Stop(f"the episode {start} to {end} isn't covered by month ends")
    part = panel.returns[kept]
    stats = {p: aud_tool._path_stats(dates, part @ base.weights_vector(p)) for p in base.PORTFOLIOS}
    allocations = {
        p: {"compounded_return": s["final_wealth"] - 1, "max_drawdown": s["max_drawdown"]}
        for p, s in stats.items()
    }
    effects = {
        effect: {m: allocations[b][m] - allocations[a][m] for m in MEASURES}
        for effect, (a, b) in base.EFFECTS.items()
    }
    usd = {name: values[kept] for name, values in common.usd_columns(panel).items()}
    fx = panel.s[kept]
    sleeves = {
        name: {
            "aud": float(np.prod(1 + part[:, base.SLEEVES.index(name)]) - 1),
            **({"usd": float(np.prod(1 + usd[name]) - 1)} if name in USD_SLEEVES else {}),
        }
        for name in SLEEVE_NAMES
    }
    return {
        "months": months,
        "start": dates[0].isoformat(),
        "end": dates[-1].isoformat(),
        "allocations": allocations,
        "effects": effects,
        "sleeves": sleeves,
        "fx_return": float(np.prod(1 + fx) - 1),
        "bills_against_cash": base.bills_against_cash(usd["bills"], fx, part[:, base.SLEEVES.index("cash")]),
    }


def robust(frozen: float, under: Mapping[str, float | None]) -> dict[str, Any]:
    """Whether an effect is robust on one measure in one episode (preregistration 2, Robustness).

    All three must hold: at least 2 points in size on the frozen panel; the same sign under every one of
    S1 to S9 (a zero is a changed sign); and every sensitivity performed, `None` meaning it wasn't.
    """
    values = {sid: under.get(sid) for sid in SENSITIVITY_IDS}
    not_performed = [sid for sid, v in values.items() if v is None]
    sign = sign_of(frozen)
    changed = [sid for sid, v in values.items() if v is not None and sign_of(v) != sign]
    big = round(abs(frozen), 12) >= SIZE_BAR
    return {
        "robust": big and not changed and not not_performed,
        "sign": sign,
        "at_least_2_points": big,
        "changed_sign": changed,
        "not_performed": not_performed,
    }


def effect_finding(results: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """One effect's decision row from its robust results across the episodes, on compounded return."""
    signs = {r["sign"] for r in results.values() if r["robust"]}
    row = 1 if {1, -1} <= signs else 2 if signs else 3
    return {"row": row, "text": ROWS[row], "robust_signs": sorted(signs)}


def decision(robustness: Mapping[str, Mapping[str, Mapping[str, Mapping[str, Any]]]]) -> dict[str, Any]:
    """The preregistered rule, on the two primary effects and compounded return only. Drawdown and the total
    effect can't change it. When the effects differ, one effect in the first row decides; otherwise one with
    a robust result of one sign puts the finding in the second row, and the third needs no robust result."""
    findings = {
        effect: effect_finding({ep: robustness[effect][ep][DECISION_MEASURE] for ep in robustness[effect]})
        for effect in PRIMARY_EFFECTS
    }
    rows = [f["row"] for f in findings.values()]
    row = 1 if 1 in rows else 2 if 2 in rows else 3
    return {"row": row, "text": ROWS[row], "effects": findings}


def analyse(frozen: common.FrozenPanel, variants: Mapping[str, Variant]) -> dict[str, Any]:
    """Every episode on the frozen panel, each effect under every sensitivity, and the decision."""
    episodes = {name: episode_measures(frozen, window, months) for name, (window, months) in EPISODES.items()}
    under: dict[str, dict[str, Any]] = {}
    whys: dict[str, str] = {}
    for sid in SENSITIVITY_IDS:
        variant = variants.get(sid) or Variant(None, "no such sensitivity was built")
        whys[sid] = variant.why
        under[sid] = (
            None
            if variant.panel is None
            else {
                name: episode_measures(variant.panel, window, months)["effects"]
                for name, (window, months) in EPISODES.items()
            }
        )
    robustness = {
        effect: {
            name: {
                m: robust(
                    episodes[name]["effects"][effect][m],
                    {sid: None if r is None else r[name][effect][m] for sid, r in under.items()},
                )
                for m in MEASURES
            }
            for name in EPISODES
        }
        for effect in base.EFFECTS
    }
    return {
        "episodes": episodes,
        "sensitivities": {
            sid: {"performed": under[sid] is not None, "why": whys[sid]} for sid in SENSITIVITY_IDS
        },
        "robustness": robustness,
        "decision": decision(robustness),
        "sensitivity_effects": sensitivity_effects(episodes, under),
    }


def sensitivity_effects(
    episodes: Mapping[str, Mapping[str, Any]], under: Mapping[str, Mapping[str, Any] | None]
) -> dict[str, dict[str, dict[str, dict[str, float | None]]]]:
    """For each effect, episode and measure: the frozen value and S1 to S9's, `None` if not performed."""
    return {
        effect: {
            name: {
                m: {
                    "frozen": episodes[name]["effects"][effect][m],
                    **{sid: None if under[sid] is None else under[sid][name][effect][m] for sid in under},
                }
                for m in MEASURES
            }
            for name in episodes
        }
        for effect in base.EFFECTS
    }


# --- what the sensitivities read

E0001_PATTERN = "raw/*.xml"


def file_sha256(path: Path) -> str | None:
    """The file's sha256, or `None` if it isn't there."""
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def xml_sha256(raw: Path) -> str | None:
    """One sha256 over the *.xml files directly in raw, sorted by name, each name and its bytes."""
    names = sorted(p.name for p in raw.glob("*.xml") if p.is_file()) if raw.is_dir() else []
    if not names:
        return None
    digest = hashlib.sha256()
    for name in names:
        digest.update(name.encode())
        digest.update((raw / name).read_bytes())
    return digest.hexdigest()


def sensitivity_inputs(
    root: Path, e0002: Path, e0001: Path, e0003: Path, history_root: Path, h10_root: Path
) -> dict[str, str | None]:
    """The sha256 of every file the sensitivities read, by path relative to its workspace. A missing file,
    or one that can't be located, is `None`."""
    out: dict[str, str | None] = {}
    for name in ("spy", "bil", "ief"):
        out[f"reference/nav-{name}.csv"] = file_sha256(root / "reference" / f"nav-{name}.csv")
    out["reference/raw/rba-cash-rate.html"] = file_sha256(root / "reference" / seam.PAGE)
    out["reference/manifest.json"] = file_sha256(root / "reference" / "manifest.json")
    out["E-0003/raw/rba_f1.csv"] = file_sha256(e0003 / "raw" / "rba_f1.csv")
    out["RBA-F1-history/firmmcrid.csv"] = file_sha256(history_root / "firmmcrid.csv")
    out["H10/FRB_h10_xml.zip"] = file_sha256(h10_root / "FRB_h10_xml.zip")
    out["E-0001/variant-summary.json"] = file_sha256(e0001 / "variant-summary.json")
    data = None
    try:
        release = json.loads((e0001 / "variant-summary.json").read_text())["release"]
        data = e0001 / "store-variant" / "releases" / e1.DATASET_ID / release / "data.csv"
    except (OSError, ValueError, KeyError, TypeError):
        pass
    out["E-0001/variant release data.csv"] = None if data is None else file_sha256(data)
    out[f"E-0001/{E0001_PATTERN}"] = xml_sha256(e0001 / "raw")
    out["E-0002/raw/s2/manifest.json"] = file_sha256(
        ev.snapshot_dir(e0002, panel_tool.SNAPSHOT) / "manifest.json"
    )
    return out


# --- the nine sensitivity panels, from the tools that define them


def not_built(ids: Sequence[str], why: str) -> dict[str, Variant]:
    return {sid: Variant(None, why) for sid in ids}


def sleeve_variants(root: Path, e0002: Path, e0001: Path, panel: common.FrozenPanel) -> dict[str, Variant]:
    """S1 to S5, with the step 3 tool's inputs and its sources. The audited facts feed no sensitivity."""
    ids = list(sl.SENSITIVITIES)
    try:
        manifest = ev.load_snapshot(e0002, panel_tool.SNAPSHOT)
        funds = sl.load_funds(e0002, manifest)
        navs = {name: sl.load_nav(root / "reference" / f"nav-{name.lower()}.csv") for name in sl.FUNDS}
        par = sl.load_par(e0001)
        v1, _ = sl.load_v1(e0001)
    except FileNotFoundError as exc:
        return not_built(ids, f"an input is missing: {exc.filename and Path(exc.filename).name}")
    _, sources, _ = sl.run_checks(panel, funds, navs, par, v1, None)
    out: dict[str, Variant] = {}
    for sid, (_, wanted) in sl.SENSITIVITIES.items():
        missing = [sources[s].why for s in wanted.values() if sources[s].values is None]
        if missing:
            out[sid] = Variant(None, missing[0])
        else:
            changes = {column: sources[s].values for column, s in wanted.items()}
            out[sid] = Variant(common.with_changes(panel, usd=changes))
    return out


def seam_variants(
    root: Path, e0003: Path, history_root: Path, panel: common.FrozenPanel
) -> dict[str, Variant]:
    """S6 and S7, as the step 4 tool builds them, from the same files and the same integrity checks."""
    ids = ["S6", "S7"]
    try:
        manifest = json.loads((e0003 / "raw" / "manifest.json").read_text())
        body = (e0003 / "raw" / "rba_f1.csv").read_bytes()
        if hashlib.sha256(body).hexdigest() != manifest["receipt_id"]:
            raise ev.Stop("the retained F1 bytes don't match their manifest")
        try:
            parsed = seam.parse_rba_f1(seam.SERIES)(body)
        except Exception as exc:
            raise ev.Stop("the F1 receipt lacks a series this check needs") from exc
        by_series: dict[str, dict[date, Any]] = {name: {} for name in seam.SERIES.values()}
        for row in parsed.rows:
            by_series[row.series_id][row.valid_time] = row.value
        tri, aonia = by_series["tri"], by_series["aonia"]
        if not tri or min(tri.values()) <= 0:
            raise ev.Stop("no usable TRI level")
        history = ext.load_history(history_root)
        steps, _ = seam.parse_target_page(
            (root / "reference" / seam.PAGE).read_text(encoding="utf-8"),
            date(panel.months[0].year, panel.months[0].month, 1),
        )
    except FileNotFoundError as exc:
        return not_built(ids, f"an input is missing: {exc.filename and Path(exc.filename).name}")
    if not seam.baseline_rebuilds(panel, history, tri):
        return not_built(ids, "the frozen cash column isn't reproduced from the historical file and the TRI")
    return {
        "S6": Variant(seam.s6_panel(panel, history, steps, tri)),
        "S7": Variant(seam.s7_panel(panel, history, aonia)),
    }


def basis_variants(e0002: Path, h10_root: Path, panel: common.FrozenPanel) -> dict[str, Variant]:
    """S8 and S9, as the step 5 tool builds them."""
    ids = ["S8", "S9"]
    try:
        h10, _ = basis.load_h10(h10_root)
        manifest = ev.load_snapshot(e0002, basis.SNAPSHOT)
        eodhd = basis.eodhd_rates(ev._read(e0002, manifest, ev.FOREX, "eod"))
    except FileNotFoundError as exc:
        return not_built(ids, f"an input is missing: {exc.filename and Path(exc.filename).name}")
    eodhd_q = basis.month_end_rates(panel.months, eodhd)
    return {
        "S8": Variant(common.with_changes(panel, s=basis.fx_returns(eodhd_q))),
        "S9": Variant(
            common.with_changes(panel, s=basis.fx_returns(basis.next_published_rates(panel.months, h10)))
        ),
    }


def build_variants(
    root: Path,
    e0002: Path,
    e0001: Path,
    e0003: Path,
    history_root: Path,
    h10_root: Path,
    panel: common.FrozenPanel,
    gate: RightsGate,
) -> dict[str, Variant]:
    for path in (root, e0002, e0001, e0003):
        ev.check_root(path)
    for sources in (
        [ev.SOURCE_ID, e1.SOURCE_ID],
        [ext.HISTORY_SOURCE, base.RBA_SOURCE],
        [aud_tool.H10_SOURCE, ev.SOURCE_ID],
    ):
        gate.authorise(Operation.BUILD, sources)
    return {
        **sleeve_variants(root, e0002, e0001, panel),
        **seam_variants(root, e0003, history_root, panel),
        **basis_variants(e0002, h10_root, panel),
    }


# --- the report


def pct(value: float) -> str:
    return f"{value * 100:.2f}"


def table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    return lines + ["| " + " | ".join(r) + " |" for r in rows]


def sign_word(sign: int) -> str:
    return {1: "+", -1: "-", 0: "0"}[sign]


def robust_word(result: Mapping[str, Any]) -> str:
    return "robust" if result["robust"] else "not robust"


MARGINS_NOTE = (
    "For each effect on compounded return in each episode, the sensitivity whose value is nearest zero "
    "(S1 to S9 only, those performed)."
)
CAN_TEST_NOTE = (
    "Under common FX translation, with cash absent from both portfolios, S6, S7, S8 and S9 can't change the "
    "sign of treasury_duration on compounded return, because W_T_AUD - W_B_AUD = W_FX (W_T_USD - W_B_USD) "
    "with W_FX positive. On that effect only S1 to S5 are a challenge."
)


def margin_rows(result: Mapping[str, Any]) -> list[list[str]]:
    rows = []
    for effect, episodes in result["sensitivity_effects"].items():
        for name, measures in episodes.items():
            found = {
                sid: v for sid, v in measures[DECISION_MEASURE].items() if sid != "frozen" and v is not None
            }
            if not found:
                rows.append([effect, name, "none performed", ""])
                continue
            sid = min(found, key=lambda s: abs(found[s]))
            rows.append([effect, name, sid, pct(found[sid])])
    return rows


def render(result: Mapping[str, Any], panel_id: str, commit: str) -> str:
    lines = [
        "# T-0023 step 6: three stress episodes. For the owner: licensed-derived values; don't share.",
        "",
        WORDS,
        "",
        f"Panel `{panel_id}`, code `{commit}`, in AUD, monthly rebalanced. Figures are percent. "
        "No bootstrap: three months can't support one.",
    ]
    for name, ep in result["episodes"].items():
        lines += ["", f"## Episode `{name}`: {ep['start']} to {ep['end']}, {ep['months']} months", ""]
        rows = [
            [p, pct(v["compounded_return"]), pct(v["max_drawdown"])] for p, v in ep["allocations"].items()
        ]
        rows += [
            [f"effect: {e}", pct(v["compounded_return"]), pct(v["max_drawdown"])]
            for e, v in ep["effects"].items()
        ]
        lines += table(["Allocation", "Compounded return", "Maximum drawdown"], rows)
        lines += [""]
        lines += table(
            ["Sleeve", "AUD", "USD"],
            [[s, pct(v["aud"]), pct(v["usd"]) if "usd" in v else ""] for s, v in ep["sleeves"].items()],
        )
        lines += ["", f"FX return: {pct(ep['fx_return'])}. Bills against cash:", ""]
        lines += table(
            ["Part", "Compounded"],
            [[k.replace("_", " "), pct(v)] for k, v in ep["bills_against_cash"].items()],
        )
    lines += [
        "",
        "## Robustness",
        "",
        "Robust: at least 2 points on the frozen panel, the same sign under S1 to S9,",
    ]
    lines += ["and every sensitivity performed.", ""]
    rows = []
    for effect, episodes in result["robustness"].items():
        for name, measures in episodes.items():
            for m, r in measures.items():
                note = "; ".join(
                    [
                        *(["under 2 points"] if not r["at_least_2_points"] else []),
                        *(
                            [f"sign changed under {', '.join(r['changed_sign'])}"]
                            if r["changed_sign"]
                            else []
                        ),
                        *([f"not performed: {', '.join(r['not_performed'])}"] if r["not_performed"] else []),
                    ]
                )
                size = result["episodes"][name]["effects"][effect][m]
                rows.append([effect, name, m, pct(size), robust_word(r), sign_word(r["sign"]), note])
    lines += table(["Effect", "Episode", "Measure", "Frozen (points)", "Result", "Sign", "Why not"], rows)
    lines += ["", "## Sensitivities", ""]
    lines += table(
        ["Id", "Status"],
        [
            [sid, "performed" if s["performed"] else f"not performed: {s['why']}"]
            for sid, s in result["sensitivities"].items()
        ],
    )
    lines += ["", "## Margins", "", MARGINS_NOTE, ""]
    lines += table(["Effect", "Episode", "Nearest zero", "Value (points)"], margin_rows(result))
    lines += ["", "## What each sensitivity can test", "", CAN_TEST_NOTE]
    decided = result["decision"]
    lines += ["", "## Decision rule (step 7)", "", f"Row {decided['row']}: {decided['text']}", ""]
    for effect, f in decided["effects"].items():
        signs = ", ".join(sign_word(s) for s in f["robust_signs"]) or "none"
        lines.append(f"- {effect}, compounded return: row {f['row']} (robust signs: {signs}).")
    lines += ["", RECOMMENDATION_NOTE, "", WORDS]
    return "\n".join(lines) + "\n"


def stdout_lines(result: Mapping[str, Any]) -> list[str]:
    lines = [
        f"{sid}: {'performed' if s['performed'] else 'not performed: ' + s['why']}"
        for sid, s in result["sensitivities"].items()
    ]
    for effect, episodes in result["robustness"].items():
        for name, measures in episodes.items():
            lines += [
                f"{effect} {name} {m}: {robust_word(r)}, {sign_word(r['sign'])}" for m, r in measures.items()
            ]
    lines.append(f"decision: row {result['decision']['row']}")
    return lines


def run(
    root: Path,
    e0002: Path,
    e0001: Path,
    e0003: Path,
    history_root: Path,
    h10_root: Path,
    *,
    gate: RightsGate,
    code: Mapping[str, str],
    now: Any = None,
    variants_of: Callable[..., Mapping[str, Variant]] | None = None,
) -> dict[str, Any]:
    ev.check_root(root)
    panel, run_dir = common.load_frozen(root)
    record = json.loads((run_dir / "run.json").read_text())
    variants = (variants_of or build_variants)(root, e0002, e0001, e0003, history_root, h10_root, panel, gate)
    result = analyse(panel, variants)
    out = common.new_output(root, "step6", code["commit"], now)
    report = render(result, record["panel_id"], code["commit"])
    summary = {
        "panel_id": record["panel_id"],
        "code": dict(code),
        "words": WORDS,
        **result,
        "sensitivity_inputs": sensitivity_inputs(root, e0002, e0001, e0003, history_root, h10_root),
        "report_sha256": hashlib.sha256(report.encode()).hexdigest(),
        "output": out.name,
    }
    common.write_outputs(out, report, summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    research = Path.home() / ".hio-research"
    parser.add_argument("--root", type=Path, default=research / "T-0023")
    parser.add_argument("--e0002", type=Path, default=research / "E-0002-eodhd")
    parser.add_argument("--e0001", type=Path, default=research / "E-0001")
    parser.add_argument("--e0003", type=Path, default=research / "E-0003")
    parser.add_argument("--history", type=Path, default=research / "RBA-F1-history")
    parser.add_argument("--h10", type=Path, default=research / "H10")
    args = parser.parse_args(argv)
    try:
        summary = run(
            args.root,
            args.e0002,
            args.e0001,
            args.e0003,
            args.history,
            args.h10,
            gate=ev.make_gate(),
            code=ev.code_commit(),
        )
    except ev.Stop as exc:
        print(f"stopped: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # the type only: a message could hold a value
        print(f"stopped: {type(exc).__name__}", file=sys.stderr)
        return 2
    print("\n".join(stdout_lines(summary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
