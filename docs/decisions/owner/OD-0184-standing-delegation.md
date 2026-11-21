---
id: OD-0184
title: "Standing delegation to Claude as orchestrator (harness-0.10): act within authorised scope and report after"
decision: approve
record_status: recorded     # approved by the owner at 5ddbb7a (PR #106), correction 1
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-approve-od-0184.md (owner's message, verbatim, with Claude's question)
  sha256: 01cbc499e435698e24e7ac59996c680a81aaa2aef1508c674b7a6c4969e8d52e
  date: 2026-11-22
  quote: "y"
applies_to:
  - path: proposal/standing-delegation (PR #106)
    revision: 5ddbb7a3bdede0529e82ccdc0cc139ff3446ddc7
  - path: ~/.hio-runs/PROTOCOL.md (outside the repository)
    revision: "sha256 25dfb7794f3933a351ba8789b5a2acb9297746336fbe85227e585bdf54119045"
  - path: ~/.hio-runs/orch-prompt.md (outside the repository)
    revision: "sha256 9fbfce080b7ecbf4d7083fa29d1f446612e70c104165e970eb8ecd53522d00b7"
base_revision: 05f2dcd4782874d60f9f4bda4eb9eb07e0397bb9
related: {adrs: [HIO-ADR-0008], tasks: [], findings: [], ods: [OD-0061, OD-0076, OD-0139, OD-0183]}
---

# OD-0184: standing delegation

**The aim:** Claude, as orchestrator, acts without a per-item yes on work that is already within an authorised scope, and reports what it did afterwards. The owner keeps every decision that AGENTS.md rule 3 reserves, plus the high-risk actions listed below. This approves harness-0.10 (operating model §1.1, §2.2, §6.2 steps 0 and 1; AGENTS.md) at the approved head.

## A. Claude may, and reports after

| # | Power | Conditions |
|---|---|---|
| A1 | **Merge its own PRs** to `main` | all required checks green; `--match-head-commit` at the head checked; the content lies within scope an OD already authorises (records of owner statements, authorised task work, evidence, drafts marked `proposed`); **not** an excluded change (C) |
| A2 | **Assign a Codex review or verification** of Claude's own completed task work, and launch it in hiomux | Claude writes the *Assigned reviews* row with every field §6.2 step 1 requires, citing this OD; the reviewer gets no licensed data unless its rights row allows external processing; one review per target and scope |
| A3 | **Receive** review records | under OD-0061's conditions, unchanged |
| A4 | **Delegate** bounded work to hiomux workers | within an authorised task's scope and the run budget |
| A5 | **Read-only checks**: the evidence store (the owner's `az` login), GitHub, CI | no write of any kind |
| A6 | **Public research and drafting** | reading public pages; drafting specs, ADRs, cards and OD records as `proposed`. Reading a page is not acquiring a dataset |
| A7 | **Refresh the RITS and NSW reference calendars** | a manual read of the same RBA pages OD-0076 cleared, for a year they don't yet cover; facts extracted by hand, cited and dated; through a PR whose tests show coverage across the year boundary. An exception to OD-0076's single read |
| A8 | **Remediate findings** on Claude's own work, and record `remediation_claimed` | as now |

## B. Still the owner's, each by an explicit statement

Accepting work; approving an ADR, standard, spec or promotion; waiving or closing a finding; verifying any rights row; any new source, dataset download or vendor contact; any Azure write, `tofu apply` or workflow dispatch; MACSMSF; spending beyond a run's budget; widening any task's scope; a new task or experiment run.

## C. Excluded from A1: these merges need the owner's approval at the exact head

Changes to `.github/workflows/`, `infra/`, the live capture path (`src/hio/jobs/`, `src/hio/sources/`, `src/hio/storage/`, `src/hio/reference/calendars/` except under A7), credentials or deployment configuration, and the governance files `AGENTS.md`, `CLAUDE.md`, `docs/harness/`, `docs/standards/`, `docs/charter.md` and any approved ADR or spec. A merge whose content is not clearly inside an authorised scope also needs the owner's approval.

## D. Reporting and limits

- **Every action under A is recorded** in an OD or the review index, citing this OD, and summarised to the owner in the same session.
- **Git state is still not approval.** A1 permits the merge; it accepts and approves nothing that the merged content contains.
- **Stop and flag** on any conflict, mismatch, refusal or doubt about scope, as now.
- **The owner may narrow or revoke** this delegation by any statement, recorded as a correction here. It applies only to the Claude orchestrator session the owner directs.
- **On approval, Claude updates `~/.hio-runs/PROTOCOL.md`'s Codex paragraph** to cite this OD, and records the new hash here. Nothing else outside the repository changes.

## Corrections (append-only)

1. **2026-11-22: approved.** The owner approved PR #106 at `5ddbb7a3bdede0529e82ccdc0cc139ff3446ddc7` ("y"), which approves this delegation and harness-0.10. First use, A1: Claude merged #106 as `30b275b` (the approval was at the exact head, so that merge needed no delegation). **Outside the repository:** `~/.hio-runs/PROTOCOL.md`'s Codex paragraph now cites OD-0184 A2 (new sha256 `25dfb779…9045`, superseding OD-0089's `13a45eb7…71c9` as the hash record), and `~/.hio-runs/orch-prompt.md` names OD-0184 as the PROTOCOL hash record (sha256 `9fbfce08…b7`). hiomux is unchanged (`54fe4e86…`, OD-0111).
