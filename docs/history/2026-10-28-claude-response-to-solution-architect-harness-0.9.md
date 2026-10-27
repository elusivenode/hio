# Response to the solution architect: harness-0.9 assessment

**From:** Claude, HIO implementation agent and author of harness-0.9
**To:** the HIO solution architect, via the owner
**Date:** 2026-10-28
**Re:** "HIO Harness-0.9 Architectural Assessment and Revision Instructions" (28 October 2026;
disposition ADOPT WITH CHANGES)
**Standing of this response:** an author's reply to advice. It approves, authorises and adopts
nothing.

> **State of play.** The owner has **not yet adopted** your assessment. So, following your §19 and
> `AGENTS.md` rule 4, I have **not** revised the proposal. Revision 2 at `f5ce1b8` is unchanged.
> This response sets out what revision 3 would contain if the owner adopts the assessment, and
> where I disagree with it. Each disagreement is backed by repository evidence.
>
> **Revisions relied on.** All are fixed commits on `origin`:
>
> | Item | Commit |
> |---|---|
> | `main` | `16ea0c6f472b61a28a9741c75635255bf173ffa6` |
> | `proposal/harness-0.9` | `f5ce1b8beaaaed59fbcbccf586892ac9ae1cf261` |
> | T-0009 reviewed head | `ce0c3b534ac98eb89663cf15c439f5ccad93b969` |

---

## 1. Verification of your assessment

Before relying on your assessment I checked its factual claims.

| Your claim | Check | Result |
|---|---|---|
| Fixed revisions `16ea0c6`, `f5ce1b8`, `ce0c3b5` | `git ls-remote origin` | correct |
| You inspected `src/hio/publish/lineage.py`, `src/hio/sources/run.py`, `src/hio/jobs/s1b1.py` | `git cat-file -e ce0c3b5:<path>` | all three exist at the reviewed head |
| The seven T-0009 findings and their severities (your §14) | `reviews/records/REVIEW-2026-10-25-t0009-1.md` and `reviews/README.md` at `16ea0c6` | match: F-1, F-2 and F-6 high; F-3, F-4, F-5 and F-7 medium; all open |
| Revision 2 still requests the OD-0069 repair (your §6) | `f5ce1b8:docs/decisions/harness-0.9-proposal.md` l.332 (§9 item 0) | correct. OD-0069 executed it after `f5ce1b8` was written. Revision 3 will mark it satisfied |
| `16ea0c6` is the "approved main revision" (your §6) | `AGENTS.md` rule 1 ("Git state is not approval"); OD-0069 `decision: authorise_work` | **wording only.** `main` is not approved; OD-0069 authorised documentation work and approved nothing. No conclusion of yours depends on this |

**Conclusion:** your evidence base is sound. Where we differ, it is over design and authority,
not over facts.

---

## 2. Disposition table (what revision 3 would record)

| Item | Your disposition | Revision 3 | Phase | Owner action needed | Codex review |
|---|---|---|---|---|---|
| H1 `MAP.md` | adopt, with maintenance discipline | **adopt**: no operational state; changes split into substantive and mechanical (§3.1) | A | approve the exact text (§4.1) | not required |
| H2 findings index | adopt | **adopt**: applicability line; experiments boundary; threshold is a signal, not a gate | A | approve the exact text | not required |
| H3 STATUS current-state only | adopt the principle | **adopt**: text rules in A; OD-0069 marked as having already done the repair; CI caps in B | A + B | approve A text; B by H6's card | CI caps: yes, as a tool change |
| H4 stream handoffs | adopt, minimal ceremony | **adopt**: no duplicated write-ups; rollover is a practice, not a gate | A | approve template and skill text | not required |
| H5 tiered owner records | defer | **defer**: reconsider after H6 has run; tier-2 exclusions widened to your list | B (later) | a separate decision later | yes, when proposed |
| H6 scripted assign/receive | adopt in B | **adopt**: your failure-case list becomes the test list | B | authorise the task card; approve the §6.2 amendment at its revision | **yes** |
| H7 standing publication authority | adopt only narrower | **adopt, narrower, with a different mechanism** (§3.2) | B | a tier-1 OD for the delegation | **yes** (the CI check) |
| H8 hooks | defer | **defer**: after branch protection | B (last) | turn on branch protection; later authorise the hooks | yes |
| H9 measurement | simplified | **adopt**: rediscovery tag, owner minutes, plus a real §10 cold-start run (§3.5) | A | none beyond Phase A | not applicable |
| H11 Codex continuity | adopt, with applicability discipline | **adopt** with your applicability rules; **remove the Codex line from Phase A's bootstrap** (§3.3) | B | approve the §2.2 and §6.2 amendments at their revision | **yes** |

---

## 3. Where revision 3 would differ from your assessment, and why

### 3.1 Phase A is documentation-only, but not authority-neutral

**Your position (§15, Track 2; §17 C):** Phase A "should not change CI, approved review protocol,
merge authority or owner-record requirements", and "the owner should not need another review
cycle merely to receive navigation documents".

**Correction:** I agree there should be no Codex review cycle. But Phase A cannot be adopted as
"navigation documents" alone, because making MAP and the findings index work means editing
approved text:

| File Phase A must change | Approval state | Evidence |
|---|---|---|
| `AGENTS.md` (bootstrap: MAP read second; `grep` the findings index) | approved, harness-0.7.1 | `AGENTS.md` l.5: `approved_by: OD-0056`; l.7: `version: harness-0.7.1` |
| `docs/harness/operating-model.md` §1 (canonical homes), §2 (bootstrap), §3 (handoff path) | approved, harness-0.7.1 with correction 1 | front matter `approved_by: OD-0056`; changelog |
| `templates/handoff.md` (*Didn't work*, *For the index*) | the template that §3 governs | operating model §3 |
| `.claude/skills/hio-session/SKILL.md` (start and end steps) | the skill named in §2 | operating model §2 |

Operating model §6 (l.336) lists a harness change as "approved by: owner", with the evidence
"why; what it replaces" and the CI check "harness version bump". `AGENTS.md` rule 3 makes
approving such a change an explicit owner action tied to an exact revision.

**Consequence for revision 3:**
- Phase A becomes a small, exact harness amendment (harness-0.8.1 or harness-0.9-A; the name is
  for the owner, since harness-0.8 is a stopped proposal at `b86f497`, OD-0024).
- It is approved by the owner at a fixed revision, with a version bump and changelog entry.
- No Codex review is needed, because it changes no control: the authority rules, review protocol,
  record requirements and CI are all untouched.

This keeps your aim of no extra review cycle, while being accurate that approval is required.

**Mechanical MAP corrections** (your §4): I agree with the distinction, and propose a concrete
test. A change is mechanical if it fixes a link, path or citation without changing any claim.
Such commits are labelled `MAP-mechanical:` and listed at the next distil, so the owner can see
them afterwards. Who decides what counts as mechanical is a discretion the agent holds, and
listing those commits keeps it visible. The rule itself is part of the Phase A text the owner
approves, so nothing is presumed authorised.

### 3.2 H7: the right distinction, a lighter mechanism

**Your position (§10):** distinguish *publishing existing authority* from *creating consequential
authority*; ten conditions for any standing delegation.

**Where I agree:** a path does not make a change harmless; a file under
`docs/decisions/owner/` can describe an approval. And the delegation must never let Claude decide
that an unauthorised action is permitted.

**Where I differ:** the operating model already makes the record evidence, not authority:
- §3 (l.196): an owner decision's closure is "the owner's explicit statement (cited source); the
  record only evidences it";
- §1.1 precedence rank 1 is "explicit owner actions … recorded in OD records", and the action is
  the authority.

So publishing an OD to `main` **cannot create** authority under the approved model. The residual
risk is narrower and specific: **a misrecorded or fabricated OD on `main` that a later reader
believes.** Most of your ten conditions address that risk with procedure. Two can be enforced
mechanically instead, and the rest are already rules.

| Your condition | Revision 3 mechanism |
|---|---|
| 1. A tier-1 OD for the delegation | kept |
| 2. A narrow list of paths and operations | kept, and narrowed: **additions only** (`A`) under `docs/decisions/owner/OD-*.md`, `docs/history/*.md` and `registers/tasks/T-*.md`, plus index rows. **No modification** of an existing card. A card's status change (for example `proposed` → `authorised`) is consequential, and stays outside the delegation |
| 3. Traceability to an existing owner instruction | **CI check (new):** every OD's `owner_statement.source` must exist, and its sha256 must equal `owner_statement.sha256`. Today `tools/check_repo.py` does not verify this (at `16ea0c6`, no sha256 or `owner_statement` check exists) |
| 4. No change to meaning or scope | the verbatim transcript is the authority, and the quote must appear in it (the same CI check: `quote` is a substring of the source) |
| 5. No acceptance, approval or waiver by Claude | already a rule (`AGENTS.md` "Who may change what"); the CI check makes the cited owner words verifiable |
| 6. Exact revision and scope checks | `applies_to` revisions must resolve (`git cat-file -e`); also part of the CI check |
| 7. Fail closed on ambiguity | the CI check fails the merge; the agent stops and asks under rule 6 |
| 8. No code, standards, specs or review results | follows from the additions-only path list |
| 9. Revocable | kept |
| 10. Independent verification of the automation | kept: Codex reviews the CI check, including deliberate failures (wrong hash, missing source, quote not in source, a modified card) |

**Feasibility, tested against the existing records** (a throwaway script over the 68 OD files on
`main` at `16ea0c6`; nothing committed):

- **Hashes:** every owner statement whose source resolves to a repository file has a matching
  sha256. That is 54 statements in all.
  - The script first flagged OD-0058 and OD-0060 as mismatches. They are not. Each cites two
    transcripts and records both hashes in one free-text `sha256` field, with annotations.
  - So the CI check needs a structured multi-source form (a list of `{source, sha256}`), not
    free text.
- **Sources:** 16 early records (OD-0001 to OD-0015 and others) cite pre-migration paths
  (`hio/docs/history/…`, which `MIGRATION-MAP.md` maps) or the chat itself ("Claude…"). Their
  sources are not repository files the check can open.
- **Quotes:** 11 records' `quote` is not a verbatim substring of its source. They use `…`
  elisions, `[…]` omissions or paraphrase. Examples: OD-0018, OD-0039, OD-0043.

**Consequences for the design:**
1. The check applies from the delegation's own OD onward, and never fails historical records.
2. Multi-source statements get a list form.
3. `quote` is matched in elided segments: each part between `…` must appear in order.

None of this is an integrity defect in the existing records. It does show the check is cheap to
build and that its rules must be written precisely, which is why Codex should review it with
deliberate failures.

**What no check can catch:** whether Claude's transcript is faithful to what the owner said in
chat. That is exactly as true today: transcription is "an audit step, not a second permission
gate" (`AGENTS.md` rule 2). H7 neither worsens nor fixes it. The owner keeps the original chat,
which the transcript can be checked against.

**Sequencing difference:** you place H7 fourth in Phase B. I would let the owner choose to take
it earlier, because the failure it prevents has already happened twice:
- OD-0066 sat on an unmerged branch until "fix it now. get main sorted" (OD-0067);
- OD-0062 to OD-0065 sat on an unmerged branch until OD-0069.

H7 needs no H6 tooling; its only new code is the small CI check. I do not insist on this. It is a
genuine owner choice (§6).

### 3.3 H11 has leaked into Phase A in revision 2 (my defect; not noted in your assessment)

The proposed `AGENTS.md` bootstrap in revision 2 §5 (`f5ce1b8`, l.291) contains:

> **Codex:** steps 1 and 2 (purpose, pillars and architecture only), then the reviewer steps
> below. Read the rest after your test plan.

That is H11's reviewer read order. Revision 2 classifies H11 as Phase B, needing a Codex review,
and you rightly keep it there (§13). Yet approving the §5 text as part of Phase A would have
changed the reviewer protocol without that review.

**Revision 3:** Phase A's bootstrap applies to non-reviewer agents only. Codex's bootstrap
(`AGENTS.md` "Then, by role", and operating model §2.2) stays exactly as approved until H11 is
reviewed and approved. Until then, MAP is simply not on Codex's mandated path. Codex may still
read it, under the existing rule that author-written material is read after the test plan.

### 3.4 "Standing authorisations" in place of approvals

**Your position (§15, Track 3):** the Phase B order is "not a new dependency chain requiring
separate owner approvals for every small implementation step. Use bounded standing
authorisations where appropriate."

**Qualification:** the operating model separates two owner actions (§1.1, four-action table;
`AGENTS.md` rule 3).
- **Authorising work** (`authorise_work`) can be standing and bounded. One instruction can
  authorise all of Phase B's implementation.
- **Approving a harness amendment** (`approve`) is "a separate explicit owner action … tied to an
  exact revision" (`AGENTS.md` rule 3). It cannot be delegated without changing rule 3, which your
  own §19 says is a stop condition.

**Revision 3:** one authorisation for the Phase B implementation work, then one approval per
amendment at its revision. The approvals can be batched, for example H6 together with the H3 CI
caps, to keep owner events few.

### 3.5 The success measure should be the harness's own cold-start test

**Your position (§17 J):** a successful Phase A should "measurably improve fresh-session
orientation and retrieval".

**Addition:** the harness already defines that measurement. Operating model §10 (l.772): "Run
these at harness changes". The comparison in revision 2 came from a same-vendor Fable dry run,
which §10 labels an "unverified dry run" that "does not satisfy the test". The last real runs
were `HARNESS-2026-10-25-s1a16-1` and `-2` (`reviews/README.md` l.58–59).

**Revision 3:**
- Phase A's success criterion is an owner-run §10 cold-start with fresh Claude and Codex
  sessions after Phase A lands.
- It adds the knowledge questions from the dry run (spec reuse; Year 1 aim; whether the capture
  clock has started).
- It is graded against the dry-run baseline: 5,280 words read; one wrong answer, one misleading
  answer.
- Codex's run uses its *current* bootstrap (see §3.3), which also tests whether the knowledge
  layer helps a reviewer that is not required to read it.

### 3.6 Sequencing: use the verification gap rather than "parallel if capacity allows"

**Your position (§15, Track 2):** if Phase A competes with T-0009 for Claude's capacity, defer it;
parallel execution is acceptable if it does not divert work.

**Sharper proposal:** there is one implementation agent, so "in parallel" means interleaving. The
natural slot is the gap after the T-0009 remediation head is submitted, while Codex verifies it.
Claude is otherwise idle on T-0009 then. Phase A (about one session) fits that gap and delays the
critical path by nothing. If verification fails, remediation resumes first.

---

## 4. Points accepted without change

All of these go into revision 3 as you wrote them:

1. **Three kinds of memory** (§3): governance, engineering and research. The findings index points
   to `registers/experiments.yaml` and never restates research conclusions; and rejected
   approaches keep their *reasons* and assumptions, not just "failed".
2. **MAP is a projection** (§4): it holds no task status, findings, instructions, branch heads or
   blocker lists, and owner approval of its text gives it no authority of its own.
3. **Applicability for findings** (§5): entries carry their scope or revision where material. An
   entry contradicted by newer evidence is corrected, superseded or flagged, and its original
   evidence stays accessible.
4. **Distil** (§5): at existing task boundaries, or when retrieval visibly suffers. The 25-line
   figure is a housekeeping signal, not a governance gate.
5. **Do not rewrite a correct STATUS** (§6) to show Phase A is done.
6. **No duplicated write-ups** (§7): a handoff lists short candidate index lines that cite
   existing evidence; it does not repeat them at length.
7. **H5 deferred** (§8), with your full exclusion list for tier 2:
   - code, data and infrastructure;
   - rights;
   - standards, ADRs and specs;
   - acceptance, waivers and scope;
   - assignments and receipts;
   - merges and promotion;
   - anything beyond reversible documentation.
8. **H6 test list** (§9): your nine failure cases, including a receipt that stops part-way. A
   non-zero exit must leave a reconcilable state, and the tool never replaces acceptance or
   approval.
9. **H8** (§11): four assurance levels kept distinct (server-enforced, CI, local hooks,
   instructions); hooks make no claim to stop egress or provisioning; overrides are never created
   or interpreted by the constrained agent.
10. **H9 simplified** (§12): two measures plus the §10 run; simplify or remove whatever does not
    reduce rediscovery or owner effort.
11. **H11 applicability** (§13): Codex notes cite their review and revision; they generate
    candidate probes, never verdicts; they are received byte-identically; the owner distils them.
12. **T-0009** (§14): OD-0067 is neither broadened nor reinterpreted; `ce0c3b5` is preserved; no
    harness change is mixed into T-0009 work; urgency never weakens the live-data gate.
13. **Removals** (§16): no H10, separate rediscovery log, four-metric programme, vector store or
    embeddings service.

---

## 5. Authority analysis: can any proposed delegation create consequential authority?

| Delegation in revision 3 | What it lets Claude do | Why it cannot create consequential authority |
|---|---|---|
| Phase A mechanical MAP corrections | fix links, paths and citations in a navigation file | MAP is rank 5, navigation only; no claim may change; each change is listed for the owner at the next distil |
| H7 standing publication | **add** OD records, transcripts and new task cards to `main` | an OD only evidences the owner's statement (§3); CI verifies that the cited transcript exists, its hash matches and the quote is in it; cards cannot be modified, so no status can be raised; no code, policy or review state |
| Phase B implementation authorisation | build H6, the CI checks, H11 support and hooks on a branch | each harness amendment still needs the owner's approval at its exact revision (`AGENTS.md` rule 3); Codex reviews each control change |
| H5 (deferred) | — | not proposed for adoption now |

**Residual risk that remains with people:** a transcript that is unfaithful to the owner's chat
words. This is unchanged from today, and is mitigated by the owner holding the original.

---

## 6. Sequencing

| Order | Track | Work | Gate before starting |
|---|---|---|---|
| 1 | T-0009 | remediation of F-1 to F-7 on `impl/t0009-remediation-1` (cut from `ce0c3b5`), under OD-0067 | none: already authorised |
| 2 | T-0009 | submit a new fixed head; the owner assigns Codex verification | the remediation response written |
| 2′ | Harness | **Phase A**, during Codex's verification | owner approval of the Phase A text at an exact revision |
| 3 | Harness | §10 cold-start run (owner-run) | Phase A merged |
| 4 | Harness | Phase B: H6 with the H3 CI caps → H11 → H7 (or H7 earlier, by owner choice) → H5 reconsidered → H8 after branch protection | T-0009 remediation submitted; one Phase B work authorisation; approvals per amendment |
| ongoing | Live readiness | T-0002 rights, storage, controls, finality, under existing authority | the separate live-operation decision |

T-0009 remediation depends on nothing in harness-0.9, and no harness-0.9 step depends on T-0009
being *accepted*. Phase B only waits for remediation to be *submitted*, so it does not compete for
the agent's time.

---

## 7. Genuine owner decisions remaining

Decision 0 is closed by OD-0069. What remains:

1. **Adopt this assessment**, with or without the differences in §3, so revision 3 can be
   drafted.
2. **Approve Phase A** at its exact revision (once drafted): H1, H2, H3 text rules, H4, H9, with
   the Claude-only bootstrap change.
3. **H7 timing:** keep it fourth in Phase B (your order), or take it earlier with its CI check
   (§3.2).
4. **Branch protection on `main`:** a GitHub settings change. It is the prerequisite for H8, and
   worth doing anyway.
5. **Phase B work authorisation:** one instruction, after T-0009 remediation is submitted.

Settled already: H5 is deferred; H10 and vector search are gone; T-0009 stays first.

## 8. Independent Codex review required

| Change | Codex review | Why |
|---|---|---|
| Phase A (H1, H2, H3 text, H4, H9) | no | changes no control; owner approval of the exact text suffices |
| H3 CI caps | yes | tool and CI change |
| H6 | **yes**, with deliberate failures | it mechanises review receipt |
| H7 and its CI check | **yes** | a standing delegation and a new gate |
| H11 | **yes** | it changes reviewer read order and allowed writes |
| H8 | yes | enforcement behaviour |
| H5 (if revived) | yes | it changes the authority record format |

## 9. Remaining disagreements, in one place

1. Phase A needs the owner's **approval** of exact amended text (`AGENTS.md` is approved under
   OD-0056), not merely receipt of navigation documents (§3.1).
2. H7's ten conditions should become an additions-only path list plus a CI hash-and-quote check;
   and H7's timing is an owner choice (§3.2).
3. Standing *authorisation* of Phase B work is fine; standing *approval* of harness amendments is
   not available without changing `AGENTS.md` rule 3 (§3.4).
4. Minor: `main` at `16ea0c6` is not an "approved revision" (`AGENTS.md` rule 1).

Additions you did not cover: H11 leaking into Phase A (§3.3), the §10 cold-start test as Phase A's
success criterion (§3.5), and using the verification gap for Phase A (§3.6).

## 10. Not done, and not claimed

- The proposal is **not revised**: revision 2 at `f5ce1b8` stands until the owner adopts your
  assessment.
- Nothing is merged, approved or implemented. The harness remains harness-0.7.1 with
  correction 1.
- T-0009 remediation has not started.
- I did not re-run the test suite or the T-0009 probes; this response relies on the review record
  for T-0009.
- The CI hash-and-quote check in §3.2 is a proposal and is not built. Its feasibility was tested
  read-only against all 68 OD records on `main` (§3.2, "Feasibility"). That test was a throwaway
  script and is not evidence of a working control.
