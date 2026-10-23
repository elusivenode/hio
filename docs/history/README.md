---
id: HIO-HISTORY
title: Superseded inputs and rationale
status: historical
owner: HIO architecture lead (owner)
last_reviewed: 2026-10-24
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
| `2026-10-18-directive-harness-refinement.md` | brief supplied by the owner in chat **as a file path with no accompanying words**. It describes itself as a "Proposed documentation-only assignment". Its authorship is not stated in the file | historical; T-0006's commissioning brief; recorded in OD-0001 (corrected; the ambiguity is preserved) | partly by the final-correction directive |
| `2026-10-18-directive-t0006-final-correction.md` | owner directive ("From: HIO owner, with ChatGPT acting as strategic architecture collaborator"), supplied by file path. It explicitly authorises six documentation corrections, and cites a Codex focused analysis that was not supplied | historical; recorded in OD-0002 | — |
| `2026-10-18-directive-review-worktree-protocol.md` | proposed harness amendment (it names ChatGPT among its roles), adopted by the owner's chat instruction "please implement ... I will advise Codex" | historical; recorded in OD-0003; implemented as T-0007 | — |
| `2026-10-18-codex-assessment-t0007.md` | a Codex assessment of T-0007 at `46ea6a5`, pasted by the owner without words | historical evidence; remediated within T-0007 (OD-0003); not a review record | — |
| `2026-10-18-directive-g1-approval-package.md` | owner directive ("From: HIO owner, on architectural advice from ChatGPT") authorising receipt of VERIFY-2026-10-18-a01-1 and preparation of the G1 package | historical; the package's `authorised_by` | — |
| `2026-10-18-owner-g1-decisions.md` | the owner's own G1 decisions, verbatim (sha256 `111b6fc2…c306a99e`) | **authority** for OD-0006…0009 (not superseded) | — |
| `2026-10-18-owner-g1-followup.md` | the owner's follow-up instructions, verbatim | authority for OD-0010 | — |
| `2026-10-18-owner-g1-completion.md` | the owner's approval of ADR-0010 rev 3 and harness-0.6, and the T-0002/T-0003 instructions, verbatim | authority for OD-0011…0013 | — |
| `2026-10-24-owner-stale-line-fixes.md` | the owner's instruction to fix the stale lines, verbatim, with the list it refers to | authority for OD-0014 | — |
| `2026-10-24-owner-further-stale-lines.md` | the owner's instruction to fix the further stale lines, verbatim | authority for OD-0015 | — |
| `2026-10-18-directive-a01-baseline.md` | owner directive commissioning this baseline and the harness | historical (in force as the commissioning brief for A01) | — |

**Rule going forward** (operating model §0). An owner directive that changes direction is
committed here, and the decisions it makes become ADRs. Directives no longer live only in
`~/Downloads` or in chat.
