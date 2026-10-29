---
id: HIO-INFRA-TOFU-PROBE
title: HIO B-2 storage probe OpenTofu definitions (short-lived; authored, never applied)
status: proposed
owner: HIO architecture lead (owner); drafted by claude/implementation-agent
---

# HIO B-2 storage probe: OpenTofu definitions (short-lived)

**Status: definitions only.** Authored under T-0012 P-1 (OD-0127). Nothing here has been planned or
applied. This is a **separate root module** from `infra/tofu/` and shares no resource, state or
identity with the evidence store.

## Purpose

The B-2 probe tests write-once behaviour and C5 timing against real Azure Blob Storage (HIO-ADR-0012
section 4.3.3). The evidence account's 3,650-day immutability would retain probe objects for a decade,
so the probe has its own account with a **one-day** immutability period, destroyed afterwards.

## Lifecycle

- **Short-lived.** It exists only for B-2.
- **Apply and destroy only under Authorisation B stage B-2**, each a separate explicit owner action
  with a plan. Neither is part of T-0012's build authority.
- **State is local and outside the repository**, in `~/.hio-state/probe.tfstate`, passed with
  `-state=...` on every command. There is no `backend` block. `tools/check_repo.py` refuses state,
  plan and variable files in git.
- **Objects become deletable one day after creation** (account default policy, Unlocked, one day).
  Soft-delete retention is deliberately not enabled, so nothing outlives the period.
- **Destroy afterwards**, once the policy period has passed for every probe object. Destroying earlier
  fails because the objects are still immutable.

## Resources

All HIO-only, in `rg-hio-probe`: a `StorageV2` account (ZRS, flat namespace, shared key off,
`default_to_oauth_authentication`, no public nested items, TLS 1.2, https only, versioning on, network
default `Allow`), one private container `probe`, the user-assigned identity `id-hio-probe` with a
federated credential, a custom role `HIO probe writer (create-only)` (data actions `blobs/read` and
`blobs/add/action` only, assignable scope the probe account) and its assignment on the probe container
only.

## Inputs (variables with no default, supplied at apply time, never committed)

`subscription_id`, `storage_account_name`, `github_oidc_subject` (GitHub's immutable subject format
with the numeric ids, read from GitHub). `location` defaults to `australiaeast`.

## Outputs

Account name, container name and identity client id. No secret.

## Checks

`tests/test_t0012_infra.py` reads the files as text and runs `tofu fmt -check` if OpenTofu is
installed. `tofu init -backend=false` and `tofu validate` are run by the orchestrator. The identity
requires the same unconfirmed provider arguments listed in `infra/tofu/README.md` ("Not confirmed").
