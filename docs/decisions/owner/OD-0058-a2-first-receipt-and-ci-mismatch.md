---
id: OD-0058
title: "Supervised first receipt under harness-0.7.1: VERIFY-2026-10-25-adr0012-2 (dac54f5) received by byte-identical import with Option (b); evidence receipt succeeded; CI failed on a missing HIO-Actor trailer (a procedure/CI mismatch); history preserved; first-use validation NOT passed; routine receipt NOT enabled"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-a2-supervised-receipt-authorisation.md and docs/history/2026-10-25-owner-a2-receipt-ci-recovery.md (pasted by the owner, verbatim)
  sha256: e863ba2f35b71e6c2ee6a8e8a5389534e21f7546af0a928cc6fd930c92a5d308 (authorisation); d5e876225ba194510c5362fdc7179a026d8f5547098ecc491b79b2994ece6aa8 (recovery)
  date: 2026-10-25
  quote: "I select Option 1. Preserve the existing published history at `347da95`. Do not amend, rebase, force-push or replace the receipt or its import commit."
applies_to:
  - path: reviews/records/VERIFY-2026-10-25-adr0012-2.md
    revision: dac54f551790674fc974adfbed9dc4bda7f7af9d   # received; blob 150e96c53740d4406a97490caa69cffe0761d568
  - path: reviews/handoffs/2026-10-25-adr0012-verify-2-codex.md
    revision: dac54f551790674fc974adfbed9dc4bda7f7af9d   # received; blob 25fc74a0f5dd150e3d6bbc8683b89d084ebbf123
related: {adrs: [HIO-ADR-0012], tasks: [], findings: [F-REVIEW-2026-10-25-adr0012-2]}
---

# OD-0058: first supervised receipt under harness-0.7.1

## Owner action

Two instructions, verbatim in the history files above: (1) authorise the production receipt of
`VERIFY-2026-10-25-adr0012-2` with Option (b) (pure import; no index change in the import commit; the
F2 index update as a separate administrative commit); (2) after the CI failure, Option 1: preserve the
published history, add no rewrite, complete the F2 index update, record the outcome and defect here,
draft a minimal procedure correction, and push documentation only after checks. The owner also
acknowledged that the import commit lacked the `HIO-Actor` trailer because §6.2 step 5.8 does not list
it, and asked that this be recorded as a **procedure/CI mismatch, not a successful CI result and not
a failed evidence-integrity check**.

## The receipt (live Git state, 2026-10-25)

| Item | Value |
|---|---|
| `main` before | `618059fcb6b85306ed152826a8865b794528cb48` |
| Reviewer branch tip `T` (= Codex's reported tip) | `dac54f551790674fc974adfbed9dc4bda7f7af9d`; parent = reviewed head `d0965ccfd37a0ddefdbb5ff08a11674c3267792a`; 1 commit, no merges |
| Assignment source | `docs/history/2026-10-25-owner-review-disposition-assignments.md` (sha256 `0fd90258c5eb772d9245161db6c0192ef4b738e27545c72a2be11f29af4e2195`), assignment A2 |
| Reviewer inventory | Codex's final-message report relayed by the owner: record sha256 `0ac2ab8ff1ba983f82c23564899cdca6783103ee54e6fce934822996712b617c`, handoff `3285f43a4a50c77cf8d83e703dcb23c0a66ddecc873c16bcac8ee8e030975852`. Reconciled both ways with Git: expected 2, found 2, missing 0, extra 0 |
| Scope and assignment checks | both PASS (assignment check with full SHAs and the expected string from OD-0053) |
| Provenance tag | `reviews/VERIFY-2026-10-25-adr0012-2`, annotated, pushed **before** the import, remote `^{}` = `T` |
| Import commit | `3131e704c8417fd4f5abe0eee404c859b6595b1a`; tree `a4e8dc69d0ab040a6f5ea7f93ada3c201585f93d`, **equal to the rehearsal's tree**; adds only the two reviewer files; no README or administrative content |
| Pre-merge recheck | branch tip, tag peel and `main` unchanged |
| Merge `--no-ff` | `347da95920dd7e71ec2392e0a95a06816dd515a1` (parents `618059f`, `3131e70`), pushed |
| Post-push verification | remote `main` = local merge; `main` blobs = `T` blobs (`150e96c5…`, `25fc74a0…`); remote tag still peels to `T`; branch tip still `T` |

**Evidence receipt: succeeded.** No head, hash, assignment, scope, index or blob-integrity check failed.
The 5.10 completion verifications all passed.

## The defect: procedure and CI disagree

- CI run [`40175402830`](https://github.com/elusivenode/hio/actions/runs/40175402830) on `347da95`
  **failed** at the step "HIO-Actor trailers on new commits": `3131e70: no HIO-Actor trailer`. Every other step passed.
- The rule, read from the repository (not assumed): `.github/workflows/ci.yml` runs
  `tools/check_repo.py trailers <push-before> <sha>`, which requires `^HIO-Actor: \S` in the message of
  **every non-merge commit** in the range (`tools/check_repo.py` `check_trailers`; operating model §8
  metadata hygiene). Merge commits are exempt.
- Harness-0.7.1 §6.2 step 5.8 lists the import-commit trailers (`Review-Id`, `Review-Branch`,
  `Review-Commit`, `Reviewed-Base`, `Reviewed-Head`, `Assignment-Source`, `Reviewer-Report`, `Record`,
  `Inventory`, `Receipt-Checks`) and **omits `HIO-Actor`**, so the procedure as approved cannot produce a CI-passing import commit.
  The earlier receipt (OD-0050) did carry the trailer.
- The local pre-commit hook (`tools/install-hooks.sh`) runs only `public imports valid_time`; it does **not** check
  trailers, so nothing local would have caught it. The rehearsal committed with hooks disabled and
  never ran `check_repo.py trailers`, so it did not show the defect (a rehearsal limitation, see below).
- The failing run is **permanent**. By the owner's choice the published history is preserved: `3131e70`
  and `347da95` are not amended, rebased or replaced, and nothing is force-pushed. The trailer check
  covers only the commits new to each push, so later pushes are not expected to repeat this failure.
  A green later run is **not** a repair of the historical failure and is reported separately.

## Rehearsal limitations (recorded)

1. The rehearsal did not run the CI trailer rule, because hooks were disabled and `check_repo.py trailers` was not run.
2. Failure cases (iii) tip moved, (iv) extra or missing file and (v) a staged F2 transition were demonstrated as logic on
   fabricated inputs, not exercised by a tool. Only the tag cases used real Git operations (on a local stand-in).
3. The assignment check's expected string comes from OD-0053 (the receiver's own text citing the owner file), because the owner file
   holds short SHAs; the check is not independent on that point.
4. The semantic index check (5.6) remains manual.
5. Two rehearsal-script slips (scratch files inside the clone; a duplicate-id test that ignored table boundaries) were found and fixed in
   the rehearsal; neither affected the live receipt.

## Adoption status (harness-0.7.1 first use)

- **Successful evidence receipt** and **complete harness adoption validation** are different things.
  The receipt is complete and verified. The adoption validation is **not passed**: the
  approved procedure, applied exactly, produced a commit the repository's own CI rejects.
- **Routine delegated receipt is NOT enabled** and stays suspended (OD-0056). This record does not declare the
  first use passed.
- A minimal correction is **proposed, not approved**:
  [`harness-0.7.1-trailer-correction-proposal.md`](../harness-0.7.1-trailer-correction-proposal.md). It needs
  the owner's approval and then a bounded test before adoption can be declared.

## Index update (separate administrative commit)

The F2 row of `reviews/README.md` moves from `remediation_claimed` to `verified_closed`, citing
VERIFY-2026-10-25-adr0012-2 at reviewed head `d0965cc`, the owner's adoption of its technical verification
(OD-0054) and this receipt. It is not an owner acceptance or waiver. Only the state cell of the F2 row changed.
F1 and F3 rows, every verdict and every other finding are unchanged. No received-review row for the record
itself was added (not requested).

## What this record does NOT do

- It does not declare the first use passed, enable routine receipt, receive B2, or reopen the ADR-0012 technical review.
- It does not change any approved procedure text, tool or workflow, accepted S1a, any source right, or authorise S1b.
- It does not rewrite, amend or replace any published commit.

## Corrections (append-only)

None.
