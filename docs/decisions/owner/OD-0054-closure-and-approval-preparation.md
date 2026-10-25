---
id: OD-0054
title: "Owner adoption of the technical verification of VERIFY-2026-10-25-adr0012-2 (dac54f5) and VERIFY-2026-10-25-harness-0.7.1-1 (4682c98); all seven findings recorded technically verified closed; closure and approval package prepared; nothing approved"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-closure-approval-preparation.md (pasted by the owner, verbatim)
  sha256: 7bcd9eadbbc96a6bb47aa5ec81ddb2acdb1e34c4c84df08bf12b5f0a63df06fb
  date: 2026-10-25
  quote: "I adopt their independent technical verification conclusions, subject to your verification of the exact Git evidence and assignments."
applies_to:
  - path: reviews/records/VERIFY-2026-10-25-adr0012-2.md
    revision: dac54f551790674fc974adfbed9dc4bda7f7af9d   # not merged, not received
  - path: reviews/records/VERIFY-2026-10-25-harness-0.7.1-1.md
    revision: 4682c981180cc25b7c3b1dfc3e39e22901de1ac3   # not merged, not received
related: {adrs: [HIO-ADR-0012, HIO-ADR-0010, HIO-ADR-0008], tasks: [T-0005], findings: [F-REVIEW-2026-10-25-adr0012-1, F-REVIEW-2026-10-25-adr0012-2, F-REVIEW-2026-10-25-adr0012-3, F-REVIEW-2026-10-25-harness-0.7.1-1, F-REVIEW-2026-10-25-harness-0.7.1-2, F-REVIEW-2026-10-25-harness-0.7.1-3, F-REVIEW-2026-10-25-harness-0.7.1-4]}
---

# OD-0054: closure of seven findings; approval preparation

> **Nothing is approved by this record.** HIO-ADR-0012 and harness-0.7.1 stay proposed. The four
> Codex records named below are **not merged and not received**.

## Owner action (the verbatim text is in the history file)

1. Adopt Codex's independent technical verification conclusions (both **READY WITH CONDITIONS**),
   subject to the receiver's verification of the exact Git evidence and the assignments.
2. Resolve every commit and sha256 from Git; preserve the immutable records and the independent
   reviewer inventories.
3. Prepare an explicit owner disposition of the still-unreceived historical reviews, with the
   OD-0053 evidence limitations. **Do not manufacture missing assignment or identity evidence.**
4. Record the three ADR-0012 findings and the four harness-0.7.1 findings as **technically
   verified closed** at their reviewed heads, **preserving the conditional qualifications**.
5. Prepare harness-0.7.1 revision 3 for exact-revision approval (the exact operating-model changes
   and the first-use validation), and ADR-0012's approval decision **separately**, confirming the
   independent gates.
6. Explain the safe integration sequence without merging unapproved ancestry through reviewer
   branches.

**Prohibited:** further reviewer PRs or technical reviews without new material evidence; approving
either proposal; changing source-rights states; altering accepted S1a; authorising S1b.

## Evidence resolved from Git (fresh fetch, 2026-10-25)

| | VERIFY-2026-10-25-adr0012-2 (A2) | VERIFY-2026-10-25-harness-0.7.1-1 (B2) |
|---|---|---|
| Branch (tip = the commit below) | `review/adr0012-verify-2-codex` | `review/harness-0.7.1-verify-1-codex` |
| Reviewer commit (owner prefix) | `dac54f551790674fc974adfbed9dc4bda7f7af9d` (`dac54f5`) | `4682c981180cc25b7c3b1dfc3e39e22901de1ac3` (`4682c98`) |
| Parent = assigned reviewed head | `d0965ccfd37a0ddefdbb5ff08a11674c3267792a` (tip of PR #4's branch) | `8ed13fdef8537b846afb7e60b14807417b2f3c0d` (tip of the harness branch) |
| Commits in range; merges | 1; 0 | 1; 0 |
| Files | `A` record, `A` handoff. **No index change** | `A` record, `A` handoff. **No index change** |
| Record | `reviews/records/VERIFY-2026-10-25-adr0012-2.md`: blob `150e96c53740d4406a97490caa69cffe0761d568`, sha256 `0ac2ab8ff1ba983f82c23564899cdca6783103ee54e6fce934822996712b617c`, 5838 bytes | `reviews/records/VERIFY-2026-10-25-harness-0.7.1-1.md`: blob `476e2bd8a58241cad8269704e44ffe95213ced62`, sha256 `735cd06a7a1618ea5663528d055cc4fb2c39398fdfe83f4659f408f77cd83e17`, 7155 bytes |
| Handoff | blob `25fc74a0f5dd150e3d6bbc8683b89d084ebbf123`, sha256 `3285f43a4a50c77cf8d83e703dcb23c0a66ddecc873c16bcac8ee8e030975852` | blob `4c48433a3af0749dca406a8f7169c3dc5ecf2a42`, sha256 `322dba072b250d53d67e8a15d5fd1735dae02a56c3795fedc14a89cfcedb00bd` |
| `tools/check_review_branch.sh` (from `main`) | PASS | PASS |
| `tools/check_review_assignment.py` | PASS: id, base `6fbec1a…`, head, branch and assignment string equal the **expected values taken from the owner-authored source, not from the record** | PASS (same basis) |
| Verdict | **READY WITH CONDITIONS** | **READY WITH CONDITIONS** |

**The owner-authored assignment source now exists and was verified.** Each record's `assignment`
field cites `docs/history/2026-10-25-owner-review-disposition-assignments.md` at commit
`db4cc82cf04a87a74e678c8b778db190a87305cc`. That file's sha256 is
`0fd90258c5eb772d9245161db6c0192ef4b738e27545c72a2be11f29af4e2195`, equal to the owner statement in
OD-0053. The expected strings were read from OD-0053 (my text citing that file), so this check is
**not circular** (unlike OD-0052). The scope-term checks were lexical: "forged", "stale" and
"inventory" are not literal words in the records, and the owner's scope items were mapped to the
records by hand instead (every item has a corresponding case or section). Two checker failures on
the way were my own usage errors (the tool wants the exact branch name), not discrepancies.

**No discrepancy was found.** The live tips were unchanged from the previous verification.

### Independent reviewer inventory: what is held

- **Supplied by the owner** (an independent source): each reviewer's branch name, **commit prefix**
  and verdict.
- **Computed from Git:** the full commits, blobs, sha256 values and the file lists above.
- **Not supplied: Codex's completion reports with the sha256 of each added file.** The inventory
  is therefore partly independent (the prefix and the verdict) and partly Git-derived. This stays
  an **explicit limitation**; it is not filled by the records' own handoffs, which are in the same
  commit as the records.

## Findings recorded as technically verified closed

By the owner's adoption (item 1), at the reviewed heads, **preserving the conditions**. This is
technical verification by Codex. It is **not** an owner acceptance of the work, a waiver, or an
approval.

| Finding | Severity | Closing record | At head | Conditional qualifications |
|---|---|---|---|---|
| F-REVIEW-2026-10-25-adr0012-1 | high | VERIFY-2026-10-25-adr0012-1 (`e1f60f9`; sha256 `4692c99f…d048`) | `860fd78` | closed **as a proposed design correction**. P2 (capture-time basis for a first capture) is held at **Q-013** and the S1b-1 gate; the verification does not validate or implement P2. Publisher timing semantics remain an S1b gate |
| F-REVIEW-2026-10-25-adr0012-2 | high | VERIFY-2026-10-25-adr0012-2 (`dac54f5`; sha256 `0ac2ab8f…617c`) | `d0965cc` | closed **as a proposed design correction**. The trusted-adapter limit is stated, not removed: a compromised adapter can still lie, and an authentication system would change the trust model and is outside the finding. **Q-013**, the **release-manifest schema** disposition, dataset-specific **`Date`/`Age`/provider write-time evidence**, and later S1b implementation evidence are separate prerequisites |
| F-REVIEW-2026-10-25-adr0012-3 | medium | VERIFY-2026-10-25-adr0012-1 (`e1f60f9`) | `860fd78` | closed as a proposed design correction; publisher timing remains a later S1b gate |
| F-REVIEW-2026-10-25-harness-0.7.1-1 | high | VERIFY-2026-10-25-harness-0.7.1-1 (`4682c98`; sha256 `735cd06a…3e17`) | `8ed13fd` | closed **as a procedure correction**. It does not authenticate Git users or cure earlier evidence limitations; the accountability limit is stated |
| F-REVIEW-2026-10-25-harness-0.7.1-2 | medium | same | `8ed13fd` | closed as a procedure correction. **The semantic check (5.6) is manual** until separately authorised tooling exists |
| F-REVIEW-2026-10-25-harness-0.7.1-3 | medium | same | `8ed13fd` | closed for the stated moving-ref control. A race after the final check cannot be eliminated by a text procedure; the files and tag stay pinned |
| F-REVIEW-2026-10-25-harness-0.7.1-4 | medium | same | `8ed13fd` | closed for tag ordering and partial-receipt recovery |

**Index state.** The finding rows in `reviews/README.md` are **not** changed by this record. Neither
new Codex commit edited the index, and the closure rows belong to a receipt (Class S in the
revision-3 procedure), validated against the imported record. Until a receipt, the records and this
OD are the authority (the records win over the index).

## Owner disposition of the unreceived reviews: prepared, not adopted

Four Codex records are on pushed branches and **none is received**. Their inputs differ.

| Record (reviewer commit) | Owner-authored assignment source | Reviewer report with file hashes | Receipt under revision 3 |
|---|---|---|---|
| VERIFY-2026-10-25-adr0012-1 (`e1f60f9`) | **absent** (OD-0053 limitation) | **absent** | stops at 5.0; also its index diff does not apply to `main` (below) |
| REVIEW-2026-10-25-harness-0.7.1 (`9c51a6b`) | **absent** (OD-0053 limitation) | **absent** | stops at 5.0 |
| VERIFY-2026-10-25-adr0012-2 (`dac54f5`) | **present** (history file at `db4cc82`) | **partial** (owner prefix and verdict; hashes absent) | can proceed once the owner relays the report or records that the prefix and computed hashes suffice |
| VERIFY-2026-10-25-harness-0.7.1-1 (`4682c98`) | **present** | **partial** | as above |

**Proposed disposition D0** (for the owner to adopt, amend or refuse; nothing is manufactured):

1. **Pin all four reviewer commits** with annotated provenance tags `reviews/<id>`, with **no
   import**. This preserves them if a branch is deleted and creates no claim of receipt.
2. **A2 and B2** are received under the approved harness-0.7.1, as its **first use** (supervised;
   see the approval package), once the owner relays Codex's completion reports or states that the
   owner-supplied prefixes plus the computed hashes suffice for these two.
3. **The two historical records** (`e1f60f9`, `9c51a6b`) either stay **"disposed, unreceived"** on
   their tags, or the owner authorises a **one-off, disposition-bound import** whose trailers say
   `Assignment-Source: absent (owner disposition)` and `Reviewer-Report: absent`, and whose OD
   restates the OD-0053 limitations. It does not reconstruct either input. **Recommended:** the
   one-off import, because the harness findings' index rows are defined by `9c51a6b` and the closure
   of ADR F1 and F3 rests on `e1f60f9`, so without them the index cannot show the chain.
4. **Not retrospectively approved:** the push-only delivery of the first two reviews, or the
   OD-0052 reading of §6.2 step 6.

**A first-use stop to expect.** Codex's index diff for `e1f60f9` was built on PR #4's `README`. A
test shows it **does not apply** to `main` (`6fbec1a`) or to PR #4's head (`d0965cc`); it applies
only to its own base `860fd78`. The `9c51a6b` diff applies cleanly to `main`. So receipt of
`e1f60f9` will stop at step 5.5 by design, and its closure rows must be derived by the receiver as
Class S rewrites validated against the record, with the owner's go-ahead. The F2 row's final state
comes from `dac54f5` (closed at `d0965cc`), not from `e1f60f9` (open at `860fd78`).

## The decisions and the safe sequence

See [`approval-package-adr0012-harness-0.7.1.md`](../approval-package-adr0012-harness-0.7.1.md): two
short approval decisions, the exact operating-model changes, the first-use validation, the
independent gates, and the integration sequence.

## What this record does NOT do

- It does **not** approve ADR-0012 or harness-0.7.1, receive or merge any record, create a tag,
  waive a finding, change a source-right state, alter accepted S1a, or authorise S1b.
- It does **not** decide Q-013, the release-manifest schema, header semantics, or the disposition
  D0 above.
- It does **not** contact Codex or open a reviewer PR.

## Corrections (append-only)

None.
