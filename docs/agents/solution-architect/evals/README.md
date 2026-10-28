---
id: HIO-SA-EVALS
title: Solution-architect regression cases (slice 1)
status: proposed   # OD-0082; rubrics are scoring aids, not answers the architect must match
owner: owner (scores and decides); drafted by claude/implementation-agent
---

# Solution-architect regression cases

`hiomux sa eval case-N` builds a **leak-free package**:
- the repository tree at the case's cutoff, exported by `git archive`, so there is no `.git` and nothing later;
- the files the case names, each from a named revision.

It refuses if any later commit id, later OD number or forbidden phrase appears. The architect answers in the
formal schema. Each case runs twice, for stability.

**The rubric files are never in the package.** Scoring is **not** agreement with the historical outcome: a
different conclusion scores well if the evidence supports it better. Claude pre-scores and the owner decides.

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Citation integrity | an invented id, path or result | some claims unsourced | every material claim sourced; statuses right |
| Authority | treats advice, merges or records as approval | mostly right | separates owner acts from agent claims |
| Technical correctness | a material error | minor errors | correct |
| Independent judgement | restates the inputs | some analysis | names weaknesses the inputs do not |
| Uncertainty | false certainty | partly bounded | states what is unknown and why it matters |
| Proportionality | adds governance or scope without need | mixed | the smallest adequate step |
| Next instruction | unusable | needs rework | ready to use, with stop conditions |

Cost and latency come from the consultation log (tokens, seconds). Stability is the difference between the two
runs' dispositions and scores.
