<!-- Pasted into the Claude Code chat by the owner, 2026-10-25, verbatim. Recorded by OD-0065. -->

**To Claude — T-0009 shared-receipt correction and storage implementation**

I authorise a bounded, backward-compatible correction to T-0009's RBA F1 ingestion and publishing design.

Preserve the separate dataset identities `rba.cash_rate` and `rba.cash_rate_tri` and their individual rights evaluations. Do not combine them into one source ID merely because they share a publication file.

Implement one immutable raw F1 receipt with explicit provenance linking it to both datasets. Ensure each extracted observation retains the appropriate dataset identity and rights reference.

Before changing accepted S1a code, identify the smallest interface extension required and verify that it leaves existing single-dataset receipt behaviour unchanged. Stop if the change requires weakening an approved observation or rights invariant.

Add tests for shared-receipt attribution, cross-dataset rights evaluation, denied publication, replay and unchanged S1a release hashes.

Continue the cloud-store interface and OpenTofu definitions within the authorised T-0009 scope, using HIO-only resources. Do not provision, create credentials or begin live capture.

Preserve the Decimal canonicalisation correction and independently test storage/rebuild equivalence.

Once the implementation slice is complete, submit one fixed head for Codex independent review covering the shared-receipt correction, return calculations, reproducibility, rights enforcement and storage controls.

Do not reopen harness design, approve new source rights, modify standards or authorise S1b deployment.

Return the new fixed implementation head, relevant test results, outstanding infrastructure gates and the first economically useful research output now reproducible.
