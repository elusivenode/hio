<!-- Pasted into the Claude Code chat by the owner, 2026-10-24, verbatim, with no other words (first
person). Recorded by OD-0031. -->

I have reviewed Codex's independent verification `VERIFY-2026-10-24-s1a-1-6` at commit `3cb3dd073f832f2cb9d49a1d2690a131b14e7f37`, reviewing S1a PR #2 head `191ac0f0461b59c61c8b11c60befd6f7f04da6b6`.

Under harness-0.7 §6.2, I authorise a bounded remediation-before-receipt exception for this verification record.

Before proceeding:
- Confirm the exact reviewer commit and record path.
- Independently calculate the record SHA-256 and verify it against Codex's reported digest.
- Verify reviewer-only scope and the assigned review identity.
- Record the exact verified digest, original reviewer provenance and this owner exception in an OD.
- Stop on any discrepancy.

This is an explicit disposition for technical remediation, not receipt into `main`, S1a acceptance or permission to change approved standards.

**Continue F4/F7 remediation on existing PR #2, within OD-0030.**

Correct the two demonstrated defects:

1. **Processing completeness:** Account for every captured receipt, including receipts with unchanged numeric values but stronger timing evidence. Preserve the distinction between capture evidence, capture mode and processing outcome. A query or resolution must refuse incomplete processing. Add Codex's counterexample as a regression proving that identical T, Q and evidence identity cannot silently produce different results.

2. **Predictive admissibility:** Enforce `predictive_pit_admissible` at the point-in-time release-building boundary. A Q>T market result marked inadmissible must be refused before publication, with no partial release output. Do not add a caller override or invent a descriptive-publication exception.

Preserve the approved Q-001 and Q-002 contracts, existing mathematical calculations, financial `data.csv` outputs and previously verified F1/F2/F3/F5/F6 behaviour.

Add focused adversarial tests, reproduce both failures before fixing them, and rerun the full regression suite.

Append fixes to PR #2 and submit a new fixed `Submission-Head` with a concise remediation response.

Codex may independently verify the corrected head within the existing bounded F4/F7 assignment, subject to the current evidence-handling rules. Neither agent may close findings by author assertion, merge either PR, accept S1a or authorise S1b.

Escalate only if implementation reveals a genuine conflict with approved contracts or requires a new policy decision. Do not initiate another harness redesign.
