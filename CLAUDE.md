@AGENTS.md

## Claude Code specifics

- This repository is HIO, a separate system. The `macsmsf` `CLAUDE.md` and its skills
  (`gold-math`, `portfolio-analytics`, …) govern **SMSF** work only. Do not apply them to HIO
  work unless a HIO document links to one as evidence.
- HIO skills: `hio-session` and `hio-return-accounting`.
- Older documents write paths as `hio/<p>`; here that means `<p>` ([`MIGRATION-MAP.md`](MIGRATION-MAP.md)).
- Auto-memory is a convenience cache, never a record. Anything that matters goes into a
  repository file (precedence in `AGENTS.md`).
