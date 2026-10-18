---
id: HIO-PENDING-DECISIONS
title: Pending owner decisions (revision-specific)
status: current            # a decision aid; nothing here is approved
owner: owner (decides); prepared by claude/documentation-agent
last_reviewed: 2026-10-18
authorised_by: OD-0010
---

# Pending owner decisions

> Each decision applies to the exact blob named. Verify with
> `git rev-parse <commit>:<path>`. **Nothing here is approved until you say so in your own
> words.** Claude then records it in an OD.

## Decision A: HIO-ADR-0010 revision 3 (completes G1)

| Field | Value |
|---|---|
| File | `hio/docs/decisions/HIO-ADR-0010-first-slice-scope.md` |
| Blob | `8ade1962cf283a11470e1a199309f12610981dc1` |
| Commit | the commit that adds this file (resolve: `git log -n1 --format=%H -- hio/docs/decisions/pending-owner-decisions.md`). The owner-facing report also states it |
| History | rev 1 (blob `fe651aca746d`, at `a82aa0d`), returned by OD-0008; rev 2 (at `f2275e2`); **rev 3**, which corrects the S1a gate per OD-0010 |

**Changed text in rev 3** (S1a entry gate):

> **G1 complete** (including approval of this revised ADR) **and a future, separate owner
> authorisation of S1a's scope**, recorded in its own owner decision record. OD-0009
> *requires* that authorisation; it is **not** that authorisation, and no record yet
> authorises S1a.

The rest of rev 2 is unchanged:
- S1a: synthetic-fixture-only, with no network access, real sources, credentials or buckets;
- S1b: live data, gated on S1a acceptance, T-0002 `owner_verified` rights per operation, and a
  separate S1b authorisation.

**Decision sought:** approve, revise or defer rev 3 at blob `8ade1962cf28`. Approving it
completes G1. **It does not authorise S1a.**

## Decision B: harness-0.6 amendment (explicit approval)

| Field | Value |
|---|---|
| File | `hio/docs/harness/operating-model.md` |
| Approved earlier | blob `7172659cf4ba` at `a82aa0d` (harness-0.5), by OD-0008 |
| **Amended revision** | blob **`e3114bd188ad525d07bd02efede38f35c2103573`** at commit **`f2275e274e2cc69cb9219fcf62184ce65e8e257c`**. It is unchanged since; check with `git diff f2275e2 HEAD -- hio/docs/harness/operating-model.md`, which should be empty |
| Companion line | `hio/reviews/README.md` "Who writes what", at `f2275e2` |

**Changed text, content (the amendment):** §6.2 step 3 adds one bullet.

```diff
    - the reviewer's own session handoff in `reviews/handoffs/`, since its other handoff
      locations are out of bounds;
+   - reviewer opinion or readiness reports in `reviews/reports/`. These are supporting opinion;
+     the records stay authoritative (harness-0.6, OD-0009);
    - its own rows in `reviews/README.md`.
```

The companion line in the review index:

```diff
- - **The reviewer (Codex):** review records and verification records (`records/`), its
-   handoffs (`handoffs/`), and its own index rows.
+ - **The reviewer (Codex):** review records and verification records (`records/`), its
+   handoffs (`handoffs/`), opinion or readiness reports (`reports/`), and its own index rows.
```

**Changed text, status-recording** (part of the same blob; listed so that the approval covers
the whole file). Each replaces "provisional" wording, or records OD-0008:
- front matter: `status: approved`, `approved_by`, `version: harness-0.6`, and the harness-0.6
  changelog line;
- §1.1: the "Provisional working protocol (bootstrap)" paragraph is replaced by "Bootstrap
  history" (the protocol operated provisionally until G1; OD-0008 approved it; the
  owner-instruction rule for a first bounded task still stands);
- §1.1 precedence row 3: "the provisional working protocol | recommendation, or provisional
  procedure only" becomes "| recommendation only";
- §6.2 status: "adopted into the provisional working protocol (OD-0003). HIO-ADR-0008 is still
  proposed" becomes "adopted (OD-0003); accepted at `b48f83c` (OD-0004); approved by OD-0008 at
  `a82aa0d`; `reports/` added by harness-0.6 (OD-0009)".

The full diff: `git diff a82aa0d f2275e2 -- hio/docs/harness/operating-model.md hio/reviews/README.md`.

**Decision sought:** approve, revise or reject the operating model at blob `e3114bd188ad` (commit
`f2275e2`), which is harness-0.6, together with the companion index line.

## Not pending here

- S1a and S1b authorisations: these are future, separate decisions.
- The T-0004 merge: after REVIEW-2026-10-18-t0004.
- The factor specs, roadmap and plan: these stay drafts and recommendations by your decision.
