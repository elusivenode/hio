---
id: HIO-EVIDENCE-S1B1-B2-PLAN
title: "Authorisation B stage B-2: storage probe execution plan (proposed)"
status: proposed            # a plan for an owner decision; authorises nothing
owner: HIO architecture lead (owner); prepared by claude/implementation-agent
created_at: 2026-10-29
base_revision: 01120e9
instruction: OD-0130 item 3 ("draft the plan at efb6fa1; no apply or dispatch")
---

# B-2 storage probe: execution plan

> **Proposed.** Nothing here is authorised until the owner's B-2 yes, which names this plan's revision. No Azure,
> GitHub or OpenTofu write has been made in preparing it.

## What B-2 answers

From the Authorisation B package (stage B-2) and H4 S-6 (OD-0119): against real Azure, using accepted T-0012
(`efb6fa1`, on `main` as `01edfe9`), does the store behave as HIO's write-once design and HIO-ADR-0012 §4.3.3 C5 assume?
Six checks (`tools/storage_probe.py`): create; conditional create of the same key refused; overwrite refused; delete
refused; one version per key; and C5 timing, `completed_at ≤ s ≤ completed_at + δ` (δ = 600 s) over N fresh creates, no
tolerance. The open question is whether Azure's whole-second `Last-Modified` breaks the lower bound.

## Preconditions

| # | Precondition | State now |
|---|---|---|
| 1 | T-0012 on `main` | done (`01edfe9`, OD-0128) |
| 2 | Providers registered in `hnf-prod` | done (B-1, OD-0125 correction 2) |
| 3 | `~/.hio-state/` backed up | **owner, outstanding**. The probe adds `probe.tfstate` there |
| 4 | Owner's `az` login on `hnf-prod`; OpenTofu 1.12.5 | at execution |
| 5 | The soak alert is disabled (`alert_enabled = false`) | true (OD-0126); B-2 does not touch the evidence store |

## Values (supplied at the prompt or in `~/.hio-state/probe.tfvars`; never committed)

| Variable | Proposed value |
|---|---|
| `subscription_id` | `hnf-prod`'s id, read by the owner's `az account show` |
| `storage_account_name` | `hioprobe` plus four random lowercase characters, chosen at plan time (globally unique) |
| `github_oidc_subject` | the immutable subject for Environment `capture`, built from `gh api repos/elusivenode/hio` (`owner.id`, `id`; read-only) |
| `location` | default `australiaeast` (same as the evidence account) |

## Steps

Each write step happens only after the owner's "go" on what is shown. `--subscription hnf-prod` is named on every `az`
command. All commands run in the owner's terminal session, at `main` at the B-2 revision.

| Step | Action | Kind | Shown to the owner |
|---|---|---|---|
| 1 | `tofu -chdir=infra/tofu/probe init` (no backend; local state) | local | output |
| 2 | `tofu -chdir=infra/tofu/probe plan -state=$HOME/.hio-state/probe.tfstate -var-file=$HOME/.hio-state/probe.tfvars -out=$HOME/.hio-state/probe.tfplan` | read | **the plan: expected 7 to add, 0 to change, 0 to destroy** (resource group, account, container, identity, federated credential, role definition, role assignment) |
| 3 | `tofu apply` of that saved plan | **Azure write, on "go"** | apply output |
| 4 | Read-back with `az`: immutability policy (1 day, Unlocked), versioning on, shared key off, public access off, ZRS, the role's data actions, the assignment's scope | read | a summary table |
| 5 | Set three `capture` Environment variables: `HIO_PROBE_ACCOUNT_URL`, `HIO_PROBE_CONTAINER`, `AZURE_PROBE_CLIENT_ID` (`AZURE_TENANT_ID` is already set) | **GitHub write, on "go"** | the names and non-secret values |
| 6 | `gh workflow run storage-probe.yml -f repeats=50`; the `capture` Environment's required reviewer (the owner) approves the job | **dispatch, on "go"; owner approves in GitHub** | the run URL; Claude watches it |
| 7 | Download the `storage-probe-report` artifact; record its sha256; commit the JSON report under `docs/evidence/b2/` with the run URL and id | read, then a records PR | the report summary (section below) |
| 8 | **At least 24 hours after the last probe object was created:** `tofu plan -destroy` (shown), then destroy on "go"; remove the three Environment variables; keep `probe.tfstate` and the plan/apply text in `~/.hio-state/` | **Azure and GitHub writes, on "go"** | the destroy plan; read-back that `rg-hio-probe` is gone |

**Optional step 7b (owner's choice; needs its own "go"):** test immutability against a *privileged* actor, which the
probe does not test. The writer's overwrite and delete refusals come from its create-only role, so they prove RBAC, not
immutability. In 7b the owner grants themselves `Storage Blob Data Contributor` on the probe container. They then try
`az storage blob delete` and an overwrite of one probe blob, which should be refused by the one-day policy, and remove
the grant afterwards. This answers the architect's point (OD-0117 consultation) that version-level WORM protects
versions, and that an overwrite may create a new current version rather than fail.

**Why 50 repeats, in one run:** the creates are independent and quick, and the precision question needs enough samples
to show where `Last-Modified` falls within its second. A second run would only add sub-second samples of the same
mechanism, and its objects would push the destroy back another day.

## Reading the result

| Observation | Meaning | Next |
|---|---|---|
| All six checks pass, 0 C5 violations in 50 | C5 holds as written for this sample (`min_diff_ms` ≥ 0) | record; B-3 can proceed on the design as is |
| C5 violations, all with `diff_ms` in (−1000, 0], and no other failure | whole-second truncation confirmed: `s` is floored below `completed_at` | **an owner decision on C5** (an ADR-0012 amendment): for example, compare at whole-second precision (`floor(completed_at) ≤ s`), with the measured distribution as evidence. B-3 waits for it |
| C5 violations with `diff_ms` ≤ −1000 or > 600 000 | clock skew or a timestamp that is not the write time | stop; investigate before any C5 change |
| Duplicate create, overwrite or delete **not** refused | the write-once assumption fails for the writer | **stop**: B-3 blocked; storage design review |
| More than one version for a key | versioning behaves differently from the backend's assumption | stop; review `AzureBlobBackend` version handling |
| Errors (auth, network) | the probe did not measure | fix and re-dispatch (same plan; objects so far still count) |

A result is never rounded or reinterpreted. The JSON report keeps every observation (`tolerance: "none"`).

## Retained evidence

The committed JSON report (keys, `completed_at`, `s`, `diff_ms`, check results; it holds no identifier other than the
probe account's host name), the run URL and id, the plan/apply/destroy text and state in `~/.hio-state/` (not
committed), and the read-back summaries in the B-2 OD record. The workflow artifact itself expires after 30 days, so
the committed copy is the record.

## Cost and risk

Cost: cents (one small ZRS account for about two days, a few hundred transactions). Risks: the destroy fails if run
inside the one-day period (it is retried later); a mistyped subject makes the probe's login fail (fix the variable and
re-apply; nothing is written). The evidence account, its identity and its state are not touched.

## What the B-2 yes would say

"Create the probe account and run the S-6 probe per `docs/evidence/S1B1-B2-probe-plan.md` at `<revision>` (steps 1–8,
[with / without] 7b); destroy it afterwards."

## Not approved by this document

Everything above is proposed. No Azure write, GitHub change, dispatch or C5 change is authorised by it.
