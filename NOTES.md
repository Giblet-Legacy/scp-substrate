# NOTES — scp-substrate (Tier 1: SCP Substrate)

NOTES.md — decisions and open questions for SCP Substrate.

## Harvest sources

| Path | What was harvested |
| --- | --- |
| `~/forge/old-substrate/keystone-gate/view/*.html` | view_template.html |
| `~/forge/old-substrate/keystone-gate/view/*.css` | view_style.css |
| `~/forge/old-substrate/keystone-gate/view/*.js` | 9 JS modules (~87KB); view_edit.js later dropped |

Everything else in the old repo (`sc.db`, `src/`, `keystone-gate/kg_*.py`,
`seeds/`, `scripts/`, docs) was **deliberately not harvested**. The
old data model (capsules/links/events/trust_scores) does not match
P9 substrate (claims/evidence). Old capsules are dead.

## Decisions

1. **Read-only v1.** No writes through the browser. All writes go
   through The Cockpit (`forge remember`, `forge dream`, etc.).
2. **No old data migration.** The legacy `sc.db` stays dead.
3. **Frontend harvested, not rewritten.** Patched for six faces and
   read-only (HARVEST_DIFF.md).
4. **Backend:** `serve.py`, stdlib `http.server`, SQLite `mode=ro`.
5. **Human validation = attestation.** P13 says it is one signed
   attestation; the old build's separate validation is gone.

## Questions (all resolved for v1.0.0; detail in SPEC.md §5)

- **Q1. How does UNKNOWN appear?** Sixth side, cool grey. Attestation
  is the gold glow.
- **Q2. Time slider source.** `created_at`, plus face and attestation
  `at`. Superseded claims not shown.
- **Q3. Links between claims.** None stored. Claims cluster by
  subject. A `claim_links` table waits for a P9 v2+ that defines one.
- **Q4. Port, database.** 8085 on 127.0.0.1; `--db`, else
  `$FORGE_HOME/forge.db`, else `~/.forge/forge.db`.

## For a later layer (not v1)

- Where attestations live. P9 and P13 don't define it yet; v1 reads
  `capsule.attestation` or evidence with `kind: "attestation"`.
- Signature verification on read (P9 v2 `verify=True`).
- P13 inspection grade (CRYSTALLINE … SPARSE) in the panel.
- Trust (`standing`) from P10/P11.
- Superseded history in the field.
- Per-function headers inside the harvested JS (files have headers).
