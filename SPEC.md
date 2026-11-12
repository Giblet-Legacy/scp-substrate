# SPEC — scp-substrate (Tier 1: SCP Substrate) — DRAFT

SPEC.md — draft specification. NOT FROZEN.

Function:
    Records the target behaviour for SCP Substrate v1.0.0. This is a
    DRAFT. It exists so the 6-face decision (Q1 in NOTES.md) can be
    resolved before any backend code is written.

Tier:      Tier 1 — Consumer
Depends:   P8 Store (SQLite), P9 Substrate (claims/evidence)
Consumed:  The operator (visual exploration), The Legacy
Version:   DRAFT — not yet v1.0.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

## 1. Six faces, one per cube side (DECIDED)

The old frontend rendered each cube with 6 painted sides — but its
6th side was HUMAN (attestation), not UNKNOWN. P13 DataCube defines
6 faces (FACT, COUNTER, OPINION, FICTION, CONTEXT, UNKNOWN) and
explicitly states that human validation is NEVER a face — it is a
separate signed attestation.

Decision: **six faces, one per cube side.** UNKNOWN replaces HUMAN
on the 6th side. Human attestation moves to the existing gold glow
(CSS --seal).

Full rationale, exact diffs, and rejected alternatives are recorded
in HARVEST_DIFF.md (this repo).

## 2. What v1.0.0 will look like (once Q1 is resolved)

- Python HTTP server, stdlib `http.server`. No Flask, no FastAPI.
- Serves `static/view/` (the harvested frontend).
- Exposes a read-only JSON API:
  - `GET /api/claims` — all active claims, adapted to the frontend's
    expected data shape
  - `GET /api/claims/<id>` — one claim with evidence
  - `GET /api/health` — probes P8/P9 SQLite
- Reads from `FORGE_HOME/forge.db` (same DB The Cockpit writes to).
- Zero writes. Browser cannot mutate the substrate.
- Single-operator, localhost only. No auth in v1.

## 3. Known limitations (will appear in v1.0.0 spec)

- Read-only. All writes via The Cockpit.
- No auth. Localhost only.
- No cross-substrate linking.
- No multi-user.
- Time slider source TBD (see NOTES Q2).
- Links between claims TBD (see NOTES Q3).

---

## Document control

- Status: DRAFT. Not frozen.
- v1.0.0 requires:
  1. Q1 (6-face visual) resolved. — RESOLVED (six faces, one per
     side; UNKNOWN on the 6th; attestation as gold glow). See
     HARVEST_DIFF.md.
  2. Frontend patch applied (view_field_world.js, ~15 lines).
  3. Backend server written (stdlib http.server, read-only JSON).
  4. Tests written and passing.
  5. Independent verification (read-only JSON matches P9's claims).
- When all are met, this becomes SPEC v1.0.0 and the repo becomes
  frozen.
