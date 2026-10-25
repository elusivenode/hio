---
id: RESPONSE-REVIEW-2026-10-25-adr0012-2
author: claude/implementation-agent
findings: [F-REVIEW-2026-10-25-adr0012-2]
responds_to: VERIFY-2026-10-25-adr0012-1   # reviewer commit e1f60f9e04034c5b9cb21ac8b3c77b93afc516ce (branch review/adr0012-verify-1-codex, not yet received); record blob 6e3848559a0f227224ff44ce91652a65c43ad512, sha256 4692c99f021f2ca9a1b965d33e0459495b93479f8ea35553490fa8023375d048 (read with git show, hash checked; OD-0052)
previous_submission_head: 860fd7879c6c663980bc4bf037a8c29e8c7df769
authorised_by: OD-0052
fix_commits: [cef81f07164c0902c6255897112903a1751ac84f]
test_commits: []   # documentation-only; no test applies
submission_head: self            # resolve: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-25-adr0012-2.md
created_at: 2026-10-25
---

# Remediation response 2: F2, provenance of post-window completion evidence

> **Author's claim, not verification.** F2 stays **open**. HIO-ADR-0012 stays **proposed**. F1 and
> F3 were verified closed by VERIFY-2026-10-25-adr0012-1 (`e1f60f9`, not yet received); this
> response does not reopen them. Only Codex may verify closure of F2, at a fixed head the owner
> assigns.

## Root cause

Revision 2 let an attempt record **assert** success, and finality accepted the assertion. Nothing
tied the record to a particular capture execution or to a response generated after the window.
The verifier's counterexample copied an old receipt's hash and length into a `verified_unchanged`
record, and every finality condition passed with no request after W_doc. Identical bytes cannot
prove when, or whether, a request was made.

## Fix (`cef81f0`; ADR §4.3.3 and §4.3.4 only)

- **Binding.** Each record carries the CI execution identity (`run_id`, `run_attempt`, the
  executed `sha`) and the **response envelope** as received, including the publisher's `Date`,
  plus the response hash and length. The record's key includes its content hash and is verified on
  read.
- **Seven completion checks (C1–C7)**, all required: integrity; response binding; content;
  **freshness from the publisher's own clock** (`Date` ≥ W_doc, so a cached pre-window copy
  fails); timing with a **provider-assigned write time**; execution binding; uniqueness.
- **Honest classification** of the evidence:
  - *replayable* from retained artefacts: C1, C2, C3, C7 and the arithmetic of C4 and C5;
  - *witnessed* outside HIO's bookkeeping: the publisher's `Date`, the store's write time, the CI
    run record, and the later-fetch re-check of a final value;
  - *trusted-adapter assertions*, not replayable: that the request was sent, that the envelope is
    the response's, and that the adapter's timestamps are truthful.
- **Stated limit.** The ADR says in so many words that **self-recorded events do not
  cryptographically prove network activity**, and names the adapter as a trusted component.
- **No second bookkeeping system.** One record type, checked against artefacts and witnesses that
  already exist. No signature, hash chain, ledger or second store. Any such mechanism would be a
  trust-model change and is not proposed.
- **Refusal** (§4.3.4): missing, failed, delayed (before W_doc, or stored after the cutoff),
  inconsistent and unverified evidence all fail closed, including a `platform: other` (manual or
  local) run and a dataset whose header and write-time behaviour is not evidenced.
- **Unchanged-response case:** accepted only through a fresh envelope plus C5–C7, with C2 and C3
  showing the bytes equal the held receipt's.

## Replay of the verifier's counterexample and its neighbours (paper trial against §4.3.3)

A cell shows whether the check passes (✓) or fails (✗). A failing check means the record is not
completion evidence.

| Case | C1 | C2 | C3 | C4 | C5 | C6 | C7 | Result |
|---|---|---|---|---|---|---|---|---|
| **Review's counterexample:** `verified_unchanged` copied from old receipt R, 16:30, no request; envelope copied from R (`Date` 09:45) | ✓ | ✓ | ✓ | **✗** `Date` < W_doc | ✓ | ✓ | ✓ | **refused** |
| Same, with a fabricated post-window `Date`, written 60 min later | ✓ | ✓ | ✓ | ✓ | **✗** write time − `completed_at` > δ | ✓ | ✓ | **refused** |
| Same, fabricated `Date`, written at the claimed time, with an invented run id | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ at build time | ✓ | **accepted at build time.** This is the **stated trust limit**: it needs the trusted adapter to lie consistently across three facts. An audit of the CI run history (no such run) and a later genuine fetch can expose it |
| Genuine unchanged check, 16:30 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | accepted |
| Genuine changed check (new vintage from `capture()`) | ✓ | ✓ | ✓ digest = the new vintage | ✓ | ✓ | ✓ | ✓ | accepted |
| Cached response, `Date` 15:58, `Age: 420`, fetched 16:05 | ✓ | ✓ | ✓ | **✗** | ✓ | ✓ | ✓ | refused; retry |
| `failed` record | n/a | n/a | n/a | n/a | n/a | n/a | n/a | refused (not evidence) |
| Check at 15:59 (before W_doc) | ✓ | ✓ | ✓ | **✗** | **✗** | ✓ | ✓ | refused (delayed rule: before the window) |
| Check stored after the build's cutoff | ✓ | ✓ | ✓ | ✓ | **✗** for that cutoff | ✓ | ✓ | refused for that cutoff; usable for a later one |
| No `Date` header | ✓ | ✓ | ✓ | **✗** | ✓ | ✓ | ✓ | refused |
| Manual or local run (`platform: other`) | ✓ | ✓ | ✓ | ✓ | ✓ | **✗** | ✓ | refused (unverified) |
| Two records, same run and source | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **✗** | refused (inconsistent) |
| Two records disagreeing about a key | n/a | n/a | **✗** | n/a | n/a | n/a | n/a | refused and quarantined pending owner review |
| Store without a provider write time | ✓ | ✓ | ✓ | ✓ | **✗** | ✓ | ✓ | refused (finality unavailable for that store) |

## Evidence

| Check | Result |
|---|---|
| Sections changed | **§4.3.3, §4.3.4** (rewritten), plus consequential lines: front matter, §4.2 gate (f), §8 item 5 and the changelog. §1, §2, §4.1, §4.3.1, §4.3.2, §4.3.5, §4.4–§4.7 and *Approval* are **byte-identical** to the verified head `860fd78` (compared section by section) |
| Accepted S1a, standards, harness-0.7, ADR-0010, `registers/` | unchanged (`git diff --stat 084154c HEAD -- src tests tools specs .github pyproject.toml uv.lock` and `git diff --stat main -- docs/standards docs/harness registers` are empty). Every source permission is still `unverified` |
| `capture()` | unchanged. An identical consecutive re-fetch still writes no capture record (`src/hio/marketdata/capture.py:98-99`) |
| Repository checks | `tools/check_repo.py` PASS; `ruff` clean; `pytest` 278 passed (see the handoff) |

## Escalations and open items (none decided here)

1. **Q-013** and the **release-manifest schema** question stay unresolved, as the owner directed.
   The verifier noted both as separate dispositions needed before implementation.
2. **Trust model.** This response makes an existing assumption explicit (the capture adapter is
   trusted). Any stronger mechanism (signatures, a hash chain, third-party attestation) would
   change the trust model, and is **not proposed**.
3. **Per-source evidence.** That `Date`, `Age` and the store's write time behave as assumed is not
   evidenced for any S1b source. It is a gate item (§4.2 (d2), (f)), not a claim.
4. **The CI-run audit** (C6) is an owner or auditor action. It is specified, not performed.

## Not claimed

- That F2 is closed, or that any finding is verified by this response.
- That the ADR is approved, that any source right is verified, or that S1b is authorised.
- That the attempt records are implemented. They are specified in a proposal.
- That the trusted-adapter assumption is removed. It is stated and bounded.
