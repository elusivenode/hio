---
id: HIO-HARNESS-0.7.1-TRAILER-CORRECTION
title: "Proposed correction to harness-0.7.1 §6.2 step 5: require the HIO-Actor trailer on receipt commits and check it before merge"
status: proposed   # NO EFFECT until the owner approves an exact revision. harness-0.7.1 (OD-0056, commit 552d4fb, blob a74a41453d10) stays in force
owner: owner (decides); drafted by claude/implementation-agent
created_at: 2026-10-25
drafted_under: [OD-0058]
revision: 1
amends: docs/harness/operating-model.md §6.2 step 5.7 and 5.8 only
---

# Proposed correction: HIO-Actor trailer on receipt commits

> **Proposal only.** The approved operating model is not edited. If the owner approves an exact
> revision, the text in §3 is applied to §6.2 steps 5.7 and 5.8 with a changelog line, as a
> status-and-content change recorded by its own OD.

## 1. Evidence, read from the repository

| Fact | Where |
|---|---|
| CI fails any **non-merge** commit in a push range whose message lacks `^HIO-Actor: \S` | `tools/check_repo.py` `check_trailers` (`git rev-list --no-merges <base>..<head>`); `.github/workflows/ci.yml`, step "HIO-Actor trailers on new commits" (base = `github.event.before` on a push) |
| Merge commits are exempt | `--no-merges` in the same function |
| The local pre-commit hook does **not** check trailers | `tools/install-hooks.sh` runs `check_repo.py public imports valid_time` only |
| Operating model states the rule as metadata hygiene | §8 (an `HIO-Actor` trailer on every commit; "not proof") and the §363 self-declaration row |
| §6.2 step 5.8 omits it | it lists `Review-Id`, `Review-Branch`, `Review-Commit`, `Reviewed-Base`, `Reviewed-Head`, `Assignment-Source`, `Reviewer-Report`, `Record`, `Inventory`, `Receipt-Checks` |
| Result | the first receipt's import commit `3131e70` failed CI run `40175402830` (OD-0058); the evidence was received correctly |

## 2. What this does not change

No tool, workflow, hook or CI rule changes; the existing CI rule is applied as written. No other
step of §6.2 changes. The trailer is metadata, not authentication (§8).

## 3. Proposed text

**Step 5.8**, add to the trailer list:

> - `HIO-Actor: <role> (evidence receipt, OD-NNNN)`, as CI requires on every non-merge commit
>   (`tools/check_repo.py trailers`); and `Co-Authored-By` when the receiver is an agent.

and after the sentence "Keep it pure: no status cell, `STATUS.md` or OD change in this commit.", add:

> The merge commit of 5.9 and any administrative commit that follows carry the same `HIO-Actor`
> trailer by the same rule (merge commits are exempt in CI, but carry it for consistency).

**Step 5.7**, add as a final check, run on the import commit before the recheck in 5.9:

> `uv run python tools/check_repo.py trailers origin/main HEAD` passes. (The local hook does not
> check trailers; CI does. Stop and fix the **unpublished** import commit if it fails.)

## 4. Bounded test before adoption (proposed)

1. In a scratch clone, build an import commit for an already-received, byte-identical record **without**
   publishing: show `check_repo.py trailers origin/main HEAD` **fails** on a commit lacking the trailer
   and **passes** on one carrying it.
2. The next real receipt (B2, when the owner assigns it) applies the corrected text in full, and the
   resulting push's CI trailer step is reported separately from any earlier failure.
3. The owner then decides in an OD whether the first-use validation (OD-0056 condition) is passed.

## 5. Open question for the owner

Whether CI status on the pushed merge should become a reported (non-gating) item in 5.10. The
trailer check is hygiene; making it a completion gate would be a broader change and is not proposed here.
