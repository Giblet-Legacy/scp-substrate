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
- 6-face decision is RESOLVED: six faces, one per cube side.
  UNKNOWN replaces HUMAN on the 6th side. Human attestation moves
  to the gold glow (--seal). See `HARVEST_DIFF.md` for the exact
  diff plan.
- The frontend patch is NOT yet applied.
- The Python server that wires P9 SQLite to the frontend is NOT
  yet written.

See `SPEC.md` and `HARVEST_DIFF.md` for the resolved design and
remaining implementation work.

## Verifying this repository

Not verifiable yet. No tests, no frozen behaviour. This repo will
be frozen at v1.0.0 only when the 6-face decision is made and the
server is wired and tested.
