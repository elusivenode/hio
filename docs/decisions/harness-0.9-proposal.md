---
id: HIO-HARNESS-0.9-PROPOSAL
title: "Decision package: harness-0.9, a knowledge layer and lighter mechanics for a long-lived two-agent project, proposed, revision 4"
status: proposed   # no effect until the owner approves an exact revision (operating model §6; AGENTS.md rule 3)
owner: owner (decides); drafted by claude/implementation-agent
created_at: 2026-10-28
drafted_under: [OD-0068, OD-0070, OD-0080]
revision: 4   # rev 1 = 5f55cc7 (dry-run reviewed); rev 2 = f5ce1b8beaaaed59fbcbccf586892ac9ae1cf261 (solution-architect assessed); rev 3 = 50e7229 (the owner's adopted direction, OD-0070); rev 4 refreshes the seeds and adds the 2026-10-28 session evidence (OD-0080, §14)
amends: "Phase A: AGENTS.md, operating model §1, §1.1, §2.1, §3, §4, §8, §12, templates/handoff.md, the hio-session skill, README.md; adds MAP.md and knowledge/findings.md. Phase B (later, separately approved): operating model §2.2, §6.2, tools/, CI"
---

# Decision package: harness-0.9 (knowledge, continuity, lighter mechanics)

> **No effect until approved.** The approved harness is harness-0.7.1 with correction 1
> (`docs/harness/operating-model.md` on `main` at `16ea0c6`). This package edits nothing approved.
> Its Phase A text is in Appendix A, so the owner can approve an exact revision of it.
>
> **Direction adopted, text not approved.** The owner adopted the solution architect's disposition
> (ADOPT WITH CHANGES), qualified by Claude's response and the owner's own adjudication (OD-0070).
> That fixes the *direction* of this revision. Approval of the *text* is a separate owner action
> at an exact revision (`AGENTS.md` rule 3).
>
> **Reviews so far:**
> - a same-vendor dry run of revision 1
>   ([report](../../reviews/reports/REPORT-2026-10-28-harness-0.9-fable-dryrun-1.md); advice under
>   operating model §10);
> - the solution architect's assessment of revision 2
>   ([verbatim](../history/2026-10-28-solution-architect-harness-0.9-assessment.md));
> - Claude's response to that assessment
>   ([verbatim](../history/2026-10-28-claude-response-to-solution-architect-harness-0.9.md)).
>
> None of these is an independent Codex review. §9 says which items need one.

## Contents

1. The problem, measured
2. What harness-0.9 is for: three kinds of memory
3. What does not change
4. Dispositions, H1 to H11
5. Phase A: scope, manifest and boundary
6. Phase B: items and design
7. H7 in detail: a candidate standing publication delegation
8. Sequencing against T-0009
9. Verification requirements and success criteria
10. Authority analysis
11. Risks, residual risks and rollback
12. Outstanding owner decisions
13. Changes from revision 2

Appendix A: exact Phase A text. Appendix B: H7 evidence schema and Codex negative cases.

---

## 1. The problem, measured

The owner's goal (OD-0068): a long-lived project in which Claude and Codex keep long-term context
and alignment, and knowledge builds up rather than being rediscovered.

The current harness proves well **who authorised what, at which revision**. It records
*governance* memory thoroughly, but not *engineering* memory. Its mechanics are costly relative
to the work they govern. Measured on 2026-10-28; the base of each figure is stated:

| Measure | Value |
|---|---|
| Commits | `main` at `eb19ef7`: 208, of which 168 non-merge. All refs: 186 non-merge, of which 37 touch `src/` or `tests/` |
| Lines added, governance records only (`reviews/`, `handoffs/`, `docs/decisions/`, `docs/history/`, `docs/harness/`, `registers/tasks/`, `STATUS.md`, `AGENTS.md`) vs `src/` + `tests/` | `main` at `eb19ef7`: 22,208 vs 9,230 (about 2.4 : 1) |
| Lines added, all of `docs/` + `reviews/` + `handoffs/` + `registers/` vs `src/` + `tests/` | all refs: 28,573 vs 11,695. `docs/` includes substantive work (standards ≈ 2,600, evidence ≈ 1,000, research ≈ 870 lines), so the total is not all overhead |
| OD records / verbatim history files / dated handoffs / review records (`main` at `eb19ef7`, excluding READMEs) | 63 / 69 / 47 / 22 |
| `operating-model.md` | 8,440 words; §6.2 (review branch protocol) alone is 3,012 words |
| `STATUS.md` before OD-0069 | 93 lines; longest line 2,729 characters (an OD history packed into a table cell). After OD-0069: 101 lines; longest line 384 characters |
| Hypotheses / experiments registered | 4 / 0 |
| Lessons and dead ends | scattered through ODs and handoffs (for example OD-0058, "nothing local would have caught it"); no class or index for them |

**Baseline for measurement** (dry run, rev 1, `5f55cc7`): the current bootstrap path (AGENTS,
STATUS, task card, review index) read 5,280 words. It gave one wrong answer (the next action) and
one misleading answer (S1b authorisation), and could not reach two knowledge questions (why S1b
specs must not reuse S1a spec files; whether the capture clock has started). The proposed path
read 4,384 words and answered all of them. A same-vendor dry run is advice, not the §10 test (§9
below).

**Five failures:**

1. **No big picture in the read path.** `AGENTS.md` → `STATUS.md` → task card → OD give rules and
   state. None says what HIO is trying to learn or what the active threads serve.
2. **Engineering knowledge is lost or buried.** The 2026-10-25 handover was 190 lines, mostly
   procedure and SHAs, and its few durable facts lived only in `~/Downloads`. Operating model §0
   already names that pattern as a defect.
3. **Current state disagreed with itself on `main`.** *Resolved by OD-0069* (merge `16ea0c6`).
   The T-0009 authority records and card are now on `main`, and `STATUS.md` is current. It is
   kept here as evidence of the failure mode that H7 addresses. **Still open:** the HIO-ADR-0012
   findings -1 and -3 read `remediation_claimed` in `reviews/README.md` but "technically verified
   closed" in OD-0054. `STATUS.md` now states this explicitly.
4. **Deterministic mechanics are prose.** Assigning and receiving one two-file review
   (`REVIEW-2026-10-25-t0009-1`) took OD-0066 and OD-0067, two transcripts, a tag, a receipt
   branch, index rows and five commits and merges. Each agent rereads 3,012 words to do it by
   hand.
5. **Codex starts cold every time.** Its independence is protected, correctly, but it keeps no
   knowledge between reviews.

Operating model §12 sets the test: "the harness must save more owner time than it costs".

## 2. What harness-0.9 is for: three kinds of memory

Adopted from the solution architect's assessment (§3), by OD-0070 point 1:

| Memory | Holds | Canonical home | Needs |
|---|---|---|---|
| **Governance** | owner instructions, authority, approvals, reviews, acceptance | OD records, approved standards and ADRs, task cards, review records | strong provenance; explicit authority; revision integrity (unchanged by Phase A) |
| **Engineering** | technical discoveries, defect patterns, failed approaches, traps, reasoning | `knowledge/findings.md` (new, H2); Codex's `reviews/knowledge/` (H11, Phase B) | easy to add; easy to find; no owner decision per observation |
| **Research** | hypotheses, experiments, negative results, data limitations, modelling assumptions | `registers/hypotheses.yaml`, `registers/experiments.yaml` (operating model §4) | pre-registration; why an approach was rejected, not only that it failed |

Harness-0.9 connects them. It does not merge them or make one an authority over another. The
findings index may point to an experiment, but never restates its conclusion.

**Success criterion** (from the solution architect's assessment, §3). A fresh agent, or a future
model, can:
1. understand HIO's purpose and architecture;
2. establish the current authoritative state;
3. identify the exact work it may do;
4. find relevant engineering and research knowledge;
5. tell proven facts from unverified claims;
6. resume with bounded context cost;
7. know when to stop rather than infer authority.

§9 makes this measurable.

## 3. What does not change

- **Authority model** (§1.1): the four owner actions; "availability is not authority";
  stop-and-flag; self-declaration. Phase A adds navigation files to precedence ranks 5 and 6 only.
- **Codex's bootstrap and review protocol** (`AGENTS.md` "Then, by role → Codex"; operating model
  §2.2, §6.2). Phase A leaves them exactly as approved (OD-0070 point 4). Codex is not required to
  read `MAP.md` or the findings index until H11 is reviewed and approved. It may read them under
  the existing rule that author-written material comes after its test plan.
- **Review evidence**: byte-identical import, the provenance tag and the receipt OD required by
  OD-0061.
- **Owner-record requirements**: every owner action keeps its OD and verbatim transcript (H5 is
  deferred).
- **CI and tools**: Phase A changes no check. Its new paths already satisfy
  `tools/check_repo.py` (`MAP.md` and `knowledge/*.md` match the canonical front-matter rule;
  `handoffs/<stream>/*.md` match `^handoffs/.+\.md$`).
- **T-0009**: OD-0067's remediation authorisation is neither broadened nor reinterpreted; no
  harness change enters its branches.
- Data rights, secrets, the `macsmsf` boundary, the return accounting standard.

## 4. Dispositions, H1 to H11

| Item | Disposition | Phase | Owner action | Codex review |
|---|---|---|---|---|
| **H1** `MAP.md` | **adopt**: a projection with no operational state; substantive changes owner-approved, mechanical corrections by a stated rule | A | approve Appendix A | no |
| **H2** `knowledge/findings.md` | **adopt**, with applicability and freshness; Settled vs Inbox; threshold is a signal, not a gate | A | approve Appendix A | no |
| **H3** `STATUS.md` current-state only | **adopt the text rules** in A (no rewrite of the current, correct `STATUS.md`); **CI caps in B** | A + B | A: Appendix A. B: approval at its revision | B: yes |
| **H4** per-session handoffs by stream | **adopt**: *Didn't work* and *For the index*; rollover is a practice, not a gate | A | approve Appendix A | no |
| **H5** tiered owner records | **defer** until H6 has operated; tier-2 exclusions widened | later | a separate decision | yes, if revived |
| **H6** scripted assignment and receipt | **adopt**: the preferred Phase B mechanism | B | work authorisation; approval of the §6.2 amendment | **yes**, with deliberate failures |
| **H7** standing publication delegation | **design candidate**: separates the three properties (§7); timing is the owner's choice; never above T-0009 or a prerequisite for Phase A | B | a tier-1 delegation OD, after Codex review | **yes**, adversarial, before approval |
| **H8** hooks | **defer**: after branch protection; a guard against mistakes, not a control | B (last) | branch protection; later, authorise the hooks | yes |
| **H9** measurement | **adopt, simplified**: `[rediscovery]` tag; owner minutes per review cycle; the §10 cold-start test | A | approve Appendix A | not applicable |
| **H10** | **removed** (folded into H4 in revision 2) | — | — | — |
| **H11** Codex continuity | **adopt** with applicability discipline; **out of Phase A** | B | approval of the §2.2 and §6.2 amendments | **yes** |

## 5. Phase A: scope, manifest and boundary

### 5.1 What Phase A is

A small, exact **harness amendment**, proposed version **`harness-0.9a`**. It is documentation
only, but it edits approved onboarding text, so it needs the owner's **approval at an exact
revision** (OD-0070 point 3; operating model §6, "Harness change … approved by owner … harness
version bump"). It changes no control, so it needs **no Codex review**.

Approving this package's Appendix A at a stated commit approves that text. A later commit applies
it verbatim, with the version bump and changelog line, as harness-0.7.1 was applied (OD-0056). Any
difference between Appendix A and the applied text is a stop.

### 5.2 Manifest

| # | Path | Change | Approval state today | Why Phase A needs it |
|---|---|---|---|---|
| A1 | `MAP.md` | **new**: seed at this revision | — | H1 |
| A2 | `knowledge/findings.md` | **new**: seed of 20 Inbox lines at this revision | — | H2 |
| A3 | `AGENTS.md` | Claude's role bullet: read `MAP.md` and the stream's newest handoff; `grep` the findings index. Ending: stream path and *For the index*. Front matter version | approved, OD-0056 (`AGENTS.md` l.5) | puts H1, H2 and H4 on the non-reviewer read path |
| A4 | `docs/harness/operating-model.md` | §1 three rows; §1.1 precedence ranks 5 and 6; §2.1 knowledge-layer paragraph; §3 handoff path and two fields; §4 boundary paragraph; new §4.1 (H1, H2, H9 rules); §8 one quarterly check; §12 durable row; front matter and changelog | approved, OD-0056 and OD-0059 | the canonical rules for H1 to H4 and H9 |
| A5 | `templates/handoff.md` | `stream:` field; *Didn't work*; *For the index* | the template governed by operating model §3 | H4 |
| A6 | `.claude/skills/hio-session/SKILL.md` | start: `MAP.md` and the stream handoff for non-reviewers; end: stream path and *For the index* | the skill named in operating model §2 | keeps the skill consistent with A3 |
| A7 | `README.md` | the "Start here" line | current navigation index | keeps the entry page consistent |

### 5.3 Outside Phase A (explicitly)

- `STATUS.md` content is not rewritten. It is already current-state (OD-0069), and the H3 rules
  are in A4.
- `AGENTS.md` "Then, by role → Codex", operating model §2.2 and §6.2, `reviews/README.md` and
  `reviews/` paths: unchanged (H11 is Phase B).
- `tools/`, `.github/`, `templates/owner-decision.md`, `.claude/settings.json`: unchanged.
- The 47 existing dated handoffs: unchanged and not migrated.

### 5.4 Maintenance rules introduced by Phase A (proportional)

- **MAP, substantive changes:** any change to a claim about purpose, pillars, architecture,
  threads, settled facts or open questions needs the owner's approval.
- **MAP, mechanical corrections:** a fix to a link, path or citation that changes no claim. It is
  committed with the subject prefix `MAP-mechanical:`, and listed at the next distil so the owner
  sees it afterwards. The rule is part of Appendix A, so it exists only once the owner approves it.
- **Findings Inbox:** any agent appends; each line cites evidence and, where material, the
  revision or component it applies to.
- **Findings Settled:** the owner accepts lines at a distil. A Settled line contradicted by newer
  authoritative evidence is marked `superseded by <line or record>` or `flagged: <reason>`, never
  deleted. Settled lines describe; they never govern a later implementation revision.
- **Distil:** at existing task boundaries, or when retrieval visibly suffers. Twenty-five Inbox
  lines is a housekeeping signal, not a trigger for an owner event.
- **No duplicated write-ups:** a handoff's *For the index* holds short candidate lines that cite
  existing evidence.

## 6. Phase B: items and design

Phase B starts after T-0009 remediation is submitted. One owner work authorisation may cover all
of it. Each consequential amendment still needs the owner's approval at its own revision;
approvals may be batched (OD-0070, "Authority and sequencing").

Suggested order (the solution architect's, with H7's timing left to the owner):
1. H6;
2. H3's CI caps;
3. H11;
4. H7 (or earlier, by owner choice);
5. H5, reconsidered;
6. H8, after branch protection.

### 6.1 H6: scripted assignment and receipt

- `tools/hio_assign.py`:
  - emits the *Assigned reviews* row and the exchange message from the owner's values;
  - refuses a second assignment for the same target.
- `tools/hio_receive.py <exchange-report.json>`:
  - implements §6.2 steps 5.1 to 5.10 as amended by option B (5.6 navigation only; a refused index diff
    received only with `--without-index` and the owner's go-ahead), and reports "index reconciliation
    pending" for 5.12; it never changes a finding's state;
  - prints a summary that becomes the body of the receipt OD;
  - exits non-zero on every stop condition;
  - never pushes `main` without `--publish`.
  - **recovery boundary (proposed clarification, OD-0109; not adopted):** publishes only a receipt it
    constructed in the same invocation from a freshly fetched remote `main`. It recovers automatically
    only from a pushed tag with no import (resuming at 5.5 with the same `T`) and from a disposable,
    unmerged `receipt/<id>` branch (discarded and rebuilt). If local `main` is ahead of remote `main`,
    including by an unpublished import or local merge of this receipt, it stops, lists those commits and
    leaves them untouched; recovery is then the owner's, by §6.2 step 5.11 (for example: reset local
    `main` to remote `main` and rerun; the tag pins `T`). An import already on remote `main` is inspected
    only (blobs, index handling, disclosure, tag) and never causes a push of `main`. Before pushing
    `main` it re-fetches remote `main`, which must still equal the cut point, and the commits pushed must
    be exactly this invocation's import and merge. §6.2 itself is unchanged;
- **Required properties:** exact target and head; revision and branch identity; scope checks;
  inventory reconciled both ways; sha256; allowed paths; byte-identical import; correct index
  transitions; final recheck; stop on mismatch.
- **Codex's test list:**
  - a moved branch tip;
  - a wrong assignment head;
  - extra and missing files;
  - a disallowed path;
  - a hash mismatch;
  - a duplicate or conflicting receipt;
  - an incorrect index transition;
  - a stale target;
  - failure part-way through a receipt.

  A non-zero exit must leave a reconcilable state (the §6.2 recovery table).
- An exit code is not evidence until the tool and its tests are independently verified. The tool
  never replaces acceptance or approval.

### 6.2 H3: CI caps (tool change)

`tools/check_repo.py`:
- `STATUS.md`: at most 60 lines, and at most 200 characters per line outside fenced blocks;
- `MAP.md`: at most 110 lines.

These checks would pass on `STATUS.md` at `16ea0c6` (101 lines) only after a rewrite to 60 lines.
So the caps land together with the first natural rewrite, not as a separate exercise.

### 6.3 H11: Codex continuity, with applicability

**Read order** (amends §2.2 and the AGENTS Codex bullet):
1. the owner assignment;
2. the target and governing standards;
3. **only** `MAP.md` *Purpose*, *Pillars* and *Architecture*;
4. **the test plan is fixed**;
5. then the rest of `MAP.md`, the findings index, earlier `reviews/knowledge/` files and the
   author's handoff, all as claims to verify.

**Reviewer-owned knowledge:** each review adds `reviews/knowledge/<review-id>.md`. It contains:
- effective adversarial tests;
- recurring defect classes;
- places where the harness misled the reviewer;
- reusable verification methods;
- limitations and scope.

Each entry cites its review and the revision it applies to. An entry marked *remediated*,
*superseded* or *not applicable* says so. Earlier notes generate candidate probes, never verdicts.
The files are not a standards register.

**Receipt:** §6.2 steps 3 and 5.2 add `A reviews/knowledge/` to the allowed paths, so
byte-identical receipt carries them unchanged. The author never edits them. The owner distils from
them directly, keeping provenance.

### 6.4 H5: deferred

Reconsider only after H6 has operated for at least two review cycles and its effect on owner
minutes is known (H9). If revived, tier 2 covers only strictly reversible documentation-only
instructions, with a verbatim transcript, its sha256, scope and base revision. Tier 2 excludes:
- code, data and infrastructure;
- rights;
- standards, ADRs and specs;
- acceptance, waivers and scope;
- assignments and receipts;
- merges and promotion.

A commit trailer is never evidence of owner authority.

### 6.5 H8: deferred

**Order:** GitHub branch protection on `main` (an owner settings change) comes first, because it
is the server-enforced control. CI comes next. Hooks are a local guard against mistakes. Agent
instructions are the weakest of the four.

**The hooks:**
- load `MAP.md` at session start;
- deny edits to `.claude/**`, `tofu init|validate|plan|apply`, `az` write verbs, enabling
  scheduled workflows, and force-pushes.

**What they do not claim:** they make no claim to stop network egress or provisioning.

**Overrides:** kept by the owner outside the repository, naming an OD and an expiry date, never
created or interpreted by the constrained agent.

## 7. H7 in detail: a candidate standing publication delegation

### 7.1 The problem and the boundary

Owner instructions have twice sat on unmerged branches while `main` misstated what was authorised
(OD-0066 until OD-0067; OD-0062 to OD-0065 until OD-0069). H7 would let Claude **publish** records
of owner actions that have already occurred, without a per-merge owner instruction.

**Boundary** (the solution architect's distinction, adopted by OD-0070):

| | Publishing existing authority | Creating consequential authority |
|---|---|---|
| What | recording, on `main`, an owner action that has already occurred | the owner authorising, accepting, approving, waiving or changing scope |
| Who | Claude, under the delegation | the owner only |
| H7 covers it? | yes, within §7.3 | **never** |

### 7.2 Three properties, kept separate (OD-0070, "H7")

| Property | Question | How it is established | What CI can prove |
|---|---|---|---|
| **Source consistency** | Do the cited transcript, hash, quotation and revisions reconcile? | the structured evidence schema (Appendix B) | **yes**: the files exist, hashes match, quoted segments appear in order in the source, revisions resolve |
| **Owner authority** | Did the owner's instruction actually authorise the recorded action? | the owner's own words, read in context by a person | **no.** A consistent record can still misquote by omission, cite a message the owner did not send, or stretch scope. CI evidence is never described as proof of authority |
| **Publication permission** | Does the standing delegation permit this specific change? | the delegation OD's terms: paths, operations, kinds | **yes**: additions only, allowed paths, allowed decision kinds, delegation in force |

### 7.3 Candidate delegation terms

1. **Granted** by a tier-1 OD naming this design at an exact revision, after Codex's adversarial
   review (§9). Revocable by the owner at any time.
2. **Operations:** additions only (`A` in `git diff --name-status`), plus appended index rows. No
   modification or deletion.
3. **Paths:**
   - `docs/decisions/owner/OD-*.md`;
   - `docs/history/*.md` (transcripts);
   - `registers/tasks/T-*.md` (new cards);
   - index rows in `docs/decisions/owner/README.md` and `docs/history/README.md`.
4. **Decision kinds publishable under the delegation:** `authorise_work` only.
   - ODs recording `accept_work`, `approve`, `waive_finding`, `reject` or `supersede` are
     **never** published under the delegation. They reach `main` only by a merge the owner
     performs or explicitly instructs, as today.
   - This is what stops additions-only paths being used to introduce fabricated acceptance,
     approval or waiver records.
5. **New task cards** may be published only with `status: proposed`, or with `status: authorised`
   and an `authorised_by` OD that is already on `main` or in the same publication. A card's status
   can never be raised by modification (no modification is allowed).
6. **Scope is quoted, not paraphrased.** The OD's action scope must be a verbatim segment of the
   transcript (Appendix B, `action.scope_quote`). An OD whose recorded scope cannot be quoted is
   not publishable under the delegation.
7. **Prospective only.** The schema applies to ODs numbered after the delegation OD. Historical
   records stay intact unless a genuine defect is established. A read-only test on 2026-10-28
   found none; see Claude's response, §3.2 "Feasibility".
8. **Fail closed:** any check failure, or any ambiguity in scope, revision or kind, means no
   publication; the agent stops and asks (`AGENTS.md` rule 6).
9. **Visible afterwards:** every delegated publication carries `Publication: delegated (OD-NNNN)`
   in its merge commit. The receipt sweep at session start lists delegated publications since the
   owner last confirmed, so the owner sees each one.

### 7.4 Residual risks (stated, not engineered away)

| Risk | Why CI cannot catch it | Mitigation |
|---|---|---|
| **Improperly attributed authority**: a transcript Claude wrote that the owner never said | every commit uses the owner's local git identity (§6.1), so nothing in git separates owner from agent | the owner holds the original chat; delegated publications are listed for the owner (term 9); optional strengthening: the owner signs transcript commits with a key the agent cannot use (§6.1's evolution path) |
| **Misleading quotation**: verbatim segments chosen to change the meaning | the segments are verbatim, so they pass | Codex's negative cases (Appendix B); `quote` must include the full sentence containing the operative verb; the owner's after-the-fact listing |
| **Ambiguous action scope** | ambiguity is semantic | term 6 (quoted scope); term 8 (stop on ambiguity) |
| **Stale delegation**: published after revocation | detectable only if revocation is recorded | revocation is an OD; CI checks that the delegation OD has no later `supersede` record |

## 8. Sequencing against T-0009

| Order | Track | Work | Gate |
|---|---|---|---|
| 1 | T-0009 (critical path) | remediation of F-1 to F-7 on `impl/t0009-remediation-1` (cut from `ce0c3b5`) under OD-0067 | none: already authorised |
| 2 | T-0009 | submit a fixed head; the owner assigns Codex verification | remediation response written |
| 2′ | Harness | **Phase A**, applied while Codex verifies T-0009; on its own branch; never in a T-0009 branch | owner approval of Appendix A at an exact revision |
| 3 | Harness | §10 cold-start test of Phase A (owner-run) | Phase A on `main` |
| 4 | Harness | Phase B, in the §6 order | T-0009 remediation submitted; one work authorisation; approval per amendment |
| ongoing | Live readiness | T-0002 rights, storage, controls, finality, under existing authority | the separate live-operation decision |

**Why T-0009 is independent:**
- No T-0009 step needs a harness-0.9 change.
- No harness-0.9 step needs T-0009 to be *accepted*: Phase B waits only for remediation to be
  *submitted*, so they do not compete for the one implementation agent.
- If Codex's verification of T-0009 fails, T-0009 remediation resumes first, and Phase A pauses.

## 9. Verification requirements and success criteria

| Item | Verification before use | Success criterion after use |
|---|---|---|
| Phase A | owner approval of Appendix A at an exact revision; `tools/check_repo.py` passes; the applied text is byte-identical to Appendix A | the §10 test below |
| H3 CI caps | Codex review; passing and failing fixtures | `STATUS.md` stays within the caps without exceptions |
| H6 | Codex review with every case in §6.1 | a receipt takes one tool run plus the receipt OD; owner minutes per review cycle fall against the `REVIEW-2026-10-25-t0009-1` baseline |
| H7 | Codex adversarial review with Appendix B's negative cases, **before** owner approval | no authority record stranded off `main`; no delegated publication the owner later disowns |
| H11 | Codex review of the §2.2 and §6.2 amendments | a later review cites an earlier `reviews/knowledge/` probe it reused |
| H8 | Codex review; allow and deny test pairs | no legitimate authorised work blocked |

**The Phase A test: operating model §10, as approved, run by the owner, with fresh Claude and
Codex sessions at the Phase A merge commit.**
- **Claude:** the six §10 questions, plus four knowledge questions:
  - why S1b specs must not reuse S1a spec files;
  - what HIO is trying to learn in Year 1, and whether the capture clock has started;
  - whether any source right is verified;
  - one engineering trap from the findings index, chosen by the owner.
- **Codex:** the seven §10 questions with its **unchanged** bootstrap. This checks that Phase A
  did not alter the reviewer path.
- **Pass:** the §10 pass criteria, plus:
  - every knowledge question answered with a path and commit;
  - no wrong or misleading answer;
  - Claude reads at most 5,280 words before its first answer (the dry-run baseline).
- **Then, after two weeks or ten sessions, whichever is later:** the owner reviews
  `[rediscovery]` lines and owner minutes per review cycle. Phase A elements that show no benefit
  are simplified or removed (§11).

## 10. Authority analysis

| Proposal | What it lets Claude do | Why it cannot create consequential authority |
|---|---|---|
| Phase A mechanical MAP corrections | fix links, paths, citations | MAP is rank 5 navigation; no claim may change; each change is listed for the owner |
| Phase A findings Inbox | append claims | rank 6: claims, not facts; Settled requires the owner |
| Phase B work authorisation | implement H6, H3 caps, H11, H7 tooling, H8 on branches | each amendment still needs approval at its revision (`AGENTS.md` rule 3); Codex reviews each control |
| H7 delegation (candidate) | publish `authorise_work` ODs, transcripts and new cards to `main` | an OD only evidences the owner's statement (operating model §3). Acceptance, approval, waiver, rejection and supersession are excluded. Scope must be quoted. Cards cannot be modified. CI proves source consistency and publication permission, **not** owner authority, which stays with the owner's words and after-the-fact listing |
| H5 | — | deferred; not proposed |

**What remains with people:** whether a transcript faithfully records what the owner said. That
is the same as today: transcription is "an audit step, not a second permission gate" (`AGENTS.md`
rule 2).

## 11. Risks, residual risks and rollback

| Risk | Mitigation |
|---|---|
| MAP drifts into a second STATUS | no operational state; substantive changes owner-approved; `last_reviewed` checked at each distil and quarterly (§8 of the operating model) |
| The Inbox becomes a dump | distil at task boundaries; lines must cite evidence; every line leaves the Inbox at a distil |
| A Settled line outlives its truth | applicability and supersession markings; Settled lines never govern later revisions |
| Phase A alters the reviewer path by accident | the Codex bullet, §2.2 and §6.2 are outside the manifest; the §10 Codex run checks it |
| H7 residual risks | §7.4 |
| Phase B tooling hides a check | Codex review with deliberate failures, before use |

**Rollback.** Phase A is reverted by one commit restoring the harness-0.7.1 text, with a
changelog line. `MAP.md` and `knowledge/` carry no authority, so removing them changes no
approval state. Each Phase B item is independently revertible; H7 is revoked by an OD.

## 12. Outstanding owner decisions

Only genuine, unresolved choices. Direction is settled by OD-0070.

1. **Approve Phase A**: Appendix A of this package at an exact commit, which applies as
   `harness-0.9a`. The approval covers the `MAP.md` text and the mechanical-correction rule.
   Findings Inbox lines need no approval: they are claims.
2. **When to apply Phase A**: now. T-0009 was accepted (OD-0079), so Phase A competes with nothing (§8, §14).
3. **Phase B work authorisation**: one instruction. Its gate (T-0009 remediation submitted) is met; §14 adds candidate items.
4. **H7 timing**: the default is fourth in Phase B; earlier is possible, but never above T-0009 and
   never a prerequisite for Phase A. Its approval follows Codex's adversarial review in any case.
5. **Branch protection on `main`**: a GitHub settings change; the prerequisite for H8, and useful
   on its own.

Not decisions now: H5 (deferred by OD-0070), H10 and vector search (removed), the T-0009 priority
(settled).

## 13. Changes from revision 2

| Area | Revision 2 (`f5ce1b8`) | Revision 3 | Source |
|---|---|---|---|
| Framing | knowledge vs authority | three kinds of memory, with homes and needs (§2); success criterion (§2) | SA §3; OD-0070 pt 1 |
| Decision 0 | open owner decision | **satisfied by OD-0069**; failure 3 marked resolved | SA §6; OD-0070 pt 5 |
| Phase A authority | "needs no review; navigation files" | an exact harness amendment (`harness-0.9a`) needing **owner approval at a revision**; no Codex review | response §3.1; OD-0070 pt 3 |
| Phase A content | described in prose | **file manifest (§5.2) and exact text (Appendix A)** | OD-0070 deliverables |
| Codex bootstrap | a Codex line in the proposed bootstrap (rev 2 §5) | **removed from Phase A**; Codex path unchanged until H11 | response §3.3; OD-0070 pt 4 |
| MAP maintenance | owner approves all changes | substantive vs mechanical (§5.4) | SA §4 |
| Findings | Settled/Inbox; 25-line distil trigger | applicability, supersession, no-governance rule; 25 lines is a signal; distil at task boundaries | SA §5; OD-0070 pt 6 |
| H3 | text rules, plus CI caps in B | text rules in A; **no STATUS rewrite**; caps in B, landing with a natural rewrite | SA §6 |
| H5 | Phase B, decide after H6 | **deferred**; revival criteria; exclusion list widened | SA §8; OD-0070 pt 7 |
| H6 | tools and adoption condition | required properties and Codex's nine failure cases | SA §9; OD-0070 pt 8 |
| H7 | narrow path list, standing approval | **three properties kept separate**; `authorise_work` only; quoted scope; prospective structured schema; residual risks; adversarial Codex review before approval; timing is the owner's | SA §10; response §3.2; OD-0070 "H7" |
| H8 | branch protection first | plus the four assurance levels; no egress claims | SA §11 |
| H9 | two measures | plus the **§10 cold-start test** as Phase A's success test, with knowledge questions and a word-count bound | response §3.5; OD-0070 pt 9 |
| H11 | read order; Codex knowledge files | plus applicability and freshness; probes not verdicts; not a standards register | SA §13 |
| Sequencing | decision 0 first | **T-0009 first; Phase A in the verification gap**; Phase B after submission | response §3.6; OD-0070 pt 10 |
| Owner decisions | 0 to 7 | five, all genuine (§12) | OD-0070 deliverables |
| Seed files | MAP and findings, rev 2 | `MAP.md` and findings updated for OD-0069 (records now on `main`); findings carry applicability | OD-0069; SA §5 |


## 14. Revision 4: evidence from the 2026-10-28 session

Drafted on the owner's instruction "distill learnings and context from this session. this is the long run
context we need to develop. we need mechanisms to track it and allow agents to access it" (OD-0080). It
changes no Phase A rule. Appendix A still names the seed files "at this revision", so approving this
revision approves the refreshed seeds.

### 14.1 What changed in the seeds

- **`knowledge/findings.md`:** four seed lines marked `superseded by …` or updated, never deleted (F-1 fixed;
  D7 verified; code now on `main`; the US calendar implemented). Twenty-two Inbox lines added from the session
  that took T-0009 from submission to acceptance (OD-0074 to OD-0079) and gave the Codex reviewer network
  (OD-0077). The index now holds 42 lines, past the 25-line housekeeping signal, so **a first distil is due**.
- **`MAP.md`:** T-0009 accepted; the D7 calendars added as real data; the OpenTofu files are on `main`;
  a hiomux thread row added.

### 14.2 Gaps the session exposed that Phase A does not close

| # | Gap | Evidence | Proposed home |
|---|---|---|---|
| G1 | **Codex cannot reach the findings.** The reviewer re-derived conventions that the Inbox already holds, such as the exact `assignment` string and confirming the head with `ls-remote` | OD-0078; VERIFY-2026-10-28-t0009-1-1 deviations | H11 (Phase B), unchanged in design. Evidence that it pays for itself |
| G2 | **Operational knowledge lives outside the repository.** hiomux's protocol, tool, notes and run summaries are in `~/.hio-runs`; a fresh agent finds them only through Claude's auto-memory, which is not a record (`CLAUDE.md`) | OD-0072, OD-0073, OD-0077 | now: `MAP.md` thread row and `[hiomux]` findings (done); Phase B: bring hiomux and its protocol into the repository (OD-0073 already defers this to Phase B) |
| G3 | **No integrity check for out-of-repository tools.** hiomux changed after OD-0073 recorded its hash, and nothing noticed until a later edit | OD-0077 finding 1 | Phase B (H6 family): `hiomux` prints its own sha256 at `up`, and the orchestrator compares it with the latest OD before delegating. One line in PROTOCOL until then |
| G4 | **Distil has no owner moment.** The Inbox has grown with no scheduled distil | §14.1 | Phase A, unchanged; schedule the first distil when Phase A is applied |
| G5 | **Every receipt needed an owner question.** Class S rows, and reports through hiomux, fall outside OD-0061 | OD-0075; OD-0078 | not a harness change: a candidate standing owner decision extending OD-0061 to hiomux `result.json` reports with `report_ok: true`. Class S transitions stay with the owner |

### 14.3 What did not need a mechanism

- **Context within the session** was held by the conversation.
- **Context across sessions** was held by the handoff, STATUS and the OD chain.

The cost was not lost information but **finding it**. Thirteen ODs on one day (OD-0068 to OD-0080), each read in full, are the
reconstruction burden that Phase A (MAP and findings) and H4 (a handoff stream) target.

---

## Appendix A: exact Phase A text

Approving this appendix at a commit approves the text below. "Replace" means the quoted old text,
which must match the approved file exactly, is replaced by the new text. "Insert" names the anchor.
Files A1 and A2 are the seed files at this revision.

### A1. `MAP.md` (new)

The file `MAP.md` at this revision, unchanged.

### A2. `knowledge/findings.md` (new)

The file `knowledge/findings.md` at this revision, unchanged.

### A3. `AGENTS.md`

**A3.1 front matter.** Replace `version: harness-0.7.1` with `version: harness-0.9a`. The
`approved_by` line is set by the approving OD when the text is applied.

**A3.2 Claude's role bullet.** Replace:

```
- **Claude:** identify your instructed scope, the files you may change, the blocking findings,
  the acceptance tests and the handoff you owe. A proposed ADR is not approved because you
  wrote it.
```

with:

```
- **Claude** (and other non-reviewer agents): after `STATUS.md`, read [`MAP.md`](MAP.md) and the
  newest handoff in your stream (`handoffs/<stream>/`). Before deriving anything non-trivial,
  `grep` [`knowledge/findings.md`](knowledge/findings.md) and say what you found; its Inbox lines
  are claims, not facts. Then identify your instructed scope, the files you may change, the
  blocking findings, the acceptance tests and the handoff you owe. A proposed ADR is not approved
  because you wrote it.
```

**A3.3 Ending a session.** Replace:

```
- **Claude and other non-reviewer agents:** write a handoff from
  [`templates/handoff.md`](templates/handoff.md) into `handoffs/`, and update `STATUS.md` if
  the current state changed.
```

with:

```
- **Claude and other non-reviewer agents:** write a handoff from
  [`templates/handoff.md`](templates/handoff.md) into `handoffs/<stream>/`, add its *For the
  index* lines to the Inbox of `knowledge/findings.md`, and update `STATUS.md` if the current
  state changed.
```

Unchanged: the Codex bullet, the reviewer ending bullet, and everything else.

### A4. `docs/harness/operating-model.md`

**A4.1 front matter.** `version: harness-0.9a`, and a changelog line, first in the list:

```
  - "harness-0.9a (YYYY-MM-DD, APPROVED by OD-NNNN at <commit>; docs/decisions/harness-0.9-proposal.md revision 4, Appendix A): knowledge layer for non-reviewer agents. Adds MAP.md and knowledge/findings.md (navigation, precedence ranks 5 and 6), per-stream handoffs with Didn't work and For the index, current-state-only STATUS rules, §4.1 maintenance rules. Codex's bootstrap (§2.2) and the review protocol (§6.2) are unchanged. No tool, CI or hook changed"
```

**A4.2 §1 table.** Insert after the row beginning `| Mission, philosophy, trajectory |`:

```
| Project map: purpose, pillars, architecture, threads, settled facts, open questions (navigation; no operational state) | `MAP.md` | Markdown + front matter, ≤110 lines |
| Engineering knowledge: findings, dead ends, settled assessments (navigation) | `knowledge/findings.md` | Markdown, one line per entry |
```

Replace `| Current state | `STATUS.md` | Markdown, ≤150 lines |` with:

```
| Current state only: live work and its authority, blockers, open findings, next actions, branches. Rewritten, not appended; no lists of records inside table cells | `STATUS.md` | Markdown, ≤150 lines |
```

Replace `| Session history | `handoffs/YYYY-MM-DD-<slug>.md` | Markdown from template |` with:

```
| Session history | `handoffs/<stream>/YYYY-MM-DD-<slug>.md` (handoffs before harness-0.9a stay at `handoffs/YYYY-MM-DD-<slug>.md`) | Markdown from template |
```

**A4.3 §1.1 precedence.** Replace:

```
| 5 | `STATUS.md` | navigational snapshot; **no independent authority** |
| 6 | handoffs, chat, model memory, meeting notes, collaborator drafts | historical context only |
```

with:

```
| 5 | `STATUS.md`; `MAP.md`; the *Settled* section of `knowledge/findings.md` | navigational; **no independent authority**; the cited source wins |
| 6 | handoffs, the *Inbox* of `knowledge/findings.md`, chat, model memory, meeting notes, collaborator drafts | historical context or unverified claims only |
```

**A4.4 §2.1.** Insert before `Before changing anything, write down:`:

```
**Knowledge layer** (harness-0.9a; non-reviewer agents). After `STATUS.md`, read `MAP.md` and
the newest handoff in your stream (`handoffs/<stream>/`). Before deriving anything non-trivial,
`grep` `knowledge/findings.md` and say what you found. Inbox lines are claims, not facts. Codex's
bootstrap (§2.2) is unchanged.
```

**A4.5 §3 handoff bullet.** Replace `Non-reviewers write to `handoffs/`;` with
`Non-reviewers write to `handoffs/<stream>/` (one immutable file per session);`.

Then insert, after the list item `- **an explicit statement of what was not approved.**`:

```
  - **Didn't work:** approaches tried and abandoned, with the reason;
  - **For the index:** short candidate lines for the findings Inbox, each citing existing
    evidence. They are not repeated at length.
```

**A4.6 §4.** Append after `- **Failed and abandoned experiments are never deleted.** …`:

```
- **Boundary with engineering knowledge.** Experiment outcomes and negative research results
  live here, with the reasons and assumptions behind a rejection. `knowledge/findings.md` may
  point to an experiment, and never restates its conclusion.

### 4.1 Engineering knowledge and the project map (harness-0.9a)

- **`MAP.md`** is a navigational projection of other records. It holds no task status, findings,
  instructions, branch heads or blocker lists. A substantive change (any claim about purpose,
  pillars, architecture, threads, settled facts or open questions) needs the owner's approval. A
  mechanical correction (a link, path or citation that changes no claim) is committed with the
  subject prefix `MAP-mechanical:` and listed at the next distil.
- **`knowledge/findings.md`** holds one line per engineering finding, dead end or settled
  assessment. Each line cites evidence and, where material, the revision or component it applies
  to.
  - **Inbox:** any agent appends; claims, not facts (precedence rank 6). Tag a line
    `[rediscovery]` when re-deriving it cost real time.
  - **Settled:** accepted by the owner at a distil (rank 5). A Settled line contradicted by newer
    authoritative evidence is marked `superseded by …` or `flagged: …`, never deleted. Settled
    lines describe; they never govern a later implementation revision.
  - **Distil:** at existing task boundaries, or when retrieval visibly suffers. Claude proposes a
    place for each Inbox line; the owner decides; every line leaves the Inbox. Twenty-five Inbox
    lines is a housekeeping signal, not a trigger for an owner event.
- **Measures** (reviewed after meaningful use): `[rediscovery]` lines, and owner minutes per
  review cycle. Elements that show no benefit are simplified or removed.
```

**A4.7 §8 quarterly review.** Insert after `- check stale `last_reviewed` (>180 days for current documents);`:

```
  - check `MAP.md` against its sources, and *Settled* findings for staleness;
```

**A4.8 §12.** Replace `| ADRs, standards, specs, registers, STATUS, task cards, handoffs, review records |` with:

```
| ADRs, standards, specs, registers, STATUS, MAP, the findings index, task cards, handoffs, review records |
```

Unchanged: §2.2, §6.2, §10 and everything else.

### A5. `templates/handoff.md`

Insert after `work_card: T-NNNN` in the front matter:

```
stream: <t0009 | harness | research | rights | …>   # the handoff lives in handoffs/<stream>/
```

Insert after the section `## Known limitations and not verified` and its bullet:

```
## Didn't work
- … (approaches tried and abandoned, with the reason; or "nothing")

## For the index
- `[area] the finding. Source: <path:line, commit, test or record>.` (short candidate lines for
  the Inbox of `knowledge/findings.md`; or "nothing")
```

### A6. `.claude/skills/hio-session/SKILL.md`

Replace Start step 2, `2. Read `AGENTS.md` (the authority rules and the bootstrap by role), then `STATUS.md`.`, with:

```
2. Read `AGENTS.md` (the authority rules and the bootstrap by role), then `STATUS.md`.
   **Non-reviewers** then read `MAP.md` and the newest handoff in their stream
   (`handoffs/<stream>/`), and `grep` `knowledge/findings.md` before deriving anything
   non-trivial.
```

Replace `- **Non-reviewers:** put it in `handoffs/`; update `STATUS.md` if the state changed (150` with:

```
- **Non-reviewers:** put it in `handoffs/<stream>/`, add its *For the index* lines to the
  findings Inbox, and update `STATUS.md` if the state changed (150
```

### A7. `README.md`

Replace:

```
**Start here:** read [`AGENTS.md`](AGENTS.md), then [`STATUS.md`](STATUS.md).
```

with:

```
**Start here:** read [`AGENTS.md`](AGENTS.md), then [`STATUS.md`](STATUS.md). Non-reviewer
agents then read [`MAP.md`](MAP.md).
```

---

## Appendix B: H7 evidence schema and Codex negative cases

### B1. Prospective structured evidence (ODs numbered after the delegation OD)

```yaml
evidence:
  statements:                  # one entry per owner message relied on
    - source: docs/history/<file>.md
      sha256: <64 hex>         # of the source file as committed
      segments:                # verbatim; each must appear in the source, in this order
        - "<the full sentence containing the operative verb>"
  action:
    kind: authorise_work       # the only kind publishable under the delegation
    scope_quote: "<verbatim words defining the scope>"   # must be within a segment above
    base_revision: <40 hex>    # must resolve
    excludes: ["<verbatim exclusions, if the owner stated any>"]
publication:
  route: delegated             # delegated | owner_merged
  delegation: OD-NNNN          # the standing delegation relied on; absent for owner_merged
  attribution: agent_transcribed   # agent_transcribed | owner_committed | owner_signed
```

**What CI checks (source consistency and publication permission):**
- every `source` exists and its sha256 matches;
- every segment appears verbatim, in order;
- `scope_quote` lies within a segment;
- `base_revision` resolves;
- for `route: delegated`:
  - `kind` is `authorise_work`;
  - the diff is additions-only within the allowed paths;
  - the delegation OD exists and has no later superseding record;
  - new cards are `proposed`, or cite an `authorised_by` OD on `main` or in the same publication.

**What CI does not and cannot check (owner authority):**
- that the owner sent the message;
- that the segments are representative;
- that the scope is what the owner meant.

`attribution: owner_signed` records the strongest available evidence for the first point, when
the owner chooses to sign.

### B2. Negative cases Codex must test (adversarial, before owner approval)

| # | Case | Expected |
|---|---|---|
| 1 | Hash mismatch after an edit to the transcript | CI fails |
| 2 | A segment not present in the source | CI fails |
| 3 | **Misleading quotation**: verbatim segments that omit a qualifying clause ("authorise drafting … not implementation" quoted as "authorise … implementation") | CI fails: segments must be full sentences and in order. Where they are full sentences but still selective, Codex must show whether the design catches it; if not, the case becomes a stated residual risk |
| 4 | **Ambiguous action scope**: `scope_quote` matches two different readings in the source | CI cannot decide. The delegation requires a stop; Codex checks the documented procedure makes the agent stop |
| 5 | **Apparently valid but improperly attributed authority**: a well-formed transcript the owner never sent | CI passes. Codex confirms the after-the-fact listing (§7.3 term 9) surfaces it, and documents it as a residual risk |
| 6 | An `accept_work`, `approve` or `waive_finding` OD added under `route: delegated` | CI fails |
| 7 | A card added with `status: authorised` and no `authorised_by` on `main` | CI fails |
| 8 | Modification of an existing card or OD under the delegation | CI fails |
| 9 | `scope_quote` outside every segment | CI fails |
| 10 | Publication after a superseding record revokes the delegation | CI fails |
| 11 | A historical OD (before the delegation) | not checked; never fails |
| 12 | Two statements, one valid and one with a bad hash | CI fails |
