---
id: HIO-HISTORY
title: Superseded inputs and rationale
status: historical
owner: HIO architecture lead (owner)
last_reviewed: 2026-10-18
---

# HIO history: superseded inputs (kept verbatim for rationale)

These files are **not policy**. They record how the current baseline was reached. Where they
conflict with a canonical document, the canonical document wins (`AGENTS.md` precedence).

| File | What it is | Status | Superseded by |
|---|---|---|---|
| (not committed) the first owner brief, "Strategic Review of Investment Research and Portfolio Construction Roadmap" | supplied only as chat text on 2026-10-18. It asked for a critical review of the research direction across a factor universe, data acquisition, modelling, the SAA/TAA connection, layer separation, validation and sequencing | historical | answered by `2026-10-18-strategic-review.md`; its intent is carried into the charter |
| `2026-10-18-strategic-review.md` | Claude's first review: it treated HIO as an extension of the SMSF and its cadence | superseded | `2026-10-18-five-year-architecture-proposal.md`, then the canonical baseline |
| `2026-10-18-directive-five-year-architecture.md` | owner directive: HIO is a separate five-year system; it corrects six methodological points in the first review | historical (its decisions are in HIO-ADR-0001/0002/0007) | — |
| `2026-10-18-five-year-architecture-proposal.md` | Claude's architecture proposal; direction accepted "for further design" | superseded in part: §5.1 → HIO-ADR-0004; AD-6 → HIO-ADR-0005; §4.1 catalogue → HIO-ADR-0009; §11 slice → HIO-ADR-0010 | canonical baseline |
| `2026-10-18-directive-harness-refinement.md` | owner directive (supplied by the owner in chat): harness refinement before the Codex A01 review | historical; commissioning brief for T-0006; its authorisation transcribed as OD-0001 (proposed) | — |
| `2026-10-18-directive-a01-baseline.md` | owner directive commissioning this baseline and the harness | historical (in force as the commissioning brief for A01) | — |

**Rule going forward** (operating model §0). An owner directive that changes direction is
committed here, and the decisions it makes become ADRs. Directives no longer live only in
`~/Downloads` or in chat.
