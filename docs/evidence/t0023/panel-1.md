---
id: HIO-EVIDENCE-T0023-PANEL-1
title: "T-0023 steps 1 and 2: interval classes and the frozen AUD defensive-sleeve panel"
status: draft
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-04
instruction: OD-0177
---

# T-0023 panel 1

> **Exploratory and unaccepted. No value is recorded here,** only hashes, counts and classes. Values are in the local run directories. Not reviewed by Codex.

## What this shows, and what it doesn't

It shows that E-0003 V1 can be rebuilt from retained bytes and names exactly what ran. **It doesn't show that any input is right.** SPY, IEF and BIL before 2016 and the RBA's pre-2011 rates still have no independent check. A hash doesn't close that gap: that's step 3.

## Step 1: interval classes

`interval_classes` replaces `intervals_span_zero`. "Every block length" is now said only when it's true, and a mixed result names the lengths on each side.

**No recorded result was misclassified.** The classes for E-0003 V1, at blocks of 6, 12 and 24 months:

| Effect | Return p.a. | Volatility | Max drawdown |
|---|---|---|---|
| Cash rate and currency | not distinguished | distinguished at every block length | not distinguished |
| Treasury duration | not distinguished | not distinguished | not distinguished |
| Total | not distinguished | distinguished at every block length | not distinguished |

None is mixed. The first E-0003 result (from 2011) has no rebuild here. It was checked by OD-0175 correction 1.

## Step 2: the panel

```
uv run --with xlrd==2.0.1 python tools/e0003_panel.py rebuild
```

**Panel id** `1aa2991815b03ba2acc908b0bf3655faae45199a04991181aeb8975ff2e58190`: the sha256 of the input hashes, the conventions and the panel's text at twelve decimals. The code revision isn't part of it, because release ids hold the revision and change at every commit. 233 months, 2007-05-31 to 2026-10-30.

| Input | sha256 |
|---|---|
| EODHD snapshot `s2`, manifest | `bb40a84650a8b7104e3d116a5d0773619dd4870ee20190a80bab370135fee38d` |
| SPY end of day | `d5012ffeae590e05bfc227b675b496393dfc70fdf433a35f5dfa42606312dbe3` |
| SPY distributions | `6370411a4e455df6ded621fcaadfa5dddcd4e8802b5306c83519f918f0c8d6d0` |
| SPY splits | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |
| IEF end of day | `99242cb7ca424bc6f1d42c115dbe6566d5580a990683d106017a21916726019e` |
| IEF distributions | `7998f1477b4e69662595a685d57c589a7c658668fb82d397f6f3f7a7297609dd` |
| IEF splits | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |
| BIL end of day | `abd11afd81caa2d5188af0d7e0ffdbb8f33b6ccb882f6de167b87440f876f857` |
| BIL distributions | `c27fe42430b8ad87d62136d220330c063d46791240453e6f62927caaed51c1b1` |
| BIL splits | `72fc76f71312c195bc2385abd71e07a78e13549f63ac883d70e69fababf03929` |
| US symbol list | `8c1f4d0c6f38d1b1a1e7df9d2f45c47b4786469f1221e16fbd0786fdbed4519c` |
| RBA F1 receipt | `8b9f41eebfd3748b70459cc4782fac51d58fda26c0c05b338a014572bb9c6297` |
| RBA historical `.xls` | `e5c18581e30081309a50dc8dce87f1ef04095538958b6e95e59f18a7868884dc` |
| `FIRMMCRID` extract, made again from the `.xls` | `55513436e68fd4dfe3e816dab59a87c8adf4d882cea6e15f6edaf46d0bf79433` |
| H.10 archive | `1c312d2fc1de99f174c26178a2cb1f0f0f6a4a08b6dce25b043603fec9a3f24a` |

## The two rebuilds

Both ran on the owner's Mac with Python 3.13.3, NumPy 2.5.4 and xlrd 2.0.1, `uv.lock` sha256 `113922fd…`.

| Check | `9333ed4` | `1d500b7` (id frozen) |
|---|---|---|
| Panel text sha256 | `2579764a…` | the same |
| Panel id | `1aa29918…` | the same; equals the frozen id |
| Comparison values sha256 | `87205407…` | the same |
| Values equal E-0003 V1's recorded file | yes | yes |
| Each sleeve's `data.csv` equals E-0002's recorded release | yes | yes |
| Release ids | | differ, as expected |
| Seam check | 189 of 189 | 189 of 189 |

**The recorded V1 report differs in two ways only:** its header carries the OD-0176 wording, and it now ends with the panel id.

## Limits of this evidence

- **One machine.** No one else has run it, and twelve decimals guards against last-bit differences only in the panel's text. The values hash is exact, so another machine may differ there.
- **The author ran it.** A permitted verifier hasn't.
- **The tests use invented data.** A Sonnet worker wrote them (W1, 37 tests); the orchestrator checked them by breaking the tool 13 ways, and all 13 were caught.
- **`1d500b7` itself had two failing tests:** freezing the id changed a default they relied on. The tool didn't change after it; the tests were fixed in the next commit.
- **The first E-0003 result isn't part of this rebuild,** only V1.
