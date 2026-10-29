---
id: OD-0120
title: "Owner assigns Codex reviews REVIEW-2026-10-29-t0010-1 (feat/t0010 at f345d1e) and REVIEW-2026-10-29-t0011-1 (infra/t0011 at 2cc7362); nothing received, accepted or authorised live"
decision: authorise_work
record_status: recorded
created_at: 2026-10-29
updated_at: 2026-10-29
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-29-owner-assign-t0010-t0011-reviews.md (owner's message AR, verbatim, with the assignment Claude put)
  sha256: 03ca35aa5dca5bd968c77e9e0af208fd875cd25d6aef15ed09349dabf7c1d9ee
  date: 2026-10-29
  quote: "approved"
applies_to:
  - path: feat/t0010
    revision: f345d1ea1498c451fe91f09bbddf327f0fd54ea8
  - path: infra/t0011
    revision: 2cc7362b962a76b76a3100fbc241a7b204957619
related: {adrs: [HIO-ADR-0012], tasks: [T-0010, T-0011], findings: [], ods: [OD-0115, OD-0116, OD-0117, OD-0118, OD-0119]}
---

# OD-0120: Codex reviews of T-0010 and T-0011 assigned

## Assignment 1

| Field | Value |
|---|---|
| Review id | `REVIEW-2026-10-29-t0010-1` |
| Repository | `elusivenode/hio` |
| Base SHA | `150f8136bf0cd803746f997e37e3365e2638f8b7` |
| Head SHA | `f345d1ea1498c451fe91f09bbddf327f0fd54ea8` (branch `feat/t0010`; fixed; `ls-remote` confirmed) |
| Scope | T-0010 (`registers/tasks/T-0010-s1b1-non-live-integration.md` at the head): W-1 transport, W-2 Azure backend and authentication, W-3 live-path wiring and workflow definition, W-4 C1–C7 and finality against HIO-ADR-0012 §4.3.3–4.3.4, the release notices; the `registers/sources.yaml` dataset records against OD-0116 (with correction 1) and OD-0118 and the T-0002 matrix; that no live path is reachable without `LIVE_AUTHORISATION` and no workflow in `.github/workflows/` has a schedule; the `check_repo` network and Azure import allowances; no regression of T-0009 A-1 to A-11 or the four S1a `data.csv` sha256; the 747-test baseline and CI's exact lint commands |
| Review branch | `review/t0010-1-codex`, cut at the head |

## Assignment 2

| Field | Value |
|---|---|
| Review id | `REVIEW-2026-10-29-t0011-1` |
| Repository | `elusivenode/hio` |
| Base SHA | `4bce6ae0f38d5a364218c6295406a558dea2f387` |
| Head SHA | `2cc7362b962a76b76a3100fbc241a7b204957619` (branch `infra/t0011`, PR #8; fixed; `ls-remote` confirmed) |
| Scope | T-0011 I-1 to I-6 (`registers/tasks/T-0011-s1b1-infrastructure-as-code.md` at the head) against the card and the H3/H4 settings adopted by OD-0119 (`docs/evidence/S1B1-H3-H4-decision-pack.md` on `main`); role scoping (create-only writer on the container; state admin on the state container only); no subscription, tenant, object, email or GitHub numeric id committed; offline validity (`tofu fmt`, `tofu validate` with `-backend=false` if the reviewer can run them; otherwise a static reading); the 440-test baseline |
| Review branch | `review/t0011-1-codex`, cut at the head |

## Common terms

- **Reviewer:** Codex, independent reviewer; writes only under `reviews/`; no PR; every file added under `reviews/`
  carries YAML front matter with at least `id`, and `tools/check_repo.py` must pass.
- **Delivery:** hiomux Codex tasks, `gpt-6-sol` `high`, with network (OD-0077), public reads only; no Azure or
  GitHub credential is available to the reviewer and none may be used.
- **Stop conditions:** a head differs from `ls-remote`; a base is not an ancestor of its head; this assignment
  conflicts with another owner-authored source.

## Not authorised

Receipt of either result; acceptance of T-0010 or T-0011; merging PR #8 or `feat/t0010`; any waiver; Authorisation B.

## Corrections (append-only)
