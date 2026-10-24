<!-- The owner's message in the Claude Code chat, 2026-10-24, verbatim (a pasted block in the
owner's first person, with no other words). The authority for OD-0023. -->

I confirm that review receipt `e55cc8922ca2f018956fe6c6f4ff97e43d5acc17` is present in HIO `main`, and that OD-0022 records the receipt.

**I authorise a bounded S1a remediation slice under harness-0.7**, addressing findings F-REVIEW-2026-10-24-s1a-1-1, -2, -3, -5 and -6.

Start a new remediation branch from current `main`, ensuring the receipt commit is an ancestor. Stop if this prerequisite fails.

Implement the following corrections:

1. Derive source identities and complete transitive lineage from verified release and receipt records. Never accept caller-supplied source IDs as authority for rights decisions.
2. Enforce consumer approval by distribution class. Approval for `hio_internal` must not authorise `smsf_app`. Preserve independent approvals and withdrawals for multiple classes.
3. Validate receipt existence and byte integrity before an observation can be selected or used to construct a release.
4. Ensure reproducibility checks fail on corrupted stored release bytes.
5. Provide atomic multi-object commit semantics: failures must not expose partial releases or catalogue transactions.

For each finding, reproduce Codex's counterexample in a regression test before correcting the implementation. Preserve all previously passing tests and approved financial mathematics.

Do not change the approved temporal semantics, the observation standard, or the implementation of findings 4 and 7. Those remain blocked pending Q-001 and Q-002 decisions.

Prepare concise, separately reviewable draft standard amendments for Q-001 and Q-002, but do not implement or approve them yet.

Submit the fix commits and a remediation response referencing all seven findings, explicitly distinguishing five remediation claims from two unresolved policy questions.

Open an author PR with a fixed `Submission-Head`, CI evidence and a completion handoff. Do not mark any finding verified closed, merge the implementation, accept S1a or begin S1b.

The next independent Codex verification requires a separate owner assignment at the fixed submission head.
