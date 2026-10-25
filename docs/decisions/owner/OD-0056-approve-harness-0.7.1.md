---
id: OD-0056
title: "Owner approval of the harness-0.7.1 procedure as applied in C1 (552d4fb); C2 (8461e99) authorised on a verified consequentiality condition; first receipt supervised; routine delegated receipt not authorised"
decision: approve
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-adr0012-harness-0.7.1-approval.md (pasted by the owner, verbatim; Decision 2)
  sha256: 53b1b54d14a59f9bcab28dfea7698fb24e1c0fe6a76c95cb963a44487b1ac90d
  date: 2026-10-25
  quote: "I approve the harness-0.7.1 procedure applied in C1, commit `552d4fbde6f4256bf969b908d721a765aae84e17`, operating-model blob `a74a41453d10b54161136ff08ac36e6ca86f33bc`."
applies_to:
  - path: docs/harness/operating-model.md
    revision: 552d4fbde6f4256bf969b908d721a765aae84e17   # C1, blob a74a41453d10b54161136ff08ac36e6ca86f33bc (from approved blob 920b1bb153bf7ffaf3a8356a7486b2fa86c5be3f)
  - path: AGENTS.md
    revision: 8461e99639f0ee7bc8cb9de2895d00d257d12974   # C2, blob 6eb9f76668149986c8a0fb0677b1e55218334719; conditional, see below
  - path: reviews/README.md
    revision: 8461e99639f0ee7bc8cb9de2895d00d257d12974   # C2, blob 921406e221281c8d07c670ec78566e56b0cbd0e2; conditional, see below
related: {adrs: [], tasks: [], findings: [F-REVIEW-2026-10-25-harness-0.7.1-1, F-REVIEW-2026-10-25-harness-0.7.1-2, F-REVIEW-2026-10-25-harness-0.7.1-3, F-REVIEW-2026-10-25-harness-0.7.1-4]}
---

# OD-0056: approve harness-0.7.1 (C1) and conditionally C2

## Owner action

Decision 2 (verbatim in the history file): approve the harness-0.7.1 procedure applied in C1; also
**authorise C2, conditional on verifying** that its `AGENTS.md` and `reviews/README.md` changes
are strictly consequential to C1 and introduce no substantive additional authority. The first
receipt under harness-0.7.1 **must be supervised**; routine delegated receipt is **not authorised**
until that pilot passes and is recorded.

## Verification from Git before recording

| Check | Result |
|---|---|
| C1 `552d4fb` parent | `6fbec1a` (= `main`); one commit |
| C1 changes | only `docs/harness/operating-model.md` (155 insertions, 19 deletions); blob `920b1bb…` → `a74a41453d10b54161136ff08ac36e6ca86f33bc`, equal to the owner's blob |
| C2 `8461e99` parent | C1; one commit; touches only `AGENTS.md` and `reviews/README.md` (6 insertions, 5 deletions); blobs `6eb9f76…` and `921406e…` equal the package |
| `tools/`, `.github/`, accepted S1a, every approved standard | not touched by C1 or C2 |

**C2 consequentiality (the owner's condition), assessed line by line:**

| C2 line | Relation to C1 | Added authority? |
|---|---|---|
| `AGENTS.md` reviewer bullet: "open a PR stating `Reviewed-Head`" → "open no PR" plus a final message carrying the branch tip SHA, the reviewed head and the sha256 of each added file | restates C1 §6.2 step 3 (no PR; the final message is the independent report) in the onboarding file | **No.** It repeats the C1 text and gives the reviewer no new power. The "never edit the work under review" limit is unchanged |
| `AGENTS.md` front matter: `status: proposed`, `version: harness-0.7.1 (proposed)` | provenance markers for a proposal | **No.** They are reverted to approved values by the status-only edit; `approved_by: OD-0021` is retained and OD-0056 added |
| `reviews/README.md` "Who writes what": "merges reviewer PRs (receipt only)" → "receives reviewer evidence by byte-identical import, never by merging a reviewer branch (receipt only; operating model §6.2 step 5)" | restates C1 §6.2 step 5 and the preamble | **No.** It removes a PR-merge role C1 abolishes and cites step 5 |

**Result: the condition is met. C2 is strictly consequential to C1 and adds no substantive
authority.** It is included.

**Observation, not an edit.** Three other files still mention reviewer PRs: `.github/pull_request_template.md`,
`.github/workflows/review-scope.yml` and `tools/review_gate.py`. The approval package treats
them as unchanged (the workflow becomes dormant, because no reviewer PRs are opened). Changing
them is a separate authorisation and is **not** done here.

## Adoption conditions

1. **Supervised first receipt** under the approved procedure, A2 (`dac54f5`) per OD-0057: the
   dry run in isolation, its checks and transcript presented to the owner, and **no push to `main`
   until the owner's explicit go-ahead**.
2. **Any step that needs improvisation stops the run** and returns the amendment to the owner as a
   new revision.
3. A clean first use is **recorded in an OD** (the adoption test) before routine receipt is
   enabled. **Until then routine delegated receipt is not authorised.**

## What this record does NOT do

- It does not receive any review, merge any reviewer branch, waive a finding, or approve an earlier
  one-off exception (push-only delivery of the first two reviews; OD-0052's reading of step 6).
- It does not authenticate Git users, and the 5.6 semantic index check stays manual.
- It does not change `tools/`, `.github/`, accepted S1a or any approved standard.

## Corrections (append-only)

None.
