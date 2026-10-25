<!-- Pasted into the Claude Code chat by the owner, 2026-10-25, verbatim, with no other words (first
person). Recorded by OD-0046. -->

**To Claude — Integrate S1b research and draft staged S1b design**

I authorise the documentation-only integration of the S1b readiness assessment and T-0002 RBA/NY Fed evidence, subject to normal Git integrity and scope checks.

1. Confirm the existing readiness-assessment merge is unchanged, and push main after verification.
2. Commit the T-0002 evidence on its existing branch, preserving every permission as unverified.
3. Check that no downloaded source data, unauthorised third-party material, credentials or implementation changes are included.
4. Integrate the evidence using `--no-ff`, after verifying the diff and repository checks.
5. Preserve the exact source URLs, access dates, quoted permissions and uncertainties.

Prepare **HIO-ADR-0010 revision 4 as a proposed amendment**, not approved policy.

Its preferred design is:

- S1b-1: official AUD and USD overnight cash observations and publisher cash-return indices, conditional on verified permissions.
- S1b-2: live FX and AUD-investor USD cash excess-return research, conditional on a separately authorised FX source.
- Additional triangulations: independently gated by source rights, calendars and methodological suitability.

The proposal must preserve the accepted S1a foundation, point-in-time invariants, immutable evidence model, independent research releases and HIO/MACSMSF boundary.

Address the implications for the existing S1b acceptance criteria, index triangulations, capture schedules, source-specific permissions and Q-010. Do not silently delete approved acceptance obligations.

For T-0002, prepare a concise owner-verification matrix showing each dataset and operation separately. In particular:

- Distinguish the RBA's special Cash Rate and Financial Data clauses from general CC BY permissions.
- Treat WM/Reuters and ASX-derived data as third-party material pending appropriate rights evidence.
- Record all applicable NY Fed reference-rate conditions, including disclaimers and derived-work identification.
- Distinguish automated retrieval rights from raw retention, calculation, reconstruction and consumer publication.

Do not mark rights as owner-verified, fetch further real data, contact publishers, implement adapters, create infrastructure or begin scheduled capture.

Return the precise ADR revision, source-rights matrix, unresolved questions and smallest next owner decisions.

Stop if any proposed design requires changing approved return mathematics or weakening existing evidence-integrity guarantees.
