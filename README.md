# scp-substrate — SCP Substrate (Tier 1)

README.md — repository purpose and consumer contract for SCP Substrate.

Function:
    Renders P8/P9 claims as a 3D time-aware semantic field. Read-only
    in v1. The frontend is harvested from a prior build; the backend
    reads P9 substrate SQLite directly. No writes through the browser.

Tier:     Tier 1 — Consumer (The Memory)
Depends:  P8 Store (SQLite), P9 Substrate (claims/evidence)
Consumed: The operator (visual exploration), The Legacy
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
Status:   0.1.0-scaffold — SCAFFOLD, NOT FROZEN

## Status disclosure

This repository is a scaffold, not a finished consumer.

- The 3D frontend (`static/view/`) was harvested from a prior build.
- It renders 5 faces (FACT, COUNTER, OPINION, FICTION, CONTEXT).
- P13 DataCube has 6 faces — the 6th is UNKNOWN (the Dream Space).
- The visual language for UNKNOWN has NOT yet been decided.
- The Python server that wires P9 SQLite to the frontend is NOT
  yet written.

See `SPEC.md` for the open question and the pending work.

## Verifying this repository

Not verifiable yet. No tests, no frozen behaviour. This repo will
be frozen at v1.0.0 only when the 6-face decision is made and the
server is wired and tested.
