---
id: HIO-ENG-SAFEGUARDS
title: Public-repository and network safeguards (S1a)
status: current
owner: HIO architecture lead (owner); implementation agent (maintainer)
version: 0.1
last_reviewed: 2026-10-24
authorised_by: [OD-0019, OD-0020]
---

# Public-repository and network safeguards

This repository is **public** (OD-0019). Every commit is published, and a pushed secret must be
treated as leaked even if it is deleted afterwards. These safeguards implement OD-0020 item 4.
They add no rule beyond the approved rights standard and `AGENTS.md`; they make those rules
mechanical.

## What never enters git

| Class | Examples | Enforced by |
|---|---|---|
| Secrets | keys, tokens, passwords, URLs with credentials, `.env` files | `.gitignore`; `tools/check_repo.py public` (secret patterns); pre-commit hook; CI |
| Downloaded or source data | any receipt, observation export or vendor file | `.gitignore` (`data/`, `receipts/`, …); `public` refuses data files outside `tests/fixtures/synthetic/` |
| Local databases | DuckDB, SQLite, WAL files | `.gitignore`; `public` refuses `*.duckdb`, `*.db`, `*.sqlite*` |
| Non-releasable artefacts | release Parquet, artefact payloads, pickles, archives | `.gitignore`; `public` refuses binary data formats and object-store directories |
| Oversized files | anything over 512 KB | `public` |

**Synthetic fixtures** are the only data files allowed. They live under
`tests/fixtures/synthetic/`, and **line 1 of each must contain `SYNTHETIC`**. Their source ids
start with `synthetic.`. `registers/sources.yaml` may never contain a `synthetic.` source, or an
`owner_verified`/`contract` verification without `verified_by: OD-NNNN` (`tools/check_repo.py
yaml`). Synthetic rights metadata therefore cannot leak into the genuine register (OD-0020
item 3).

The local object store used by S1a tests and demo builds lives in a temporary directory, or in
`.hio-store/` (ignored). It is never committed.

## Network

| Step | Network | Why |
|---|---|---|
| Dependency installation (`uv sync` / `uv run --with`) | **allowed**, to the package index only | installing pinned packages from `uv.lock` |
| Tests and builds | **blocked**: `tests/conftest.py` refuses every non-loopback socket connection | S1a is synthetic-fixture-only (OD-0017) |
| Source code in `src/hio/` | **no network client may be imported** (`socket`, `http`, `urllib`, `requests`, `httpx`, …) | `tools/check_repo.py imports` |
| Source-data access | **forbidden in S1a** | real-source adapters are S1b, which is not authorised |

GitHub Actions cannot restrict a job's egress without a third-party action. CI therefore relies
on the import rule and the socket block, not on a runner firewall. Adding an egress allow-list is
an S1b question.

## CI permissions

The workflow requests `contents: read` only. The repository's default workflow token is
read-only. Third-party actions are pinned to commit SHAs. There are no secrets and no `schedule:`
triggers. `persist-credentials: false` keeps the checkout token out of the workspace.

## Local hook

`sh tools/install-hooks.sh` installs a pre-commit hook running `public`, `imports` and
`valid_time`. It is a convenience; CI is the enforcement point.
