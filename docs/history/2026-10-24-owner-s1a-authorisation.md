<!-- The owner's message in the Claude Code chat, 2026-10-24, verbatim (a pasted block in the
owner's first person, with no other words). The authority for OD-0017 (recorded) and OD-0018. -->

I have reviewed the HIO state at `dc4fd02`.

**1. S1a authorisation**

I authorise S1a under HIO-ADR-0010 revision 3, using the approved boundaries and acceptance requirements.

For OD-0017:
- Migration source: `dc4fd0241fe039fd2e8361cb82604a59a0458413`.
- Destination: a new private repository, `elusivenode/hio`.
- Leave `docs/hio-a01-baseline` unmerged. Any pointer change to `macsmsf/main` requires a separate reviewed change.
- Use a history-preserving subtree split with local provenance, identity, content-hash and link verification before the first push.
- Adopt Python 3.13, `uv`, `pytest`, `hypothesis`, `ruff` and DuckDB.
- GitHub Actions CI only, with minimum permissions and no secrets or scheduled workflows.

You may create the private repository and migrate the verified history within this scope. Stop and report any discrepancy before pushing.

S1a is strictly synthetic-fixture-only. No source-data network fetch, live data, credentials, buckets, scheduled capture or SMSF integration is authorised.

This is **authorisation to perform S1a work, not acceptance of S1a or authorisation of S1b**. Submit the implementation and evidence at a fixed revision for independent Codex review.

**2. T-0004**

I confirm the cross-lineage review mechanics described in OD-0010. Codex may review the pinned T-0004 target at `fe3fdc7` in a separate read-only worktree and commit its review evidence only on the scoped review branch. Do not merge the amendment without my subsequent decision.

**3. Parallel work**

Continue T-0002 and T-0003 under their existing restrictions. Source permissions remain unverified and blocked. Vendor questions remain drafts; do not contact vendors.

Separately, prepare a proposed, SMSF-owned ETF diagnostic task card. Its objective is to distinguish asset-class returns from fund-specific underperformance, quantify ETF liquidity and tracking characteristics, identify current economic and factor exposures, and evaluate hypothetical exposure-replacement scenarios. Use read-only interfaces and preserve all existing `macsmsf` functionality.

Do not implement this SMSF workstream until separately authorised.

Correct the material roadmap date and gate inconsistencies without changing approved architectural substance. Preserve any historical wording that forms part of an approved blob unless changed through the appropriate process.

Report the exact revisions, completed migration checks, outstanding decisions and review requirements.
