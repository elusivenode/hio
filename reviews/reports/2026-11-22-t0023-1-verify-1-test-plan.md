---
id: VERIFY-2026-11-22-t0023-1-1-TEST-PLAN
title: T-0023 remediation verification test plan
status: in_review
---

# Test plan: VERIFY-2026-11-22-t0023-1-1

I am Codex, the independent reviewer. T-0023 is in_review. This plan was fixed before reading the author's response or handoff.

## Assignment and limits

OD-0186 correction 1 on public `main` and its Assigned reviews row name repository `elusivenode/hio`, base `4b6472e54aa7a1d989ee78ee49f83d6967a27536`, head `602be49d296316313ea479fb6b7b364555e253e5`, and branch `review/t0023-1-verify-1-codex`. Verify F-REVIEW-2026-11-22-t0023-1-1 and -2 and absence of regression in T-0023 tools and tests. The worktree matches the branch and head. The local head predates correction 1; the public `main` source supplies it. No licensed input, private research directory, Azure, or vendor URL will be read. Real-input reruns are author reports.

## Checks

1. Compare the assigned base and head, including merges, to establish the actual code, test and record changes. Do not treat the response as evidence.
2. For F-1, trace C5's declared six fund/year/accession tuples from the preregistration to the implementation. Check missing and duplicate rows, wrong fund/year/accession, and an otherwise passing incomplete set. Run targeted tests and, if needed, read-only synthetic probes.
3. For F-2, trace run selection and loading through every downstream consumer. Recalculate the panel identifier from validated inputs and panel bytes; check the rebuild flags and paired changes to panel CSV and run JSON. Check the seam output's panel identifier. Run targeted tests and synthetic probes.
4. Run the focused T-0023 tool tests against the frozen head. Inspect changed tests for power and identify any regressions or claim narrower than the code warrants.
5. Record each original finding as technically verified closed or still open, give a READY or NOT READY verdict limited to the assigned scope, and state all unverified real-input claims. Add only review records, a test-plan report and reviewer handoff under `reviews/`. Leave files uncommitted for the runner.

## Governing records

T-0023, OD-0184 A2, OD-0186 correction 1, the original `REVIEW-2026-11-22-t0023-1` findings, the preregistered T-0023 checks, and the approved return-accounting and rights standards. The source discrepancy would stop this review if the public `main` correction or Assigned reviews row differed from the assignment transcription; both matched on inspection.
