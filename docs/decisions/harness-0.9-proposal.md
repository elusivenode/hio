---
id: HIO-HARNESS-0.9-PROPOSAL
title: "Decision package: harness-0.9, a knowledge layer and lighter mechanics for a long-lived two-agent project, proposed, revision 1"
status: proposed   # no effect until the owner approves an exact revision (operating model §6)
owner: owner (decides); drafted by claude/implementation-agent
created_at: 2026-10-28
drafted_under: [OD-0068]
revision: 1
amends: AGENTS.md (bootstrap), STATUS.md (scope), templates/handoff.md, operating model §1, §2, §3, §6.2 step 5, §12; adds MAP.md and knowledge/
---

# Decision package: harness-0.9 (knowledge, continuity, lighter mechanics)

> **No effect until approved.** The approved harness is harness-0.7.1 with correction 1
> (`docs/harness/operating-model.md` on `main` at `eb19ef7`). Nothing here edits it. The seed
> files `MAP.md` and `knowledge/findings.md` on this branch are `proposed` drafts, offered so the
> owner can judge real content rather than a plan.

## 1. The problem, measured

The owner's goal (OD-0068): a long-lived project in which Claude and Codex keep long-term
context and alignment, and knowledge builds up rather than being rediscovered.

The current harness was built for a different goal and does that well: proving **who authorised
what, at which revision**. Nobody has caught it in a false approval claim. But it records
*authority*, not *knowledge*, and its mechanics cost more than the work they govern. Measured on
`main` at `eb19ef7` and across all refs on 2026-10-28, ten days after the first commit:

| Measure | Value |
|---|---|
| Commits | 208 on `main`; 186 non-merge across all refs, of which 37 touch `src/` or `tests/` |
| Lines added: `docs/`, `reviews/`, `handoffs/`, `registers/` | ≈ 28,500 |
| Lines added: `src/`, `tests/` | ≈ 11,700 |
| OD records / verbatim history files / dated handoffs / review records | 64 / 70 / 47 / 23 |
| `operating-model.md` | 8,440 words; §6.2 (review branch protocol) alone is 3,012 words |
| `STATUS.md` | 93 lines, within the 150-line limit, but its longest line is 2,729 characters (an OD history packed into a table cell) |
| Hypotheses / experiments registered | 4 / 0 |
| Recorded lessons, dead ends or "didn't work" lines | none as a class; a grep of `handoffs/`, `reviews/records/` and the OD records finds none |

**Five failures this produces:**

1. **No big picture in the read path.** A session reads `AGENTS.md` → `STATUS.md` → task card →
   OD. These cover rules and current state; none says what HIO is trying to learn or what the
   active threads serve. The charter and roadmap exist but are not in the bootstrap.
2. **Knowledge is lost or buried.** The handover of 2026-10-25 was 190 lines, almost all
   procedure and SHAs. Its five durable facts (for example: spec files must be named
   `<factor_id>.yaml`; changing an S1a spec changes S1a release ids) lived only in a file in
   `~/Downloads`. Operating model §0 already names that pattern as a defect to fix.
3. **Current state needs three documents to work out, and they disagree.**
   - `STATUS.md` on `main` does not mention T-0009 and says "S1b is not authorised". The
     authority for T-0009 (OD-0062 to OD-0065, the T-0009 card) exists only on the unmerged
     branch `impl/t0009-shared-receipt-and-storage`.
   - `F-REVIEW-2026-10-25-adr0012-1` and `-3` read `remediation_claimed` in `reviews/README.md`,
     but "technically verified closed" in OD-0054 and `STATUS.md`. Reconciling them takes
     OD-0053 and OD-0054.
4. **Deterministic mechanics are prose.** Receiving two Markdown files from Codex
   (`REVIEW-2026-10-25-t0009-1`) took a whole session: the assignment OD (OD-0066) and its
   transcript; a tag; a receipt branch; a byte-identical import; index rows; a receipt OD
   (OD-0067, 76 lines) and its transcript; CI and exchange checks; five commits and merges. Every
   check is mechanical, yet each agent rereads 3,000 words to perform it by hand.
5. **Codex starts cold every time.** Independence is protected, correctly, but Codex also keeps
   no knowledge between reviews: not the recurring defect classes, not the probe techniques that
   found F-1 and F-2, nothing.

Operating model §12 already sets the test this harness fails: "the harness must save more owner
time than it costs".

## 2. Sources of ideas

- The owner-supplied description of a personal multi-agent harness used in another environment
  (2026-10-27; not committed, see the history file of OD-0068). Its main lessons:
  - keep big picture, findings, rulings and operational state in **separate files with separate
    change rules**, because mixed files drift;
  - capture is automatic or cheap, **approval is manual** (an inbox, distilled by the owner);
  - rolling per-stream handoffs replace standalone handovers;
  - roll sessions over at task boundaries, not at compaction;
  - put enforcement in hooks, failing closed, not in prose;
  - measure memory by real rediscovery incidents; drop infrastructure that does not beat the
    simple baseline (a vector store there tied keyword search and was removed).
- HIO's own operating model §0, §8 and §12, which already state most of the intent.

Ideas from that source that are **not** proposed: tmux worker fleets, run lanes and usage
telemetry. They solve parallel throughput, which is not HIO's constraint, and §9 rules out
multi-agent orchestration without an ADR showing measured benefit.

## 3. What does not change

- The authority model (§1.1): the four owner actions, "availability is not authority",
  stop-and-flag on conflict, self-declaration, and the precedence table's ranks 1, 2 and 5.
- Separation of duties and review independence (§2.2, §5): Codex never edits work under review,
  never infers a target, and reads the author's handoff only after fixing its test plan.
- Immutable review evidence received by byte-identical import with a provenance tag (§6.2). H6
  mechanises the receipt; it does not weaken it.
- Data rights, secrets, the `macsmsf` boundary, the return accounting standard.

## 4. Proposed changes

Each item is independent, and can be approved, deferred or rejected alone. **Phase A** is
documentation only. **Phase B** is code and is reviewed by Codex before use.

### H1. `MAP.md`: one page, read second (Phase A)

A single page at the repository root, read immediately after `AGENTS.md` by **every** agent
including Codex. Contents: what HIO is for in this phase, the research pillars, the architecture
as current, target and proposed, the active threads (what each serves, its state, where its
detail lives), settled facts, and the open strategic questions. A draft is on this branch.

- **Change rule:** the owner approves changes. An agent may propose an edit in a handoff or a
  commit marked `proposed`.
- **Precedence:** navigation, with the standing of rank 3 (charter, roadmap). The cited source
  wins any disagreement.
- **Budget:** at most 120 lines (CI check, like `STATUS.md`).

### H2. `knowledge/findings.md`: the findings index (Phase A)

One line per finding, dead end or settled assessment, each citing its source (path, commit,
test or record). Two sections:
- **Settled:** lines the owner has accepted at a distil. Navigation only; the cited source wins.
- **Inbox:** any agent appends here at any time. Inbox lines are claims, not facts.

The receiver copies the *For the index* lines from a Codex review handoff into the inbox at
receipt, so the reviewer's knowledge is kept without widening the reviewer's write scope.

**Rule for every agent:** before deriving something non-trivial, `grep` the findings index and
say what was found. A miss that cost real time is a rediscovery incident (H9).

**Distil:** on owner request, or when the inbox passes 25 lines. Claude proposes the placement
of each inbox line (settled, MAP, rejected); the owner approves; every line leaves the inbox
either way.

A seed with 21 lines is on this branch, drawn from the 2026-10-25 handovers, the OD records and
the review records.

### H3. `STATUS.md` holds operational state only (Phase A)

Rewritten (not appended) at every state change, at most 60 lines: live work and its branch, what
waits on the owner, the next actions, and open findings by review. The OD history moves out; the
OD index in `docs/decisions/owner/README.md` is already that log. The CI line limit falls from
150 to 60.

### H4. Rolling handoffs per stream (Phase A)

`handoffs/<stream>.md`, newest entry first, at most five entries (older entries stay in git
history). Streams start as `t0009`, `harness`, `research` and `rights`. The entry template
keeps every field of `templates/handoff.md` (including *not approved* and the completion block)
and adds four short headings: **Stopped at**, **Didn't work**, **For the index** and
**Surprised by**. The *Resume* prompt in the completion block is the successor prompt for the
next session.

Standalone handover documents are retired except for work stopped part-way, and never live
outside the repository. The existing 47 dated handoffs stay as history; they are not migrated.

### H5. Tiered owner records (Phase A; needs an amendment to `AGENTS.md` rule 2)

| Tier | Owner actions | Record |
|---|---|---|
| **1** | approve, accept, waive, reject, supersede; any authorisation that touches code, infrastructure, data, rights or a slice's scope; any Class S index transition | an OD record plus a verbatim `docs/history/` transcript, as today |
| **2** | documentation-only authorisations; routine receipt under OD-0061; drafting; status corrections | **one row** in the OD index (date, decision, the quote, scope) and an `Owner-Instruction:` trailer quoting the owner's words on the commit that acts on it. No separate OD file or transcript |

The owner may raise any instruction to tier 1 by saying so. Rule 2 ("transcription is an audit
step, not a second gate") is unchanged; only the size of the audit record changes. Git keeps the
quote immutable in the commit, which is the evidence the history file gives today.

### H6. Mechanised assignment and receipt (Phase B)

- `tools/hio_assign.py`: from the owner's values, emit the *Assigned reviews* row and the
  exchange message, and refuse a second assignment for the same target.
- `tools/hio_receive.py <exchange-report.json>`: implement §6.2 steps 5.1 to 5.10 (tip, inventory
  both ways, sha256, scope and assignment checks, tag, import, Class N/S row checks, blob
  verification, final recheck). Print a receipt summary; exit non-zero on every stop condition;
  never push `main` without `--publish`.
- §6.2 step 5 then shrinks to its inputs (5.0), "run the tool; a non-zero exit is a stop", the
  recovery table and the accountability paragraph. A Codex review of the tools is the adoption
  condition, as the CI reviewer gate was under harness-0.7.

### H7. Authority for in-flight work lives on `main` (Phase A)

OD records, verbatim transcripts and task cards for authorised work merge to `main` through the
existing documentation-only lane as soon as they are written, ahead of the code they authorise.
Then `main` alone answers "what is authorised now?", and `STATUS.md` cannot contradict the
records it summarises.

### H8. Hooks: load the map, enforce the hard limits (Phase B)

Project-level Claude Code hooks, committed in `.claude/settings.json` with tests:
- **SessionStart** (start, resume, clear, compaction): print `MAP.md`, the head of `STATUS.md`
  and the inbox count.
- **PreToolUse**, failing closed: deny the standing hard limits that prose now carries:
  `tofu init|validate|plan|apply`; `az` write verbs; network fetches from source publishers;
  enabling scheduled workflows; force-pushes; any push to `main` outside the receipt tool. An
  owner-set environment variable lifts a specific limit for one session when an OD authorises it.

Codex has no equivalent hook surface; it keeps reading these rules from `AGENTS.md`.

### H9. Measuring it (Phase A)

`knowledge/rediscovery.md`: one line per real incident in which an agent re-derived or
re-investigated something already known, with the cost and where it should have been found.
Review after two weeks or ten sessions, whichever is later, against:
- rediscovery incidents (falling);
- owner minutes per review cycle (falling);
- bootstrap tokens to first useful action (at most 25k, as §12 already sets);
- records written per code commit (falling).

### H10. Session rollover at task boundaries (Phase A)

Commit the work, write the rolling handoff entry, distil if anything durable came out, then
`/clear` or start a new session, rather than relying on compaction. The new session starts from
`AGENTS.md` → `MAP.md` → `STATUS.md` → the top entry of its stream's handoff.

### H11. Codex continuity (Phase A)

Codex reads `MAP.md` and the *Settled* section of the findings index as background. They are
owner-approved summaries, not the author's narrative, but Codex treats any line inside its review
scope as a claim to verify, never as evidence. Codex's review handoff gains a **For the index**
section (recurring defect classes, probes that worked, places where the harness misled it),
which reaches the inbox at receipt (H2).

## 5. Proposed `AGENTS.md` bootstrap (replaces "Bootstrap" when H1, H3, H4 and H10 are approved; links are written relative to the root when applied)

> **Common path:**
> 1. This file.
> 2. `MAP.md`: what HIO is for, the active threads, settled facts, open questions.
> 3. `STATUS.md`: live work and what waits on the owner.
> 4. The top entry of your stream's handoff in `handoffs/`.
> 5. Your task card and its owner instruction; the approved ADRs and standards it names.
> 6. Before deriving anything non-trivial: `grep` `knowledge/findings.md`
>    and say what you found.
>
> **End:** write your stream's handoff entry, add *For the index* lines to the findings inbox,
> and rewrite `STATUS.md` if the state changed.

## 6. Alternatives considered

| Alternative | Why not |
|---|---|
| Keep harness-0.7.1 as is | The measurements in §1 are the cost of keeping it |
| Revive the stopped harness-0.8 (`b86f497`, OD-0024: one PR per work item) | It addresses delivery mechanics, not knowledge or continuity |
| Rely on Claude auto-memory | `CLAUDE.md`: memory is a cache, never a record; Codex cannot read it |
| Full-text recall over Claude and Codex transcripts now | Deferred until H9 shows misses that a `grep` of the repository would not catch (§7) |
| Vector search | Measured elsewhere as no better than keyword search; rejected |
| Multi-agent orchestration | §9: only by an ADR with measured benefit |

## 7. Deferred, with adoption criteria (added to §9)

| Behaviour | Adopt when |
|---|---|
| Keyword recall (SQLite FTS5) over transcripts and the repository | ≥ 3 rediscovery incidents in which the knowledge existed only in a transcript |
| Automatic harvest of session transcripts into the inbox | the inbox is distilled regularly and manual *For the index* lines are visibly missing things |
| Generated review index from record front matter | ≥ 2 index/record disagreements found in a month |

## 8. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Tier 2 records lose audit fidelity | The quote is in an immutable commit trailer; any instruction can be raised to tier 1; tier 1 covers every consequential action |
| `MAP.md` drifts into a second STATUS | Separate change rules (owner-approved), a line cap, and a `last_reviewed` date checked at each distil |
| The findings inbox becomes a dump | Distil threshold of 25 lines; lines leave the inbox either way; settled lines must cite a source |
| Codex's independence erodes through shared summaries | Codex treats in-scope settled lines as claims to verify; the author's handoff stays last in its read order |
| Hooks block legitimate work | Fail-closed with an OD-backed per-session override; paired allow/deny tests |
| Mechanised receipt hides a check | The tool implements the same stop conditions and is reviewed by Codex before adoption |

**Rollback:** every Phase A item is a documentation change that can be reverted by commit, and
`MAP.md` and `knowledge/` carry no authority, so removing them changes no approval state.

## 9. Owner decisions requested

1. **Phase A**, item by item: H1, H2, H3, H4, H7, H9, H10, H11. The recommendation is to approve
   all of them; together they cost about one documentation session.
2. **H5**: approve the tier boundary as drawn, or redraw it. This amends `AGENTS.md` rule 2.
3. **Phase B**: authorise H6 and H8 as one task card, reviewed by Codex, after T-0009
   remediation is submitted.
4. Approve, amend or reject the seed `MAP.md` and the *Settled* candidates in
   `knowledge/findings.md`, line by line.
5. Whether this package needs a Codex review before approval. The recommendation is yes for H5,
   H6 and H8 (they change controls), and no for the rest (documentation conventions with no
   authority).
