---
id: HIO-ADR-0012-VERIFICATION-ASSIGNMENT-DRAFT
title: "Draft Codex verification assignment for the HIO-ADR-0012 remediation (F1-F3), for the owner to issue or amend"
status: draft   # NOT an assignment. Only an owner-authored source assigns a review (operating model §6.2 step 1)
owner: owner (assigns); drafted by claude/implementation-agent
created_at: 2026-10-25
drafted_under: OD-0051
---

# Draft verification assignment: HIO-ADR-0012 remediation

> **Not an assignment.** The head cannot be written here, because a file cannot contain its own
> commit id. It is the commit that adds `reviews/responses/RESPONSE-REVIEW-2026-10-25-adr0012-1.md`
> on branch `docs/adr0012-staged-s1b-proposal`, and the owner states it in the assignment.

## Proposed assignment values

| Field | Proposed value |
|---|---|
| Verification id | `VERIFY-2026-10-25-adr0012-1` |
| Repository | `elusivenode/hio` |
| Base SHA | `6fbec1aa064551d7aa505cf3008a677acfd68e73` (`main`, containing the received review) |
| Head SHA | the PR #4 head after the remediation: `git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-25-adr0012-1.md`, stated in the owner's assignment. Fixed; never rebased or force-pushed during verification |
| Previous reviewed head | `1d68da3e90d879da6318082551bab943c60cf68b` |
| Review branch | `review/adr0012-verify-1-codex`, cut at the head |
| Reviewer | Codex, independent reviewer |
| Delivery | as the owner decides: harness-0.7 (a reviewer PR), or the **push-only pilot** of harness-0.7.1 if the owner authorises that exception for this verification too |
| Writes allowed | `.md` files under `reviews/` only |

## Scope (bounded)

**Verify, independently of the response,** that each of F-REVIEW-2026-10-25-adr0012-1, -2 and -3
is closed at the head, by writing the failure scenarios from the record yourself and running them
against the new ADR text. Record each as `verified_closed`, `remediation_rejected` or still open.

1. **F1.** Does any path still give a vintage a `knowable_at` earlier than evidence supports?
   Check §4.3.1 P1/P2/P3 against observations §3 and `src/hio/marketdata/knowability.py`. Is P1
   guarded (semantics evidenced first; an instant later than `captured_at` refused)?
2. **F2.** Can a release be labelled final without a verified post-window record? Try failed,
   missing, parse-failed, key-missing and unchanged-content cases, and a cutoff between W_doc and a
   late check. Is the unchanged case evidenced given `capture()` writes nothing for an identical
   re-fetch (`capture.py:98-99`)? Is `capture()` left unchanged?
3. **F3.** Are the SOFR and SOFR Index rules separate, and is an independent Index check required
   in every case? Does `cash.usd` finality depend on SOFR only?

**Also check, because the remediation is large enough to need it:**
4. **No scope creep.** Compare the ADR against the reviewed head `1d68da3` section by section:
   are §4.1 and §4.4–§4.6 unchanged, and is §2's supersession table unchanged? Does any new text
   change approved return mathematics, an approved standard, S1a behaviour, or a rights value?
5. **The escalations are honest.** Is Q-013 correctly characterised as a clarification of
   approved semantics plus an opt-in S1a change, and does the ADR stand without it (P3)? Is the
   release-manifest escalation (§4.3.4) necessary?
6. **New defects.** Does the attempt-record design (§4.3.3) weaken any evidence-integrity
   guarantee, or create a new failure mode (for example an attempt record claiming a check that
   did not happen)?

**Out of scope:** approving the ADR; verifying any right; the FX source; S1b implementation.

**Output:** a `VERIFY-2026-10-25-adr0012-1` record with a verdict and per-finding states, any new
findings as `F-REVIEW-2026-10-25-adr0012-N`, `Reviewed-Head` stated, and — in the final message —
the review branch tip SHA and the sha256 of each file added.
