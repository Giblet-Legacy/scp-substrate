# NOTES — scp-substrate (Tier 1: SCP Substrate)

NOTES.md — open questions and decisions for SCP Substrate.

## Harvest sources

| Path | What was harvested |
|---|---|
| `~/forge/old-substrate/keystone-gate/view/*.html` | view_template.html |
| `~/forge/old-substrate/keystone-gate/view/*.css`  | view_style.css |
| `~/forge/old-substrate/keystone-gate/view/*.js`   | 9 JS modules (~87KB) |

Everything else in the old repo (`sc.db`, `src/`, `keystone-gate/kg_*.py`,
`seeds/`, `scripts/`, docs) was **deliberately not harvested**. The
old data model (capsules/links/events/trust_scores) does not match
P9 substrate (claims/evidence). Old capsules are dead. Old Python
server used the old schema. Not reused.

## Decisions taken at scaffold time

1. **Read-only v1.** No writes through the browser. All writes go
   through The Cockpit (`forge remember`, `forge dream`, etc.).
2. **No old data migration.** 12MB of legacy `sc.db` stays dead.
   New claims populate via The Cockpit; the substrate viewer reads
   from P9's `claims` table.
3. **Frontend harvested, not rewritten.** The vanilla JS + Canvas
   works. Porting it is cheaper than rewriting it.
4. **Backend deferred.** Python server (stdlib `http.server`) reads
   P9 SQLite, serves static files, exposes a read-only JSON API.
   Written next session.
5. **6-face decision deferred.** See open question Q1 below.

## Open questions (must resolve before v1.0.0 freeze)

- **Q1. How does UNKNOWN appear visually? — RESOLVED**
  Six faces, one per cube side. UNKNOWN replaces HUMAN on the 6th
  side. Human attestation moves to the gold glow (--seal), per
  P13's rule that human validation is never a face.
  Full rationale and exact diffs in HARVEST_DIFF.md.

- **Q2. Time slider source.** Old code used `created` timestamps on
  capsules. P9 `claims` table has `created_at`. Map them, or derive
  a different temporal axis (e.g. `superseded_at`)?

- **Q3. Links between claims.** Old `links` table had custom
  relationships. P9 does not. Do we (a) show only spatial proximity
  (no explicit links), (b) derive links from shared subjects, or
  (c) expose a separate `claim_links` table that a future P9 v2
  could support?

- **Q4. Port, workspace, defaults.** Server on which port? Default
  8085 (matches The Cockpit's future `forge web`)? Reads from
  `FORGE_HOME/forge.db` or a `--db` flag or env var?

## Not-yet-written

- Python server (`serve.py`, stdlib `http.server`)
- JSON API adapter (P9 claims → old frontend's data shape)
- Static file router
- Tests
- The 6-face visual integration
