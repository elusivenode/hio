---
id: OD-0065
title: "Owner authorises the T-0009 shared-receipt correction (one F1 receipt, two datasets), the cloud-store interface and HIO-only OpenTofu definitions, and one fixed head for Codex review; nothing live"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-shared-receipt-and-storage-authorisation.md (pasted by the owner, verbatim)
  sha256: 4bab9ead05c6ab083018264e92f96c16d7c78f870fa44be82fdc75005f19d9f4
  date: 2026-10-25
  quote: "I authorise a bounded, backward-compatible correction to T-0009's RBA F1 ingestion and publishing design."
applies_to:
  - path: registers/tasks/T-0009-s1b1-cash-capture-and-research.md
    revision: 772b362461c8690a2777e86a31e8fe51ec14c0a9   # branch impl/t0009-adapters-and-run-record
related: {adrs: [HIO-ADR-0012], tasks: [T-0009], findings: []}
---

# OD-0065: shared-receipt correction, storage interface, OpenTofu definitions

## Owner action

1. **Shared-receipt correction.** `rba.cash_rate` and `rba.cash_rate_tri` keep separate dataset
   identities and separate rights evaluations. One immutable raw F1 receipt carries explicit
   provenance to both. This **supersedes my recommendation** (one source id for the file), which the
   owner did not adopt. Stop condition: if the accepted S1a interface cannot be extended without
   weakening an approved observation or rights invariant.
2. **Tests:** shared-receipt attribution, cross-dataset rights evaluation, denied publication, replay,
   unchanged S1a release hashes, the Decimal canonicalisation correction, storage and rebuild equivalence.
3. **Continue** the cloud-store interface and OpenTofu definitions within T-0009, HIO-only resources.
4. **Codex review:** "submit one fixed head for Codex independent review" covering the shared-receipt
   correction, return calculations, reproducibility, rights enforcement and storage controls. The head
   and scope are fixed in the review assignment draft prepared at that head.

## Limits (the owner's, restated)

No provisioning, no credential, no live capture, no new source right, no standards change, no
harness design, no S1b deployment authorisation. Q-013, the storage provider selection, the network and
credential controls and every source right remain undecided and unverified.

## Corrections (append-only)

None.
