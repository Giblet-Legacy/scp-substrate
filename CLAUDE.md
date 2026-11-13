# Forge Stack Context — SCP Substrate

CLAUDE.md — Context briefing for AI assistants working in this repository.

## What this repo is
Tier 1 Consumer. Reads P8/P9 substrate SQLite, renders claims as a
3D time-aware visual field. Does not store, sign, or classify —
that is P8/P9/P13's job. This consumer only renders.

## Status: FROZEN at v1.0.0
`serve.py` (stdlib, read-only, SQLite mode=ro) serves the harvested
frontend in `static/view/`, patched to P13's six faces: UNKNOWN on
the 6th side, human attestation as the gold glow (SPEC.md §1,
HARVEST_DIFF.md). Tests: `python -m pytest -q`. Changes after freeze
are new layers and a new SPEC version, not edits to v1 behaviour.

## v2 layer
`serve_v2.py` (SPEC_V2.md, frozen 2.0.0) is the entry point from
v2: reads through P9 `substrate_v3` with verification and follows P9
SPEC_V3 §3 for attestations. `serve.py` stays frozen.

## v3 layer
`serve_v3.py` (SPEC_V3.md, frozen 3.0.0) is the entry point from
v3: v2 plus ISO 8601 times, so attested claims no longer stop the
field drawing. Run `python serve_v3.py`.

## v4 layer
`serve_v4.py` (SPEC_V4.md, frozen 4.0.0) is the entry point from
v4: v3 plus a "Keywords" cluster mode where a subject is the unit.

## The Immutable Rule
Never rewrite a primitive. Add a layer. This repo consumes
primitives; it never edits them.

## Read-only v1
The web UI is READ-ONLY in v1. It reads P8/P9 SQLite and renders.
No writes through the browser. All writes go through The Cockpit
(`forge remember`, `forge dream`, etc.).

## Dual-Device Workflow
S24/Termux and laptop/VS Code. LF-only. British English (-ise).
Good/Bad/Ugly CHANGELOG, latest at top. Header discipline on every
file and every function.
