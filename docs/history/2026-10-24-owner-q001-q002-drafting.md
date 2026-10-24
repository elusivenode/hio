<!-- Pasted into the Claude Code chat by the owner, 2026-10-24, verbatim, with no other words. It
is written in the first person and combines solution-architecture advice ("As
solution-architecture advice for owner adoption") with a drafting instruction ("This
instruction authorises drafting only"). Recorded by OD-0026. -->

I acknowledge Codex's independent F6 verification at `d9fa2766126aa38bb9cfbce83f37818a0d65fe4a`. F6 is verified closed within the reviewed S1a local single-writer storage contract.

As solution-architecture advice for owner adoption, I support Option A for both Q-001 and Q-002, subject to these refinements:

**Q-001:** Point-in-time queries must evaluate quality eligibility using the quality decisions effective at their cutoff. Later adjudications must not retroactively alter earlier point-in-time results. Restated-quality analysis must be explicitly labelled. Distinguish market knowability from HIO's own historical quality eligibility.

**Q-002:** Equally evidenced contradictory observations must not be resolved by ingestion order. Preserve the original observations and represent conflicts and resolutions with timestamped, append-only events. An unresolved conflict makes the key unavailable for affected research results from the time the conflict becomes known, without retroactively changing earlier point-in-time results.

Please refine the existing Q-001 and Q-002 draft amendments accordingly, including the relevant information clocks, mode-specific behaviour, conflict adjudication and executable regression invariants.

This instruction authorises drafting only. Do not change implementation code or the approved observation standard yet.

Preserve Codex's F6 verification evidence and all previous review records. Do not merge PR #2 or PR #3, close findings 4 or 7, or begin S1b.

Return the exact draft revision and the minimum remaining owner decisions needed to authorise implementation. Do not initiate further harness redesign.
