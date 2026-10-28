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

## S1b-1.0 implementation, step 2: exploratory releases and index comparisons
- Added `hio.jobs.s1b1` (ingest under P3, derived US calendar, two cash releases, two index comparisons) and `tests/test_s1b1_releases.py`. Additive changes to S1a code only: `CaptureMode.SCHEDULED_P3`, an optional `parsers` argument on `VintageStore`, `calendar_from_observations`; the `jobs` import rule allows `sources`. The S1a release-hash tests pass unchanged (suite: 321 passed).
- Results on invented data: AUD and USD legs match independent compounding (RA fixture 0.000295890411 holds); the US holiday is derived from published dates only; every vintage is `schedule_only`; `as_known_by_market` returns nothing; rebuild from stored receipts reproduces every release hash; both index comparisons classify `within_expected_bound`; releases are exploratory and say so.
- **Fixed during the work:** the comparison's precision estimate read Decimal exponents, which differ between parsed and reloaded values, so a rebuild changed the release hash. It now counts places in the canonical rendering (a regression test covers rebuild reproduction).
- **FINDING 2 (needs an owner decision): one F1 file, two source ids blocks all AUD publishing.** Identical bytes stored under `rba.cash_rate` and `rba.cash_rate_tri` hit accepted S1a lineage ("receipt attributed to several sources"), and the capture index covers every capture. Building and rebuilding work; writing any AUD release does not (the USD releases publish). Recommendation: one source id for the F1 file serving both series, with D1 and D3 rights recorded together (same file, same terms under U2). ADR-0012 §4.2 lists two ids, so this is a recorded staging decision like OD-0063, not a silent change. The other options change accepted S1a lineage.
- Known limitations: SOFR's documented release instant uses weekdays, so across a US-only holiday it is a day early (labels stay `schedule_only`, never a market claim); the spec patches (gate (d)) are not applied (a spec version bump would change S1a `spec_ref` strings; the S1a data.csv hashes are unaffected, but this needs a deliberate step); the comparison bound uses observed precision as a stand-in for publisher rounding, to be confirmed on real data.

## S1b-1.0 implementation, step 3: shared receipt, cloud-store interface, OpenTofu (branch `impl/t0009-shared-receipt-and-storage`, OD-0065)
- **Shared F1 receipt (owner direction; supersedes my one-source-id recommendation).** `rba.cash_rate` and `rba.cash_rate_tri` keep separate dataset ids and rights. One raw receipt is captured under the publication id `rba.f1`, with a provenance link record naming both datasets and their series. Smallest S1a interface extension: `SeriesDef.dataset_id` (None keeps S1a behaviour), a link-aware lineage attribution (a receipt with no link resolves exactly as before), a `staged_writes()` factory. Capturing the file needs every dataset it serves; each release is authorised on the datasets it uses (the AUD cash leg does not need the TRI right; its TRI comparison does). No approved observation or rights invariant is weakened: a shared receipt without its link, or with a wrong one, fails closed.
- **Cloud-store interface.** `BlobBackend` has no overwrite and no delete; `BlobObjectStore` and an in-memory `FakeBlobBackend` (no network). Ordered, resumable commits (bytes, manifest, links, capture records, processing outcomes, run record last). Tested byte-equivalent to the local store through the whole pipeline.
- **OpenTofu (HIO-only, never applied).** `infra/tofu/`: flat-namespace account, versioning, account-level immutability (Unlocked), no shared keys, create-only writer role (`add/action`, no `write`/delete), GitHub OIDC federation, owner read-only. `tofu fmt -check` passes; no `init`/`validate`/`plan` run. Unconfirmed provider attributes are listed in `infra/tofu/README.md`.
- **Documentation check (read 2026-10-25, Microsoft Learn and provider source).** Confirmed: version-level immutability needs versioning and is not supported with a hierarchical namespace; a locked policy cannot be removed; Put Blob supports `If-None-Match: *` (412 when it exists); `add/action` creates, `write` overwrites. Not confirmed: the azurerm container and role-definition attribute names for the installed provider, the GitHub issuer and subject strings (not re-read), per-container immutability in the provider.
- **Tests (`uv run pytest`, 348 passed):** shared-receipt attribution, cross-dataset rights, denied publication, replay from receipts and links alone, fail-closed provenance, Decimal canonicalisation, storage equivalence, immutability, overwrite detection, failed-commit resume, infrastructure controls. The S1a release-hash tests pass unchanged.
- **Known limitations:** payload layouts are assumed; the SOFR P3 release instant uses weekdays; spec patches (ADR gate (d)) are not applied; a crash after every write except the run record is resumed by a run that reports "unchanged" (the missing completion record is the trace).

## NOT approved by this session
Nothing. No right verified, no Q-013 decision, no provider chosen, no S1b-1 authorisation, no
standard amended.

## Completion block
- Branch: `docs/s1b1-readiness-package` (from `origin/main` `0665b66`); SHA: see `git log -n1 --format=%H -- <this file>`.
- Pushed: no. Received into `main`: no.
- Next actor: owner, to answer the three confirmations in package §6.2 and approve the §6.1 rights evidence after reading the live clauses.
- Prompt: "Read `docs/evidence/S1B1-readiness-package.md` §6. Decide Authorisation A and the two confirmations; Claude then records OD and drafts T-0009."
