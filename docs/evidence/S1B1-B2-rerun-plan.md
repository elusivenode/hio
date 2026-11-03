---
id: HIO-EVIDENCE-S1B1-B2-RERUN-PLAN
title: "Authorisation B stage B-2, re-run: instrumented C5 probe and step 7b on the held probe account (proposed)"
status: proposed            # a plan for owner "go"s; authorises nothing
owner: HIO architecture lead (owner); prepared by claude/implementation-agent
created_at: 2026-10-29
base_revision: a71f0ff
instruction: OD-0134 item 5 (T-0015 F-3)
---

# B-2 re-run plan

> **Proposed.** Each write step needs the owner's "go". It builds on `docs/evidence/S1B1-B2-probe-plan.md` (the first
> run) and `docs/evidence/b2/README.md` (its result).

## Why a re-run

The first run (GitHub run `40853094503`) failed C5 50 times out of 50, and the conditional create returned 403
instead of 409. The architect (consultation `20261029T202344-ask-4dcb`) found that the probe measured `completed_at`
after the write and a metadata read, whereas HIO-ADR-0012 defines it as the moment the publisher body is fully read,
**before** the attempt record is written. The re-run measures what C5 actually needs, under T-0015's instrumentation,
so that the owner can decide a C5 amendment on evidence.

## Preconditions

1. T-0015 F-1 and F-2 are merged into `main`. A dispatch runs the default branch, so the instrumented probe must be
   there.
2. The probe account `hioprobehoue` still exists (held under OD-0134 item 6), and its three Environment variables are
   still set.
3. `~/.hio-state/` is backed up (owner).

## Steps

| Step | Action | Kind |
|---|---|---|
| R-1 | `gh workflow run storage-probe.yml --ref main -f repeats=50`; the owner approves the `capture` deployment in GitHub | **dispatch, on "go"** |
| R-2 | Download the report; retain it verbatim in `docs/evidence/b2/` beside the first run, with its sha256 | records PR |
| R-3 | Read the result (table below); put the C5 decision to the owner | none |
| 7b-1 | The owner, with their own `az` login, grants themselves `Storage Blob Data Contributor` on container `probe` (scope: that container only) | **Azure write, on "go"** |
| 7b-2 | On one probe key from R-1: list its versions; try to **delete the retained version** (`--version-id`), expecting refusal under the one-day policy; then upload different bytes to the same key, which may succeed by creating a new current version. Re-list the versions and download the retained version to confirm it is byte-identical and still present | **Azure writes, on "go"** |
| 7b-3 | Remove the role assignment from 7b-1; read back that it is gone | **Azure write, on "go"** |
| D-1 | **At least 24 hours after the last write** (R-1 or 7b-2), `tofu plan -destroy` (shown), then destroy on "go"; remove the three probe Environment variables; read back that `rg-hio-probe` is gone | **Azure and GitHub writes, on "go"** |

## Reading the result

| Observation | Meaning | Next |
|---|---|---|
| The candidate `floor_s(completed_at) ≤ s ≤ completed_at + δ` holds in all 50; the `Date` brackets show a small offset | whole-second flooring explains the first run | the owner decides the C5 amendment at that form, with the measured distribution as evidence |
| The candidate fails for some, and the `Date` brackets show a clock offset beyond 1 s | storage-clock or runner-clock skew | a declared `ε_storage` is needed; the owner decides a bound, kept separate from C4's ε |
| Writes take seconds (long monotonic durations) | latency, not skew | revisit δ and the write path before deciding |
| The conditional create now gives `BlobExists` (F-1) | the backend mapping works against Azure | none |
| 7b: deleting the retained version is refused and its bytes are intact | version-level immutability protects retained versions against a privileged actor | record it; the write-once claim then rests on RBAC plus immutability |
| 7b: deleting the retained version succeeds | immutability does not protect as assumed | **stop**: storage design review before B-3 |

## Cost and risk

Cents. 7b grants the owner a data-plane role on the probe container only; it is removed in 7b-3. The evidence account
is never touched.

## What the "go"s would say

R-1: "go, dispatch the re-run." 7b: "go, run 7b." D-1: "go, destroy."

## Not approved by this document

No dispatch, Azure write, role grant, destroy or C5 change is authorised by it.
