---
id: HIO-HARNESS-0.9-PROPOSAL
title: "Decision package: harness-0.9, a knowledge layer and lighter mechanics for a long-lived two-agent project, proposed, revision 2"
status: proposed   # no effect until the owner approves an exact revision (operating model §6)
owner: owner (decides); drafted by claude/implementation-agent
created_at: 2026-10-28
drafted_under: [OD-0068]
revision: 2   # rev 1 = 5f55cc79348304263378eb1d919856e45bda1f4f; rev 2 answers REPORT-2026-10-28-harness-0.9-fable-dryrun-1 (17 findings; §10)
amends: AGENTS.md (bootstrap; rule 2 for H5), STATUS.md (scope), templates/handoff.md, operating model §1, §2.2, §3, §6.2 steps 3 and 5, §9, §12; OD-0061 (H5 only); adds MAP.md and knowledge/
---

# Decision package: harness-0.9 (knowledge, continuity, lighter mechanics)

> **No effect until approved.** The approved harness is harness-0.7.1 with correction 1
> (`docs/harness/operating-model.md` on `main` at `eb19ef7`). Nothing here edits it. The seed
> files `MAP.md` and `knowledge/findings.md` on this branch are `proposed` drafts, offered so the
> owner can judge real content rather than a plan.
>
> **Review status.** Revision 1 had a same-vendor dry-run review
> ([`REPORT-2026-10-28-harness-0.9-fable-dryrun-1`](../../reviews/reports/REPORT-2026-10-28-harness-0.9-fable-dryrun-1.md),
> adopt with changes, 2 high, 9 medium, 6 low). Under operating model §10 that is advice, not an
> independent review. §9 item 7 asks for a Codex review of the control items.

## 1. The problem, measured

The owner's goal (OD-0068): a long-lived project in which Claude and Codex keep long-term
context and alignment, and knowledge builds up rather than being rediscovered.

The current harness was built to prove **who authorised what, at which revision**, and it
records that thoroughly. It records *authority*, not *knowledge*, and its mechanics are costly
relative to the work they govern. Measured on 2026-10-28, ten days after the first commit; the
base is stated per row:

| Measure | Value |
|---|---|
| Commits | `main` (`eb19ef7`): 208, of which 168 non-merge. All refs: 186 non-merge, of which 37 touch `src/` or `tests/` |
| Lines added, governance records only (`reviews/`, `handoffs/`, `docs/decisions/`, `docs/history/`, `docs/harness/`, `registers/tasks/`, `STATUS.md`, `AGENTS.md`) vs `src/` + `tests/` | `main`: 22,208 vs 9,230 (about 2.4 : 1) |
| Lines added, all of `docs/` + `reviews/` + `handoffs/` + `registers/` vs `src/` + `tests/` | all refs: 28,573 vs 11,695. `main`: 26,784 vs 9,230. `docs/` includes substantive work (standards ≈ 2,600, evidence ≈ 1,000, research ≈ 870 lines) |
| OD records / verbatim history files / dated handoffs / review records (`main`, excluding READMEs) | 63 / 69 / 47 / 22 |
| `operating-model.md` (`main`) | 8,440 words; §6.2 (review branch protocol) alone is 3,012 words |
| `STATUS.md` (`main`) | 93 lines, within the 150-line limit; its longest line is 2,729 characters (an OD history packed into a table cell) |
| Hypotheses / experiments registered (`main`) | 4 / 0 |
| Lessons and dead ends | scattered through ODs and handoffs (for example OD-0058, "nothing local would have caught it"); there is no class or index for them |

**Baseline for H9** (from the dry run, §2): the current bootstrap path (AGENTS, STATUS, task
card, review index) read 5,280 words and gave one wrong answer (the next action) and one
misleading answer (S1b authorisation). The proposed path read 4,384 words, gave neither, and
answered two knowledge questions the current path could not reach.

**Five failures:**

1. **No big picture in the read path.** A session reads `AGENTS.md` → `STATUS.md` → task card →
   OD. None says what HIO is trying to learn or what the active threads serve; the charter and
   roadmap are not in the bootstrap.
2. **Knowledge is lost or buried.** The handover of 2026-10-25 was 190 lines, almost all
   procedure and SHAs. Its few durable facts lived only in a file in `~/Downloads`, the pattern
   operating model §0 already names as a defect.
3. **Current state disagrees with itself on `main`.**
   - `STATUS.md` does not mention T-0009 and says "S1b is not authorised"; OD-0067 on `main`
     authorises T-0009 remediation; OD-0062 to OD-0065 and the T-0009 card are only on the
     unmerged branch `impl/t0009-shared-receipt-and-storage`.
   - The HIO-ADR-0012 findings read "3 findings open" (STATUS l.39), "technically verified
     closed" (STATUS l.47, OD-0054) and `remediation_claimed` (`reviews/README.md`).
4. **Deterministic mechanics are prose.** Receiving two Markdown files from Codex
   (`REVIEW-2026-10-25-t0009-1`) took a whole session: OD-0066 and its transcript, a tag, a
   receipt branch, a byte-identical import, index rows, OD-0067 (76 lines) and its transcript,
   CI and exchange checks, and five commits and merges. Every check is mechanical, and each
   agent rereads 3,012 words to perform it by hand.
5. **Codex starts cold every time.** Independence is protected, correctly, but Codex keeps no
   knowledge between reviews: not recurring defect classes, not the probes that found
   `F-REVIEW-2026-10-25-t0009-1` and `-2`.

Operating model §12 sets the test: "the harness must save more owner time than it costs".

## 2. Sources of ideas

- An owner-supplied description of a personal harness used in another environment (2026-10-27;
  not committed, see OD-0068's history file). Lessons taken:
  - keep big picture, findings, rulings and operational state in **separate files with separate
    change rules**;
  - make capture cheap and **approval manual** (an inbox, distilled by the owner);
  - use per-stream handoffs instead of standalone handovers;
  - roll sessions over at task boundaries, not at compaction;
  - put guards in hooks that fail closed, as defence in depth;
  - measure memory by real rediscovery incidents; drop infrastructure that does not beat the
    simple baseline.
- HIO's own operating model §0, §8 and §12, which already state most of the intent.
- The dry-run review (§10).

**Not proposed from that source:** tmux worker fleets, run lanes, usage telemetry. They solve
parallel throughput, which is not HIO's constraint; §9 rules out multi-agent orchestration
without an ADR showing measured benefit.

## 3. What does not change

- The authority model (§1.1): the four owner actions, "availability is not authority",
  stop-and-flag on conflict, self-declaration. Precedence ranks 1 to 6 keep their sources; H1
  and H2 add new navigation files at ranks 5 and 6 only.
- Separation of duties and review independence (§2.2, §5). Codex never edits work under
  review, never infers a target, and reads author-written material only after fixing its test
  plan (H11 keeps this).
- Immutable review evidence received by byte-identical import with a provenance tag (§6.2), and
  the receipt OD required by OD-0061.
- Data rights, secrets, the `macsmsf` boundary, the return accounting standard.

**What does change in authority terms** (each listed in §9): H5 amends `AGENTS.md` rule 2's
*record format* for a narrow class; H7 is a new standing merge approval for a narrow class; H11
amends the reviewer read order and allowed writes.

## 4. Proposed changes

Each item can be approved, deferred or rejected alone.
- **Phase A** is documentation only: H1, H2, H4, H9.
- **Phase B** changes controls, tools, CI or the reviewer protocol, and needs a Codex review
  before use: H3's CI caps, H5, H6, H7, H8, H11.

### H1. `MAP.md`: one page, read second (Phase A)

At the repository root, read immediately after `AGENTS.md`. It holds what does **not** change
week to week: purpose and pillars, the Year 1 trajectory, the architecture as current, target
and undecided, each thread's purpose with a pointer to its state, settled facts, and the open
strategic questions. **It holds no operational state**; state lives only in `STATUS.md`. A draft
is on this branch.

- **Change rule:** the owner approves changes; an agent proposes them.
- **Precedence:** rank 5, alongside `STATUS.md`: navigation with no independent authority. The
  cited source wins.
- **Sources:** every line cites a source on `main`, or says "(branch …, not on `main`)".
- **Size:** about 100 lines; a CI check follows in Phase B with H3.

### H2. `knowledge/findings.md`: the findings index (Phase A)

One line per finding, dead end or settled assessment, each citing **repository** evidence
(path and line, commit, test, record) or a reproducible fact. Sections:
- **Settled:** lines the owner accepted at a distil. Rank 5; the cited source wins.
- **Inbox:** any agent appends at any time. Rank 6: claims, not facts. A line that cost real
  time to rediscover is tagged `[rediscovery]` (H9).

**Rule for every agent:** before deriving something non-trivial, `grep` the index and say what
was found.

**Boundary with research memory:** experiment outcomes and negative results stay in
`registers/experiments.yaml` (§4). The findings index holds engineering, data, rights and
process knowledge, and at most a one-line pointer to an experiment.

**Distil:** on owner request, or when the Inbox passes 25 lines. Claude proposes a placement for
each line (Settled, MAP, rejected), and the owner approves line by line. An estimated 10 to 15
owner minutes per distil. Lines from Codex's own notes (H11) are distilled by the owner directly,
not placed by Claude.

A seed of 20 Inbox lines is on this branch.

### H3. `STATUS.md` holds operational state only (Phase A text; Phase B CI)

Rewritten, not appended, at every state change. It covers:
- live work, with its branch;
- what waits on the owner;
- the next actions;
- open findings by review.

The OD history moves out: the OD index in `docs/decisions/owner/README.md` is already that log.
No lists of ODs inside table cells.

CI caps (Phase B, a tested change to `tools/check_repo.py`): 60 lines and 200 characters per
line for `STATUS.md`; 110 lines for `MAP.md`.

### H4. Per-session handoffs grouped by stream (Phase A)

`handoffs/<stream>/YYYY-MM-DD-<slug>.md`: one immutable file per session, as now, grouped by
stream so the newest file in a stream is the resume point. Streams start as `t0009`, `harness`,
`research` and `rights`. The template keeps every current field (including *not approved* and the
completion block) and adds:
- **Didn't work**;
- **For the index** (lines to copy into the findings Inbox).

The completion block's prompt is the successor prompt. **Rollover:** at a task boundary, commit,
write the handoff, add *For the index* lines, then `/clear` or start a new session; don't rely on
compaction.

Standalone handovers are retired except for work stopped part-way, and never live outside the
repository. The existing 47 handoffs stay where they are.

### H5. Lighter owner records for documentation-only instructions (Phase B; amends `AGENTS.md` rule 2)

| Tier | Owner actions | Record |
|---|---|---|
| **1** (as today) | approve, accept, waive, reject, supersede; any authorisation touching code, infrastructure, data, rights, merges or a slice's scope; **review assignments; receipts (OD-0061)**; Class S transitions | an OD record plus a verbatim `docs/history/` transcript with its sha256 |
| **2** | documentation-only authorisations (drafting, status corrections, navigation files) | a verbatim `docs/history/` transcript with its sha256, and **one row** in the OD index citing it. No separate OD file |

**What changes:** for tier 2, the OD file, which mostly restates the transcript. The verbatim
transcript and its hash stay, so owner confirmation keeps the evidence §6.1 requires. An
`Owner-Instruction:` trailer may be added, but it is metadata and never evidence. The owner may
raise any instruction to tier 1.

**Rule 2 amendment text:** "Record it promptly: an OD record for tier 1, or a verbatim transcript
and an OD-index row for tier 2 (operating model §1.1)."

**Sequencing:** decide H5 after H6 is in use. Mechanised receipt may remove most of the record
cost that motivates it.

### H6. Mechanised assignment and receipt (Phase B)

- `tools/hio_assign.py`: emit the *Assigned reviews* row and the exchange message from the
  owner's values, and refuse a second assignment for the same target.
- `tools/hio_receive.py <exchange-report.json>`:
  - implements §6.2 steps 5.1 to 5.10: tip, inventory both ways, sha256, scope and assignment
    checks, tag, import, Class N and Class S row checks, blob verification, final recheck;
  - prints a receipt summary that becomes the body of the receipt OD;
  - exits non-zero on every stop condition;
  - never pushes `main` without `--publish`.
- §6.2 step 5 shrinks to:
  - its inputs (5.0);
  - "run the tool; a non-zero exit is a stop";
  - the recovery table;
  - the accountability paragraph.
- **Adoption condition:** a Codex review of the tools, including deliberate failing cases.

### H7. Standing approval: authority records reach `main` first (Phase B; a new owner approval)

A narrow, explicit **standing merge approval** (tier 1, its own OD). It lets Claude merge to
`main`, without a per-merge owner instruction, commits that touch **only**:
- `docs/decisions/owner/OD-*.md` and the OD index;
- `docs/history/` transcripts and their index;
- `registers/tasks/T-*.md`.

It never covers code, `reviews/`, `STATUS.md` content beyond the item's row, ADRs, standards
or specs. Each task card must state `status` and `authorised_by` in its front matter, so a
`proposed` card on `main` is plainly not authorised. `STATUS.md` names the code branch of each
authorised item.

Then `main` alone answers "what is authorised now?". The owner can revoke the approval at any
time.

### H8. Hooks as defence in depth (Phase B)

- **Prerequisite:** GitHub branch protection on `main` (an owner action in GitHub settings). It
  is the real control against an unauthorised push; hooks are not.
- **SessionStart:** print `MAP.md`, the head of `STATUS.md` and the Inbox count.
- **PreToolUse**, failing closed:
  - deny edits to `.claude/**`;
  - deny `tofu init|validate|plan|apply`;
  - deny `az` write verbs;
  - deny enabling scheduled workflows;
  - deny force-pushes.
- **Overrides:** kept by the owner outside the repository (user-level settings), each naming an
  OD and an expiry date.
- **Limits stated plainly:** a local hook cannot tell an agent's push from an owner's, and a
  pattern match on network fetches is bypassed by any client library. So the hooks catch
  mistakes; they do not stop an adversary.

Codex has no equivalent hook surface. It reads the rules from `AGENTS.md`.

### H9. Measuring it (Phase A)

Two measures, reviewed after two weeks or ten sessions, whichever is later:
- **rediscovery incidents:** Inbox lines tagged `[rediscovery]`. The owner and Codex log
  incidents too, since an agent rarely notices its own;
- **owner minutes per review cycle**, estimated by the owner. Baseline: the
  `REVIEW-2026-10-25-t0009-1` assignment and receipt.

The bootstrap baseline is in §1.

### H11. Codex continuity without author framing (Phase B; amends §2.2 and §6.2 step 3)

- **Read order:** before fixing its test plan, Codex reads only MAP's *purpose*, *pillars* and
  *architecture* sections. MAP's threads, the findings index and the author's handoff come after.
  Codex treats any line within its review scope as a claim to verify.
- **Codex's own knowledge file:** each review adds `reviews/knowledge/<review-id>.md`, holding
  recurring defect classes, probes that worked, and places where the harness misled it.
  - It is a new file, so byte-identical receipt carries it unchanged.
  - §6.2 step 3 and step 5.2 add `A reviews/knowledge/` to the allowed paths.
  - The author never edits these files. The owner distils from them directly.
- Codex's next session reads the previous `reviews/knowledge/` files after its test plan.

(H10 of revision 1, session rollover, is folded into H4.)

## 5. Proposed `AGENTS.md` bootstrap (when H1, H2 and H4 are approved)

> **Common path:**
> 1. This file.
> 2. `MAP.md`: what HIO is for, the architecture, the threads and where their state lives.
> 3. `STATUS.md`: live work and what waits on the owner.
> 4. The newest handoff in your stream (`handoffs/<stream>/`).
> 5. Your task card and its owner instruction; the approved ADRs and standards it names.
> 6. Before deriving anything non-trivial: `grep` `knowledge/findings.md` and say what you
>    found.
>
> **End:** write your stream's handoff, add *For the index* lines to the findings Inbox, and
> rewrite `STATUS.md` if the state changed.
>
> **Codex:** steps 1 and 2 (purpose, pillars and architecture only), then the reviewer steps
> below. Read the rest after your test plan.

(Links are written relative to the root when applied.)

## 6. Alternatives considered

| Alternative | Why not |
|---|---|
| Keep harness-0.7.1 as is | §1 measures its cost; the current read path gave a wrong next action in the dry run |
| Revive the stopped harness-0.8 (`b86f497`, OD-0024) | It addresses delivery mechanics, not knowledge or continuity |
| Rely on Claude auto-memory | `CLAUDE.md`: memory is a cache, never a record; Codex cannot read it |
| Full-text recall over transcripts now | Deferred until H9 shows misses a repository `grep` would not catch (§7) |
| Vector search | Measured elsewhere as no better than keyword search |
| Multi-agent orchestration | §9: only by an ADR with measured benefit |

## 7. Deferred, with adoption criteria (added to §9)

| Behaviour | Adopt when |
|---|---|
| Keyword recall (SQLite FTS5) over transcripts and the repository | ≥ 3 `[rediscovery]` incidents where the knowledge existed only in a transcript |
| Automatic harvest of session transcripts into the Inbox | distils run regularly, and *For the index* lines visibly miss things |
| Generated review index from record front matter | ≥ 2 index-versus-record disagreements in a month |

## 8. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Tier 2 loses audit fidelity | Verbatim transcript and sha256 kept; tier 1 covers every consequential action, assignments and receipts |
| `MAP.md` drifts into a second STATUS | No operational state in MAP; owner-approved changes; CI line cap; `last_reviewed` checked at each distil |
| The Inbox becomes a dump | Distil at 25 lines; every line leaves the Inbox; Settled lines must cite repository evidence |
| The author frames the reviewer | H11 read order; Codex-owned knowledge files the author never edits |
| The standing merge approval is stretched | Narrow path list; no code, reviews or policy; revocable; CI could enforce the path list later |
| Hooks are mistaken for a control | Branch protection first; hooks labelled defence in depth |
| Mechanised receipt hides a check | Same stop conditions; reviewed by Codex with deliberate failing cases |

**Rollback:** each Phase A item is a documentation change, reverted by commit. `MAP.md` and
`knowledge/` carry no authority, so removing them changes no approval state.

## 9. Owner decisions requested

0. **Now, independent of harness-0.9** (recommended first): one bounded instruction to bring
   OD-0062 to OD-0065 and the T-0009 card to `main`, and rewrite `STATUS.md`. This fixes today's
   contradiction (§1 failure 3) without waiting for this package. It must not delay T-0009
   remediation: the PIT capture clock has not started, and that is the project's real
   constraint.
1. **Phase A:** H1, H2, H4 and H9, and the `STATUS.md` text rules of H3. Recommended: approve.
   About one documentation session, plus 10 to 15 owner minutes per distil.
2. **The seed files:** approve, amend or reject `MAP.md`, and each Inbox line of
   `knowledge/findings.md`, at the first distil.
3. **H7:** a standing merge approval for authority records, with the path list as drawn.
4. **H6 and H3's CI caps:** authorise them as one task card, after T-0009 remediation is
   submitted.
5. **H5:** decide after H6 is in use. It amends `AGENTS.md` rule 2 and narrows nothing in OD-0061,
   since receipts stay tier 1.
6. **H8:** turn on branch protection on `main`; then authorise the hooks.
7. **Codex review** of H5, H6, H7, H8 and H11 before each is applied. Phase A needs none: it
   creates navigation files with no authority.

## 10. Changes from revision 1 (answering the dry run)

| Finding | Change |
|---|---|
| DRY-1 (high) | Receipts and assignments are tier 1; tier 2 keeps the verbatim transcript and its sha256; the trailer is optional metadata; the rule 2 amendment is stated, removing the contradiction |
| DRY-2 (high) | H7 is an explicit, narrow standing approval with a path list (§9 item 3) |
| DRY-3 | H8: branch protection first, `.claude/**` denied, overrides outside the repository with OD and expiry, labelled defence in depth |
| DRY-4 | H11: purpose and architecture only before the test plan; Codex-owned `reviews/knowledge/<id>.md`, received byte-identically, distilled by the owner |
| DRY-5 | CI caps, H5, H7 and H11 moved to Phase B |
| DRY-6, DRY-7 | MAP holds no operational state; off-main citations marked; sources added; "plan agreed" removed |
| DRY-8 | MAP and Settled lines at rank 5, Inbox at rank 6 |
| DRY-9 | A 200-character line cap, and no OD lists in cells |
| DRY-10, DRY-14 | Findings re-sourced to repository evidence or reproducible facts; the `spec_ref` line reworded; two lines with no repository source dropped |
| DRY-11 | §9 completed: decision 0, H7, the CI caps, H11, distil cost, and the experiments boundary (H2) |
| DRY-12, DRY-13 | §1 counts corrected with bases; overstated claims removed |
| DRY-15 | Per-session immutable files under `handoffs/<stream>/` |
| DRY-16 | `[rediscovery]` tag replaces a separate log; owner and Codex log too; baseline in §1 |
| DRY-17 | Noted: OD-0068's verbatim transcript contains a local path with the account name, which is also the public GitHub owner name. No change, since the transcript is verbatim |
| Recommendation 13 | H10 folded into H4; *Surprised by* dropped; H9 reduced to two measures |
