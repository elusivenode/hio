---
id: HIO-RESEARCH-T0003-VENDOR-DRAFTS
title: "T-0003 draft written questions to EODHD and S&P DJI: NOT SENT"
status: draft              # for owner review only (OD-0013). Do not send.
owner: owner (approves sending); drafted by claude/documentation-agent
created_at: 2026-10-18
task: T-0003
---

# Draft vendor questions (NOT SENT)

> **OD-0155: the owner may send these; none has been sent.** Claude has no mail channel, and the sender's details and recipient addresses are for the owner. Record the date sent as a correction to OD-0155.
>
> Drafted for owner review under OD-0013; revised under OD-0147 (2026-11-04), so the context describes HIO's independent research, its write-once store, and processing, and not only the SMSF. Sending needs a separate owner
> instruction. The sender's name and contact details are left blank on purpose. No
> fund-identifying details are included beyond what the questions need.

## 1. To EODHD (EOD Historical Data)

**Subject:** Licensing questions before subscribing: private research use, retained and derived data

Hello,

I am considering an EOD Historical Data subscription and would like to confirm how your terms apply before subscribing.

**Context:** I run a private investment research system on my own. It computes investment returns and risk analysis from end-of-day data, and I would not sell it or offer it to anyone. Its results may inform decisions for a small self-managed family superannuation fund in Australia, of which I am one of two individual trustees (two members, no employees, no external clients). Raw data would never be redistributed or displayed to anyone else.

1. **User classification:** does this count as **Non-Professional** ("solely in a personal capacity")? Does the fund's use of the results make me a Professional User? If so, which plan applies, and at what price?
2. **Derived figures:** may I compute returns and other figures from your prices and dividends, and keep them in my system? May derived figures (not raw prices) appear in a private report read only by the fund's two trustees and its auditor?
3. **Storage:** may I keep raw downloads and derived figures in private cloud object storage, processed in a private cloud build environment? My store retains records under a write-once policy for up to ten years, so they can't easily be deleted. Is that compatible with your terms?
4. **After cancellation:** what may I keep once a subscription ends: raw data, derived figures, or both? If deletion is required, does the write-once store above prevent me from using your data at all?
5. **Automated use:** may a scheduled job download data under my key? What request limits apply?
6. **Third-party tools:** may raw data be processed by cloud services acting for me? I keep raw licensed data out of AI tools, but would AI tools be permitted to see derived figures?
7. **Data content:** for US-listed and ASX-listed ETFs, do you provide **unadjusted** daily closes **and** separate dividend records (ex-date, pay date, amount) and split records? Are historical values ever revised, and is a revision flagged? How far back does each go?
8. **Futures:** do you offer individual-contract daily settlements, and under the same terms?
9. **Closing price:** for a US-listed ETF, what exactly is your end-of-day close: the primary exchange's official close, a consolidated close, or something else? Which venue or data partner does it come from, and has that changed over the history?
10. **Named coverage:** do you cover a broad US equity ETF, a 7-10 year US Treasury ETF and a T-bill ETF (for example SPY or IVV, IEF and BIL), back to each fund's inception, on the unadjusted-close, dividend and split basis in question 7?
11. **Checking your data:** may I compare figures computed from your data with a fund issuer's published total returns, and keep the result of that comparison?
12. **A short trial:** can I take one month of access on these terms? What can I keep when it ends, and what is the full cost, including any exchange fees?

Thank you,
[name, contact details: to be completed by the owner]

## 2. To S&P Dow Jones Indices (data licensing)

**Subject:** Licensing enquiry: S&P 500 total-return index levels for private internal research

Hello,

I would like to understand the licensing options and pricing for S&P 500 index-level data.

**Context:** I run a private investment research system on my own. Its results may inform decisions for a small self-managed family superannuation fund in Australia, of which I am a trustee (two members). I would not create or market any investment product, and I would not redistribute the data.

1. **Product:** daily **S&P 500 Total Return** and **Net Total Return** index levels (USD), historical and ongoing. Which licence covers this, what does it cost, and how far back does the history go?
2. **Derived figures:** may returns computed from licensed levels be kept in my system and shown in a private report read only by the fund's two trustees and its auditor?
3. **Storage and retention:** may licensed data and derived figures be held in private cloud storage under a write-once policy for up to ten years? What may be retained after a licence ends?
4. **Methodology:** are the index methodology and the dividend-reinvestment and withholding conventions for the net series available to licensees?

Thank you,
[name, contact details: to be completed by the owner]

## Notes for the owner

- These questions map to the open items in
  [`T-0003-equity-total-return-sources.md`](T-0003-equity-total-return-sources.md), so the
  answers can be recorded as evidence (verification `contract` or `owner_verified`).
- Sending reveals limited context about the fund (a two-member family SMSF). Remove that if you
  prefer a generic enquiry, but the answer to question 1 may then not be reliable.
- **Question 3 can decide the design.** Evidence-store retention is 3,650 days under the account default, so a licence that requires deletion needs a different home for its raw data.
