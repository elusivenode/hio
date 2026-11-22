---
id: HIO-EVIDENCE-FACTORS-DATA-LAYERS-1
title: "Local data layers, version 1: silver sets, fund builds from silver, a catalogue and a backup, run on the real stores (OD-0231)"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0231
---

# Data layers 1

> **Exploratory and unaccepted.** The contract is `docs/decisions/local-data-layers-proposal.md` (proposed). **No value from a series is recorded here** (OD-0210). Run once, by the author; not reviewed.

## What was built

Four tools, by four workers in parallel, each checked and integrated at its checked commit:

| Tool | Does | Checked commit |
|---|---|---|
| `tools/silver_build.py` | builds one instrument's silver set from a pinned snapshot and its observation spec | `df67a8e` |
| `tools/factor_build.py` (silver mode) | builds a fund series from one silver set, named by `silver_id` | `94b5f3c` |
| `tools/lake_catalogue.py` | verifies the three layers and rebuilds one DuckDB catalogue with lineage | `1171b70` |
| `tools/lake_backup.py` | verified backup, restore and compare | `945fae0` |

Nine observation specs are proposed in `specs/observations/`. IGB's exclusion moved there from its factor spec, which is now 0.1.2 (0.1.1 archived).

## The run on real data

**Silver:** nine sets in `~/.hio-research/silver/`, one for each fund that has a factor spec, each from the snapshot its existing build used. IGB's set applies its one correction.

**Gold from silver, the equivalence test:** all nine fund series were rebuilt from silver into the factor store.

| Factor | Spec | Build from silver | Same bytes as the build from bronze |
|---|---|---|---|
| `cash.us.bil.market_total_return` | 0.1.0 | `2c6a3315580871b3` | yes (`316e1ae416c2b9ca`) |
| `rates.us.ief.market_total_return` | 0.1.0 | `484ca18a25670c59` | yes (`0f81c557ccd2cd80`) |
| `equity.us.spy.market_total_return` | 0.1.0 | `552a84169712c54f` | yes (`d4ef493e70d0a9d5`) |
| `equity.au.vas.market_total_return` | 0.1.0 | `ba209dc810588b24` | yes (`3400cc7b06bfff70`) |
| `equity.us.ivv_au.market_total_return` | 0.1.0 | `b0be521d9fcdb07a` | yes (`37e6b519c1ed236d`) |
| `rates.au.agvt.market_total_return` | 0.1.0 | `ad64f8ffa1ebcb4e` | yes (`d6212e7ff903725a`) |
| `rates.au.igb.market_total_return` | 0.1.2 | `f74357a0f86f00d7` | yes (0.1.1, `806c46a7f761cd6d`) |
| `rates.au.vgb.market_total_return` | 0.1.0 | `ca146ac531170bd4` | yes (`e3e895a2ce53e464`) |
| `equity.us.ihvv.aud_hedged.market_total_return` | 0.1.0 | `6d6aadb65c63fd24` | yes (`e5a5dbf4ff45c95f`) |

Because the bytes are identical, the series that derive from these (excess, translated, hedged) need no rebuild: they name their parents by `build_id` and `series_sha256`, and the hashes are unchanged.

**Catalogue:** `~/.hio-research/catalogue/lake.duckdb`, built over the EODHD snapshots, the silver sets and the factor store: 5 snapshots, 9 silver sets, 30 gold builds, their series in long form, 121 lineage rows, **0 problems**. A recursive query walks the hedged SPY series back through its parent builds to the snapshot.

**Backup and restore:** the whole research store (998 files) was backed up to a scratch directory on the same Mac, verified, restored into an empty directory and compared: all identical. From the restored copy alone the catalogue verifies with no problem, and one corrected series (IGB) and one original (VAS) rebuild to the same bytes.

## Broken on purpose

| Break | Result |
|---|---|
| One digit changed in a copy of a silver set | the factor build refuses; the catalogue reports the set as a problem and leaves it out |
| A factor spec that declares its own correction, built from silver | refused: corrections belong to the observation spec |

## Limits

- **The backup target was a scratch directory on the same disk.** It proves the tool, and protects nothing until a real target is chosen.
- **Silver covers the nine funds with factor specs.** The H.10 exchange-rate file and the RBA history are still read directly by their builders; in the catalogue they appear only as input files of the builds that used them.
- **Portfolio and risk outputs are not in the catalogue.**
- The bronze mode of the factor build is kept, so two paths to gold exist until it is retired.
- A worker noted one untested path: cleanup after a silver build fails midway (issue W1-1, low).
- The four tools were checked by their author on real data and by the workers' tests on invented data; no independent review.

## Not established

That any series is right. Nothing is accepted, no spec is adopted, and the proposal is not approved.
