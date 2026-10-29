---
id: HIO-EVIDENCE-S1B1-H3-H4
title: "S1b-1 decision pack: H3 (network and credential controls, the OD-0038 successor) and H4 (storage settings and provider validation)"
status: proposed            # a request for owner decisions; authorises nothing
owner: HIO architecture lead (owner); prepared by claude/implementation-agent
created_at: 2026-10-29
base_revision: 4bce6ae
instruction: OD-0118 decision 1 ("draft the H3 and H4 decision packs")
governs: [HIO-ADR-0012 rev 3 (approved), T-0009 §8, T-0010, T-0011]
---

# S1b-1 decision pack: H3 and H4

Each item is one yes/no. A yes records the setting; **none of them provisions anything**. Provisioning and the first
live capture remain Authorisation B, which should name the apply steps. Sources: readiness package §5.3 (controls),
T-0011 (assessment of `hnf-prod` and GitHub, 2026-10-29), architect consultations `20261029T120200-ask-1eee` and
`20261029T121425-ask-c603`.

## H3: network and credential controls

| # | Control | Recommendation | A yes records |
|---|---|---|---|
| C-1 | **Capture workflow** | a separate workflow; triggers `schedule` and `workflow_dispatch` only; actions pinned by commit SHA; permissions `contents: read`, `id-token: write`; runs in the `capture` Environment | this workflow shape (T-0010 W-3) |
| C-2 | **Network use** | only `src/hio/sources/http_transport.py` (data sources) and `src/hio/storage/azure_auth.py`/`azure_blob.py` (GitHub OIDC, Azure) may import a network client or the Azure SDK, enforced by `check_repo`. **No runner egress firewall** on GitHub-hosted runners: a static architectural guard, not containment | the guard, and **no egress firewall as an accepted residual** (the S1b successor to Q-008) |
| C-3 | **Writer identity** | a user-assigned managed identity; federated credential with GitHub's **immutable subject** for Environment `capture` (supplied at apply, never committed); a create-only custom role (`blobs/read`, `blobs/add/action`) on the evidence container only; no static key anywhere (shared key off) | this identity design |
| C-4 | **`capture` Environment rules** | **Remove the required-reviewer rule before go-live** and keep the `main`-only branch policy. A required reviewer pauses *every* job in the Environment, scheduled ones included, so daily capture would wait for your approval each run. Manual dispatch is already limited to people with write access | removing the reviewer rule at go-live (a GitHub change under this yes) |
| C-5 | **Reader identity** | your own user, `Storage Blob Data Reader` on the evidence container; no other reader | this assignment |
| C-6 | **Who runs OpenTofu** | you, locally, with `az login` scoped to `hnf-prod` (`--subscription` named on every command; your `az` default is `hnf-dev`); no CI apply; plans reviewed before apply | owner-run apply; no CI credentials for IaC |
| C-7 | **State** | a separate state account (T-0011 I-2); the bootstrap's own local state kept outside the repository on your machine, with a copy you hold | this state arrangement |
| C-8 | **Configuration values** | tenant, client and subscription ids as GitHub Environment *variables* on `capture` (not committed, not secrets: they are identifiers, not credentials) | this placement |
| C-9 | **Supply chain** | `uv.lock` with hashes (Azure SDK and dependencies), `.terraform.lock.hcl` with provider hashes, CI installs locked only | this baseline |
| C-10 | **`main` protection** | done (OD-0118): PRs only, `harness` and `tests` required, no force-push or deletion, admins included | — (recorded) |

## H4: storage

| # | Setting | Recommendation | Note |
|---|---|---|---|
| S-1 | **Placement** | Azure Blob Storage, `australiaeast`, `hnf-prod`, resource group `rg-hio-evidence` (HIO-only) | `hnf-prod` is empty (T-0011) |
| S-2 | **Replication** | **ZRS** (three zones, one region) | GZRS adds a paired region at about twice the storage cost; the off-provider copy (S-7) covers the region risk better |
| S-3 | **Immutability** | account-level version-level WORM, **Unlocked**, 3,650 days; decide on locking after the soak | a Locked policy cannot be removed; its period only grows |
| S-4 | **Network** | default action **Allow**, with Entra-only auth and no shared key | GitHub-hosted runner addresses are not stable; Deny needs a self-hosted runner or private networking |
| S-5 | **Soft delete** | blob and container, 30 days | already in the definitions |
| S-6 | **Provider validation (needed before C5 can be relied on)** | after the evidence store exists, a synthetic probe from the `capture` workflow: create, conditional-create conflict, overwrite and delete denied for the writer, version listing, and `Last-Modified` against `completed_at` over repeated runs | the architect's point: Azure's timestamps are **whole seconds**, so C5's `completed_at ≤ s` can fail within the same second. Any tolerance is a separate decision on ADR-0012 C5 |
| S-7 | **Second copy (T-0011 I-8)** | defer the destination decision to within the first month of capture | adds `external_processing` for a new host |
| S-8 | **Budget** | 20 a month (billing currency) on the HIO resource group, alerts at 80% and 100% | expected cost is a few dollars |
| S-9 | **Audit logs** | Log Analytics, 90 days, blob read/write/delete | supports the C5/C6 audit |
| S-10 | **Resource providers** | register `Microsoft.Insights`, `Microsoft.OperationalInsights`, `Microsoft.AlertsManagement` in `hnf-prod` at apply time | a subscription-level write |

## Also owed before the first live capture (not H3/H4)

- T-0010 W-3: the capture workflow and CLI wiring (live path still refused until Authorisation B).
- H5 (Q-010): recommended **decline** for this slice (architect and Claude agree).
- 2027 calendars (T-0010 W-5) before the capture runs into January 2027.

## Not approved by this document

Everything above is proposed. Nothing here verifies a right, provisions a resource, changes the C5 rule or authorises
live capture.
