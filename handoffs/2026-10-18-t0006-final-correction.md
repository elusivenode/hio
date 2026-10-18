---
id: HANDOFF-2026-10-18-t0006-final-correction
date: 2026-10-18
actor: claude/documentation-agent (Claude Opus 5.5, Claude Code session)
work_status: authorised (OD-0002) → submitted_for_review; NOT accepted
base_revision: 23ad27f3d25763d829b5846815b0568000d6648f
head_revision: self       # resolve: git log -n1 --format=%H -- hio/handoffs/2026-10-18-t0006-final-correction.md
work_commits: []
work_card: T-0006
---

# Handoff: T-0006 final harness correction (harness-0.2 → harness-0.3)

> A dated snapshot. Not a decision. It supersedes the navigation in
> `2026-10-18-harness-refinement.md`, which is kept unchanged as history.

## Changes, by directive correction

1. **Authorisation versus approval.**
   - Operating model §1.1 now separates four owner actions: *instruct*, *accept*, *approve* and
     *waive*.
   - An explicit instruction authorises bounded, reversible work immediately; transcription is
     audit only. Ambiguous instructions are not permission for consequential work.
   - The OD template now has `decision`, `record_status` and `owner_statement`.
   - OD-0001 is **corrected**, append-only: the original bare-path ambiguity and the earlier
     claim are preserved.
   - OD-0002 records this directive.
   - T-0006 gained a truthful state history and remains **not accepted**.
2. **Advice and adoption** (§1.1, §5.1, AGENTS rule 4).
   - Collaborator drafts are advice. The owner's adoption is what authorises.
   - The history index now states exactly how each directive arrived, without altering the
     archived files.
3. **Provenance** (§6.1).
   - `HIO-Actor` trailers are self-declared metadata, not proof.
   - Four provenance classes are distinguished.
   - The lightest credible proof now is verbatim, hashed, owner-supplied artefacts tied to a
     fixed commit.
   - Hosted PR reviews and signing are the evolution path; none was built.
   - The rule "a wrong-trailer closure is void" was removed, because it overclaimed.
4. **Provisional protocol** (§1.1, AGENTS rule 5).
   - The harness operates provisionally while HIO-ADR-0008 is proposed.
   - No prior approved OD is needed to begin owner-instructed work, which resolves the
     circularity.
5. **State-aware reviewer test.**
   - The review index now has an **Assigned reviews** table (empty: "No review target has been
     assigned"), kept separate from **Candidate review targets**.
   - §2.2 and §10 expect "No review target has been assigned" before an assignment, and the
     exact assignment after.
   - The fresh Codex test is **pending**.
6. **Deduplication.**
   - The AGENTS authority rules and bootstrap were condensed, with pointers to §1.1 and §2.
   - The `hio-session` skill was reduced to pointers.
   - A misplaced "Skills" bullet was moved back into operating model §2.
   - Nothing was deleted from history.

## Correction to an earlier dry-run claim

The previous handoff reported the reviewer-role dry run at `72d1e56` as "7/7 correct". Under
the state-aware criterion (§10), its Q2 answer **would fail**: it inferred a review target
(`85ef0fa..72d1e56`) when none had been assigned. The earlier handoff is left as written; this
note corrects it.

## Tests and evidence

| Claim | Method | Result |
|---|---|---|
| The branch did not move before editing | `git log -1` | `23ad27f`, clean |
| ADR `status:` lines unchanged | `git diff 23ad27f -- 'hio/docs/decisions/HIO-ADR-*' \| grep '^[-+]status:'` | see the owner report |
| No file outside `hio/` changed | `git diff --stat 23ad27f -- . ':!hio'` | see the owner report |
| YAML parses; links and anchors resolve; STATUS ≤150 lines | the documentation check procedure in `2026-10-18-harness-refinement.md` | see the owner report |

## Not run

- **No fresh Claude or Codex cold-start session was run for harness-0.3.** No dry run was
  repeated either. The independent test is pending.
- No independent review.

## Open findings

None recorded. No review is assigned.

## NOT approved by this session

- T-0006 is **not accepted**.
- HIO-ADR-0008 and every A01 ADR, standard and spec remain **proposed**.
- No review is assigned.
- No finding is closed or waived.

## Next permissible action

The owner decides:
1. accept or return T-0006;
2. whether to assign the A01 review, filling the *Assigned reviews* row with the exact SHAs.

No agent action is authorised beyond reading and drafting.
