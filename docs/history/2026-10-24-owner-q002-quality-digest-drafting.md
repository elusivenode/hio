<!-- Pasted into the Claude Code chat by the owner, 2026-10-24, verbatim, with no other words (first
person). Recorded by OD-0034. -->

**To Claude — HIO Q-002 reproducibility-pin amendment**

Codex's F7 round-9 review identifies a missing provenance dependency: quality-decision events can change a result while the existing evidence, resolution and algorithm pins remain identical.

I select a separate `quality_digest` as the preferred architectural resolution, subject to confirming the exact counterexample and approved contract.

Before changing anything, locate and independently verify `VERIFY-2026-10-24-s1a-1-9`, including its reviewer commit, record hash, scope and assignment. Stop if the evidence cannot be verified.

Prepare a narrow amendment to the Q-002 reproducibility contract adding `quality_digest`, computed from the canonical quality decisions relevant at Q.

Specify:
1. The exact events and fields included in the digest.
2. Deterministic ordering and canonical encoding.
3. The empty-history representation.
4. How quality events after Q are excluded.
5. How the new pin participates in result and release provenance.
6. Tests proving fixed-cutoff stability, sensitivity to relevant quality changes, independent reconstruction and refusal on mismatched pins.

Preserve the existing meanings of `evidence_digest`, `resolution_digest` and `algorithm_revision`.

Do not change implementation code, previously approved standards, or Codex records in this step.

Return the exact amendment revision and the minimal approval decision needed for implementation. Continue F7 under the existing PR #2 only after the standards amendment and review-evidence prerequisites have been satisfied.

Do not initiate another harness redesign, merge PR #2 or #3, accept S1a or authorise S1b.
