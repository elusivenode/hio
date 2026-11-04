---
id: HIO-SA-PERFORMANCE-REVIEW-1
title: "Solution architect: first performance review (draft)"
status: proposed           # drafted under OD-0155 item 5; accepts nothing, changes no power
owner: owner (decides); drafted by claude/implementation-agent
created_at: 2026-11-04
evidence: "~/.hio-runs/*/sa/consultations.jsonl and each answer file (local, never committed); the ODs and handoffs cited"
---

# Solution architect: first performance review

> **Not independent.** Claude wrote this about advice given to Claude, and Claude chose the questions. No one has graded these 14 answers against outcomes. ChatGPT's earlier grading (OD-0087) covered the stress cases, not this real use.

## Summary

**Claude's recommendation: continue bounded advisory use, with no change in powers.** It repeatedly changed Claude's drafts before they reached the owner, and its one serious limit in use was the context budget (OD-0155 item 4). The evidence shows the advice was useful and adopted. It doesn't show the advice was right, because most of it hasn't met an outcome yet.

The review was due after five consultations (OD-0089) and came after 14.

## What was used

| Measure | Result |
|---|---|
| `ask` consultations | 14; `assess` was never used |
| Mechanically clean | 14 of 14: status `ok`, no problems, `gpt-6.1-sol` at `high`, no auto-loaded `AGENTS.md` |
| Time | median 186 s, longest 463 s, about 43 minutes in all |
| Output tokens | about 74,000, reasoning included |
| Counted as genuine | 14 with the identity check `…180220-ask-1a5f`, 13 without. OD-0128 left this to the owner |

## What each consultation did

| Consultation | Question | Advice | What happened |
|---|---|---|---|
| `…180220-ask-1a5f` | identity check | states its role | none needed |
| `…192519-ask-dab7` | harness state | approve Phase A now; no revision 5 | no citation found in the records; Phase A was approved (OD-0091) |
| `…211545-ask-2e83` | H6 false closure | option B: separate finding states from receipt | adopted (OD-0100, OD-0104) |
| `…103714-ask-15f7` | H6 recovery | refuse pre-existing imports | adopted (OD-0109); H6 was parked later with a high finding open (OD-0114) |
| `…120200-ask-1eee` | state against target | prioritise capture; leave H6 parked | that order was followed (OD-0115) |
| `…121425-ask-c603` | Azure client | SDKs behind `BlobBackend` | adopted (OD-0117) |
| `…182940-ask-9dab` | architecture review | finish the cash path before paying for data | became the base-camp criteria (OD-0129) |
| `…185323-ask-0373` | soak alert | split, with two corrections | became T-0013 |
| `…194055-ask-6296` | base-camp scope | non-live build plus gated checklist | became T-0014 |
| `…202344-ask-4dcb` | B-2 result | the probe measured `completed_at` wrongly; keep B-3 blocked | changed the re-run (OD-0134); C5 was later removed from the capture gate by the owner's revision (OD-0139), not by this measurement |
| `…141451-ask-15e3` | why blob storage | keep Azure, narrow the gate, shift to factors | fed the factor-first draft (OD-0136) |
| `…142328-ask-3901` | Claude's sequencing | revise: capture first, and the reasons for removing gates are too broad | changed the drafts (handoff 2026-11-03) |
| `…165541-ask-dee0` | Claude's go-live plan | change the order | changed the alert order; **caught two errors Claude had made** (OD-0142, handoff 2026-11-04) |
| `…093209-ask-a45b` | next work | real cash results and one duration experiment | set the work order (OD-0147, OD-0150) |

## Against ChatGPT's condition 4 (OD-0089 correction 1)

- **A substantive disagreement with Claude: yes.** `…142328-ask-3901` and `…165541-ask-dee0` both rejected parts of Claude's drafts.
- **A case where proceeding beat stopping: yes.** `…192519-ask-dab7` advised approving Phase A now, and `…141451-ask-15e3` advised narrowing a gate.

## Strengths

- **Evidence labels held up:** answers separate verified, reported, owner-decided and judgement, and name the revision read.
- **It stated limits on its own advice:** for example, `…103714-ask-15f7` said that narrowing "does not establish that the next implementation will be correct", and H6 did go on to fail again.
- **It stayed in its role.** Its answers said advice only, and I found no attempt to approve, waive or direct Codex in the opening text of each answer. I did not read every answer in full for this draft.

## Weaknesses

- **It went stale in use.** The last two consultations ran at `310d7dd`, because `main` exceeded the budget, so they relied on Claude's description of newer state. That weakens the "repository evidence first" rule exactly when the question was most current. The budget change addresses this only until the bundle grows again.
- **Agreement is hard to read as quality.** Claude framed every question, and most recommendations were adopted. That could reflect good advice or framing that led to it.
- **Its value on H6 is mixed:** its advice narrowed the design twice, and seven verifications later H6 was still parked.
- **Some links don't work later:** answers link to absolute paths inside a session clone.
- **Slow on broad questions:** 463 s for the longest. Acceptable for how it is used.

## Not measured

- Whether any advice proved correct against an outcome. The soak and real factor results are the first real tests.
- Errors the architect missed. Codex still found defects in work it had advised on, but no one has traced those back.
- Any held-out case: none is named, so none has been run.

## For the owner

1. Accept this review, or have it graded independently (ChatGPT graded the stress test).
2. Name the two held-out cases, re-run at cutoff `cab1747` to stay clean (OD-0089 correction 1).
3. Decide whether `1a5f` counts, though it changes nothing here.
4. Consider a second review after the soak, once outcomes exist.
