---
id: HIO-APPROVAL-PACKAGE-2026-10-25
title: "Approval package: HIO-ADR-0012 (staged S1b) and harness-0.7.1 (review-evidence delivery): two separate owner decisions, with the safe integration sequence"
status: prepared_for_owner   # NOT approval. Neither proposal is approved by this file
owner: owner (decides); prepared by claude/implementation-agent
created_at: 2026-10-25
prepared_under: OD-0054
---

# Approval package

> **Prepared for the owner. Neither decision is made here.** Each decision below is separate and
> is recorded by the owner in its own OD citing the **exact revision**. Approving one does not
> approve the other.

## At a glance

| | Decision 1: HIO-ADR-0012 | Decision 2: harness-0.7.1 |
|---|---|---|
| What is approved | the design of staged S1b (S1b-1 cash legs; S1b-2 FX; independent triangulations) | review evidence delivered by a pushed branch with no reviewer PR, received by a byte-identical import with a verified provenance tag |
| Exact revision | branch `docs/adr0012-staged-s1b-proposal`, commit `d0965ccfd37a0ddefdbb5ff08a11674c3267792a`; file `docs/decisions/HIO-ADR-0012-staged-s1b.md`, blob `eb110ee394afa5b3a8abe612cf2e22196acbf51c` | branch `proposal/harness-0.7.1`, commit **C1** `552d4fbde6f4256bf969b908d721a765aae84e17`; file `docs/harness/operating-model.md`, blob `a74a41453d10b54161136ff08ac36e6ca86f33bc` (from approved blob `920b1bb153bf7ffaf3a8356a7486b2fa86c5be3f`). Optional **C2** `8461e99639f0ee7bc8cb9de2895d00d257d12974` |
| Independent verification | F1, F3 closed at `860fd78` (`e1f60f9`); F2 closed at `d0965cc` (`dac54f5`) | F1–F4 closed at `8ed13fd` (`4682c98`), a mechanical equivalent of C1 (below) |
| Verdicts | READY WITH CONDITIONS | READY WITH CONDITIONS |
| Effect on approved documents | supersedes only HIO-ADR-0010 rev 3's S10-B2 and S10-B5, and S10-B8(ii)'s wording if the FX source is not RBA F11 | replaces §6.2's preamble sentence and steps 3, 4, 5 and 6; with C2, two conforming lines |
| Does not decide | Q-013, the release-manifest schema, header semantics, any source right, S1b | any finding's acceptance beyond the technical closure already adopted |

---

## Decision 1: approve HIO-ADR-0012 at an exact revision

### Provenance
- ADR file `docs/decisions/HIO-ADR-0012-staged-s1b.md`, **revision 3**, `status: proposed`, blob
  `eb110ee394afa5b3a8abe612cf2e22196acbf51c` at commit `d0965ccfd37a0ddefdbb5ff08a11674c3267792a`.
  Base `main` `6fbec1aa064551d7aa505cf3008a677acfd68e73`. PR #4 (open), CI green.
- Lineage: revision 1 `1d68da3` → REVIEW-2026-10-25-adr0012 (REQUEST CHANGES; received, OD-0050,
  tag `reviews/REVIEW-2026-10-25-adr0012`) → revision 2 `860fd78` → VERIFY-2026-10-25-adr0012-1
  (F1, F3 closed; F2 open) → revision 3 `d0965cc` → VERIFY-2026-10-25-adr0012-2 (F2 closed).
- Records (all **unreceived**): `e1f60f9…` and `dac54f55…`. OD-0054 holds their hashes.

### What approval would do
- ADR-0012 becomes approved policy, with the §3 invariants (S1a, return mathematics, observation
  invariants, evidence integrity, release integrity, the HIO/`macsmsf` boundary) unchanged.
- Per its §2, it **supersedes only** HIO-ADR-0010 rev 3's S10-B2 (inclusions) and S10-B5 (entry
  gate), plus S10-B8(ii)'s wording if the FX source is not RBA F11. The S1a column and S1a
  acceptance (OD-0042) are untouched, and every S1b obligation is kept and re-mapped (§5).

### Independent gates: approval opens none of them
| Gate | Where it stands |
|---|---|
| **Q-013**: the capture-instant reading of `captured_on_schedule` for a first capture | open; the ADR stands without it, falling back to `schedule_only` (P3) |
| **Release-manifest schema**: whether finality evidence ids can be release inputs | open; an amendment of the releases standard if not |
| **Publisher header semantics**: `Date`, `Age`, provider write time, per dataset | not evidenced; examining it needs an owner-approved fetch; without it a dataset has **no finality** |
| **Source rights**: `owner_verified` per dataset and operation | all `unverified`; the verification matrix holds recommendations only |
| **Network and credential controls** (OD-0038); bucket and keys | undecided |
| **S1b-1 and S1b-2 authorisation**; the FX-source decision | not given |

### Implementation prerequisites (before any S1b code)
1. S1b-1's entry gate (a)–(g) and (d2), (d3) in the ADR §4.2, including the owner's decisions above.
2. An owner-authorised, opt-in change to accepted S1a placement only if Q-013 is decided for P2.
3. A task card and a separate authorisation for the S1b-1 scope and infrastructure.

### Stop conditions
- any change to the return mathematics, an approved standard, or the S1a release hashes;
- any need to alter `capture()` or another accepted S1a function (it needs its own authorisation);
- finality labelling while the manifest question or the header evidence is open;
- use of any series whose permissions are not `owner_verified`.

### Draft decision text (for the owner to adopt, amend or refuse)
> I approve HIO-ADR-0012 revision 3 as at commit `d0965ccfd37a0ddefdbb5ff08a11674c3267792a`, file
> blob `eb110ee394afa5b3a8abe612cf2e22196acbf51c`. It supersedes only HIO-ADR-0010 revision 3's
> provisions S10-B2 and S10-B5, and the wording of S10-B8(ii) if the FX source is not RBA F11. This
> adopts the technical verification of F-REVIEW-2026-10-25-adr0012-1, -2 and -3 recorded in OD-0054.
> It does not decide Q-013, the release-manifest schema, publisher header semantics, any source
> right, or authorise S1b-1 or S1b-2.

### After approval (status-only edits, as for ADR-0010)
The ADR's `status`, `approved_by` and *Approval* section; the decisions register row; a status note
on HIO-ADR-0010 recording the partial supersession; `STATUS.md`. Check by `git diff` that only status
lines changed.

---

## Decision 2: approve harness-0.7.1 at an exact revision

### Provenance
- The amendment package: `docs/decisions/harness-0.7.1-proposal.md` **revision 3**, blob
  `72deffc37a4c58f8fb9ea04ce4ab6ba2aa994e6f` at commit `8ed13fdef8537b846afb7e60b14807417b2f3c0d`
  (branch `docs/harness-0.7.1-review-receipt`). Verified by VERIFY-2026-10-25-harness-0.7.1-1
  (`4682c98`): **F1–F4 closed**, READY WITH CONDITIONS.
- The text to be approved, applied to the real file: `proposal/harness-0.7.1` commit **C1**
  `552d4fbde6f4256bf969b908d721a765aae84e17`. It applies the package's replacement text
  **mechanically**: each of the five anchors matched exactly once, and the matching is
  whitespace-tolerant because step 6's phrase wraps across a line in the approved file. Only
  `docs/harness/operating-model.md` changes (blob `920b1bb…` → `a74a414…`).

### Exact operating-model changes (C1)
| Where in §6.2 | Change |
|---|---|
| Preamble sentence | "merging a reviewer PR is receipt, never acceptance" becomes "receipt (step 5) is evidence delivery, never acceptance. Reviewers do not open PRs." |
| Step 3, last two sentences | the reviewer pushes the branch and **opens no PR**; its **final message** is the independent report (branch, tip SHA, reviewed head, sha256 of every added file) |
| Step 4, first sentence | the scope check is run by the **receiver** from `main`'s copy of `tools/check_review_branch.sh` against the pushed branch, not by CI on a PR |
| Step 5 (entire) | replaced by **receipt by byte-identical import**: 5.0 inputs (owner assignment source, reviewer report, conflict search); 5.1 tip resolution; 5.2 two-way inventory; 5.3 checks; 5.4 tag first; 5.5 import; 5.6 index-row classes N and S; 5.7 verify; 5.8 pure import commit; 5.9 final recheck then merge; 5.10 complete only when verified; 5.11 recovery table; the accountability statement; the stop conditions |
| Step 6, first phrase | remediation is on the work's own author branch at a new `Submission-Head`, which Claude states |
| Front matter (status-only on approval) | `status`, `version`, `changelog` |

**Unchanged:** steps 1, 2, 4a, 7, 8 and 9; `tools/`; `.github/` (the `review-scope.yml` workflow
becomes dormant, because there are no reviewer PRs; removing it is a separate change to accepted
content); accepted S1a; every approved standard.

### Not covered by Codex's verification: C2 (optional, separate)
`proposal/harness-0.7.1` commit **C2** `8461e99639f0ee7bc8cb9de2895d00d257d12974` changes two lines
that still assume reviewer PRs:
- `AGENTS.md` (blob `6eb9f76668149986c8a0fb0677b1e55218334719`): the Codex bullet "Push the branch
  and open a PR stating `Reviewed-Head`" becomes "open no PR" plus the final-message report.
  **This line is the practical source of reviewer PRs.** Left unchanged, Codex keeps opening them.
- `reviews/README.md` (blob `921406e221281c8d07c670ec78566e56b0cbd0e2`): "merges reviewer PRs
  (receipt only)" becomes "receives reviewer evidence by byte-identical import".

These are mechanical conformance edits that Codex did not verify. **The owner approves C1, and
separately decides whether C2 is included.** Recommended: include C2.

### First-use validation (the condition Codex named)
Until it is recorded as passed, **routine delegation to Claude (package §3, item 3) is suspended**:
each receipt needs the owner's go-ahead before anything is pushed to `main`.

1. **The first receipt under 0.7.1 is a supervised run.** Claude performs 5.0 to 5.8 in a scratch
   clone and produces a transcript: the cited assignment source, the parsed tip, the two-way
   inventory, the scope and assignment results, the tag verification, the row-by-row index
   comparison, and the blob comparison.
2. **The owner reviews the transcript** and says "proceed". Only then are the tag verified, `main`
   merged (5.9) and pushed.
3. **Any step that needs improvisation stops the run** and returns the amendment to the owner as a
   new revision. It is not patched in flight.
4. **The first use is recorded in an OD** listing any unclear or failed step. A clean first use
   lifts the suspension.
5. **Suggested first use:** VERIFY-2026-10-25-adr0012-2 (`dac54f5`). Its assignment source exists,
   and it needs only one index change, a single Class S row for F2. It does need Codex's report
   (tip and sha256 of each added file) relayed, or an owner statement that the prefix plus the
   computed hashes suffice.
6. **A known stop to expect later:** the `e1f60f9` index diff does not apply to `main` or to PR
   #4's head (tested), so its receipt stops at 5.5 by design (OD-0054).

### Prerequisites and stop conditions
- The amendment takes effect only when C1 is merged. Until then harness-0.7 governs, and the
  one-off exceptions already recorded remain the only route.
- Stop if a receipt would make a reviewer commit an ancestor of `main`, if any 5.0 input is absent,
  if an index row falls outside Class N or Class S, or if any tool or workflow change would be
  needed (that is a separate authorisation).

### Draft decision text
> I approve the harness-0.7.1 amendment as applied in commit
> `552d4fbde6f4256bf969b908d721a765aae84e17` (`docs/harness/operating-model.md`, blob
> `a74a41453d10b54161136ff08ac36e6ca86f33bc`), derived from the package at commit `8ed13fd…` (blob
> `72deffc37a4c58f8fb9ea04ce4ab6ba2aa994e6f`) and verified by VERIFY-2026-10-25-harness-0.7.1-1.
> [I also approve / I do not approve] commit `8461e99639f0ee7bc8cb9de2895d00d257d12974` (AGENTS.md
> and the review index). Adoption is conditional on a supervised first use recorded in an OD;
> routine delegation of receipt is suspended until then. This waives no finding and approves no
> earlier exception.

---

## Safe integration sequence (no unapproved ancestry through reviewer branches)

**The rule.** A reviewer branch is cut at the head it reviews, so its ancestry is the author's
proposal. **A reviewer branch is never merged into `main`.** Evidence is received by import, and
the stop condition is any step that would make a reviewer commit an ancestor of `main`.

| Step | Action | Why here |
|---|---|---|
| 0 | **Now:** nothing is merged. The author branches, `proposal/harness-0.7.1` and the records branches are pushed; the four reviewer branches are untouched | the starting point |
| 1 | The owner records Decision 1, Decision 2 and the disposition D0 (OD-0054), each in its own OD | separate decisions |
| 2 | Status-only approval commits on the approved branches (ADR status and register row; the operating model's `status`, `version`, `approved_by`, changelog). Check that only status lines changed | the harness-0.7 pattern (9b58811 then 3ebeb21) |
| 3 | The owner merges the **author** work `--no-ff`, in this order: (a) PR #4's branch; (b) `docs/harness-0.7.1-review-receipt`; (c) `proposal/harness-0.7.1`; (d) the records branches `docs/od0053-…` and `docs/od0054-…`. Expected conflicts are index rows only (owner and history indexes, `STATUS.md`, `open-decisions.md`), resolved by keeping both sides. OD-0052 is byte-identical on (a) and (b) | PR #4 first, so that `main`'s finding rows carry the claim rounds the closure rows rewrite. The operating model last, so the new procedure takes effect only after the author merges |
| 4 | Pin each reviewer commit with an annotated tag `reviews/<id>`, with no import | harmless and recoverable |
| 5 | **Receive** the evidence by import under the now-effective 0.7.1, the **first use supervised**. Dependency order: `dac54f5` (first use); `9c51a6b` (under D0, since its rows must exist before `4682c98` can transition them); `4682c98`; `e1f60f9` last, or left unreceived | index rows must exist before a verification can transition them |
| 6 | The receiver runs the receipt sweep and reports any review branch not received or dispositioned | silence becomes visible |

**Why not merge the reviewer branches even after step 3.** After step 3 their ancestry is in `main`,
so a merge would no longer bring unapproved content. It is still wrong here: the approved procedure
is import; the earlier `1a05d8e` was already imported, so a later merge would collide; and a merge
would carry the reviewer's index edits in unvalidated.

## Not decided here
Q-013; the release-manifest schema; publisher header semantics; every source right; S1b-1, S1b-2
and the FX source; the network, credential and bucket decisions; the receipt dispositions in D0.
