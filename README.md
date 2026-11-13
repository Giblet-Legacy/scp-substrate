# scp-substrate — SCP Substrate (Tier 1)

README.md — repository purpose and consumer contract for SCP Substrate.

Function:
    Renders P9 claims as a 3D time-aware field of six-faced cubes.
    Read-only. A stdlib Python server reads P9's SQLite directly and
    serves the harvested frontend. No writes through the browser.

Tier:     Tier 1 — Consumer (The Memory)
Depends:  P8 Store (SQLite), P9 Substrate (claims/evidence)
Consumed: The operator (visual exploration), The Legacy
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
Status:   1.0.0 — FROZEN (serve.py). v2 (serve_v2.py, SPEC_V2.md):
          verified reads via P9 substrate_v3, frozen at 2.0.0.
          v3 (serve_v3.py, SPEC_V3.md): ISO times, so attested claims
          draw; frozen at 3.0.0. Run `python serve_v3.py`.

## Run it

    python serve.py                   # $FORGE_HOME/forge.db, port 8085
    python serve.py --db path/to/forge.db --port 8085

Then open <http://127.0.0.1:8085/>. Python 3 standard library only.

## What you see

- One cube per active claim, clustered by subject.
- Six sides, one per P13 face: FACT, COUNTER, OPINION, FICTION,
  CONTEXT, UNKNOWN (grey). Hollow means not inspected.
- Gold glow and a green strand: a human has attested the claim.
- The time slider replays claims as they were written.

## API (read-only)

- `GET /api/health`: database probe (200 / 503)
- `GET /api/claims`: active claims, adapted
- `GET /api/claims/<id>`: one claim with evidence

Contract: `SPEC.md`. Frontend changes: `HARVEST_DIFF.md`.

## Verifying this repository

    python -m pip install pytest      # dev only
    python -m pytest -q

The P9 end-to-end test writes real signed claims with
`../substrate-layer/substrate_v2.py`. It needs the sibling
substrate, envelope and sign layers plus `cryptography`, and skips
without them. Two more tests skip without `node` or
`../datacube-layer`.
