---
id: HANDOFF-2026-10-25-s1b1-readiness-package
date: 2026-10-25
actor: claude/implementation-agent (Claude Sonnet 5.5)
work_status: proposed
base_revision: 0665b66b1af4aa51ceda89d9e95451e365b2670d
head_revision: self
work_commits: []
work_card: T-0002
---

# Handoff: s1b1-readiness-package

> A dated snapshot. **Not a decision**, and never authoritative over ADRs, OD records or the
> review index.

## Changed files
- Added `docs/evidence/S1B1-readiness-package.md` (revision 2: reconciled with `origin/main` at `0665b66`, owner direction applied, one authorisation request).
- Added OD-0062 (with its history file and index row) and proposed T-0009 (staging direction, IaC, lean capture, the one staging decision). Package §7 notes the supersession.
- Added this handoff. `STATUS.md` unchanged (state did not change).

## Done
- Rights by dataset × operation for D1–D3, D7–D9, plus a new SIFMA item; timing-evidence analysis
  with a recommendation of no separate probe; Q-013 and manifest recommendations; Tigris vs Azure
  comparison; first slice with 14 acceptance tests; ten consolidated decisions R1–R10.

## Tests and evidence
| Claim | Method | Result |
|---|---|---|
| Repository checks pass | `uv run python tools/check_repo.py` | PASS, 0 problems |
| Provider facts | two web searches | thin; provider rows are marked [EXT] and unconfirmed |

## Known limitations and not verified
- Storage-provider facts (Object Lock, `If-None-Match`, OIDC, immutability on HNS, pricing) are
  unconfirmed. RBA and NY Fed quotations are still fetch-tool extracts (U7).
- No real source was fetched. Nothing was provisioned, no credential created.

## Open findings
- none recorded for this work.

## Assumptions made
- Drafting needs no OD gate; the owner's message is to be transcribed as an OD record.

## Conflicts found between documents
- Revision 1 (drafted at stale `618059f`) said OD-0061 was absent. Wrong: after fetch and fast-forward to `0665b66`, OD-0061, STATUS and harness-0.7.1 + OD-0059 were verified present and left untouched.
- Releases standard §2 enumerates the manifest core "exactly"; resolved by deferral (exploratory releases).

## S1b-1.0 implementation, step 1 (branch `impl/t0009-adapters-and-run-record`)
- Added: `hio.sources` (five dataset specs and parsers, transport protocol, fixture transport only, `run_capture`), `hio.marketdata.runrecord` (capture-run record, written in full per T-0009 §4, hash verified on read), `attempt_record_key` in `contracts/layout.py`, the `sources` import rule in `tools/check_repo.py`, synthetic fixtures under `tests/fixtures/synthetic/s1b1/`, and `tests/test_s1b1_capture.py` (30 tests).
- Not changed: `capture()`, S1a vintages, knowability, jobs, library, publish, storage, rights.
- Evidence: full suite 308 passed (includes the S1a release-hash tests); `ruff check` clean; `check_repo.py` PASS.
- Payload layouts are ASSUMED (fixtures mirror them); the first authorised structure check must confirm. A mismatch fails closed as a failed run.
- No real transport, URL, register entry or network call exists. URLs are unset in the specs by design.
- **Rights finding:** the RBA F1 file carries ASX and FENICS columns, so retaining the file raw retains third-party material (package §6.1). Needs the owner with U1.
- Owner note: the Azure subscription `hnf-dev` is excluded from this work; subscription ids are kept out of the repo (public).

## NOT approved by this session
Nothing. No right verified, no Q-013 decision, no provider chosen, no S1b-1 authorisation, no
standard amended.

## Completion block
- Branch: `docs/s1b1-readiness-package` (from `origin/main` `0665b66`); SHA: see `git log -n1 --format=%H -- <this file>`.
- Pushed: no. Received into `main`: no.
- Next actor: owner, to answer the three confirmations in package §6.2 and approve the §6.1 rights evidence after reading the live clauses.
- Prompt: "Read `docs/evidence/S1B1-readiness-package.md` §6. Decide Authorisation A and the two confirmations; Claude then records OD and drafts T-0009."
