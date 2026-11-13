# CHANGELOG — scp-substrate (Tier 1: SCP Substrate)

CHANGELOG.md — build history for SCP Substrate, latest entry at top.

## [v1.0.0] — 2026-11-13 — FROZEN

### Good
- `serve.py`: stdlib `http.server`, binds 127.0.0.1:8085. Reads P9
  SQLite with `mode=ro`, so SQLite itself refuses writes and a
  missing database is never created. GET/HEAD only; writes get 405.
- API: `/api/health` (200/503 with row counts), `/api/claims` (active
  claims, adapted), `/api/claims/<id>` (any claim, with evidence).
- Adapter keeps every P9 column, reads faces from a stored P13 cube
  or the claim's `face` tag, and reads attestation from the capsule
  or `kind: "attestation"` evidence (SPEC §3).
- Six-face patch applied across `static/view/`: UNKNOWN (cool grey)
  on the 6th side, attestation as the gold glow and green strand.
  LENSES is injected by the server. No HUMAN side, no validation.
- Read-only page: write path (`view_edit.js`, unlock and new-cube
  dialogs, edit buttons) removed.
- Injected JSON is escaped, so claim text cannot break out of the
  page's scripts. Static serving is limited to files directly in
  `static/view/`.
- 24 tests pass, including claims written by P9's own
  `substrate_v2` (sign, supersede, evidence) and a `node --check` of
  the joined scripts. Checked in headless Edge: page loads with no
  console errors.
- Q2–Q4 resolved (SPEC §5).

### Bad
- Signatures are not verified on read; the server trusts the
  database file.
- Where attestations live is not defined by P9 or P13. v1 uses its
  own convention (SPEC §3) until one is.
- No P13 inspection grade, no trust (`standing` is always 0), and
  superseded claims don't show in the field.
- The harvested JS has file headers but not per-function headers.

### Ugly
- HARVEST_DIFF's first draft said "~15 lines in one file". It was
  six files, plus a hard-coded LENSES and a 5-face scoring rule. The
  sprint brief said not to touch other files in `static/`. That was
  overridden, because the one-file patch would have left HUMAN in
  the grid, legend, panels and time slider.
- Entity/subject hubs and cluster modes are still in the frontend,
  always empty. They are dead weight until a layer feeds them.

## [v0.1.0-scaffold]

### Good
- Repository scaffolded: `Giblet-Legacy/scp-substrate` created as
  Tier 1 Consumer (The Memory / 4D Graph Viewer).
- Static frontend harvested from prior build
  (`JamesTheGiblet/scp-substrate` keystone-gate/view, 11 files,
  ~100KB): view_template.html, view_style.css, and 9 JS modules.
- Frontend is vanilla JS + Canvas 2D. Zero external deps. No node,
  no build step, no CDN.
- Old 12MB `sc.db` and its capsule schema NOT migrated. The old
  data is dead. New claims live in P9's `claims` table.
- Read-only posture recorded: no writes through the browser in v1.
- 6-face decision made: six faces, one per cube side. UNKNOWN
  replaces HUMAN on the 6th side. Human attestation moves to the
  gold glow (--seal), per P13's rule. Recorded in HARVEST_DIFF.md.

### Bad
- Frontend renders 5 knowledge faces + HUMAN (attestation) on the
  6th side. Decision made to swap HUMAN for UNKNOWN — see Good.
- Backend server (Python, reads P9 SQLite) not yet written.
- No tests, no spec freeze. This is v0.1.0-scaffold, not v1.0.0.

### Ugly
- The old visualiser used 5-lens geometry for cubes. A cube has 6
  sides; 5 are painted. Extending to 6 faces is not "add a face" —
  it is a design decision about how dreams (UNKNOWN) appear. That
  decision is deferred to the next session with fresh eyes.
