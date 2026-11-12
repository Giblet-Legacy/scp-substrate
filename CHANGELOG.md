# CHANGELOG — scp-substrate (Tier 1: SCP Substrate)

CHANGELOG.md — build history for SCP Substrate, latest entry at top.

## [Unreleased]

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

### Bad
- Frontend renders 5 faces (FACT, COUNTER, OPINION, FICTION,
  CONTEXT). P13 DataCube has 6 faces. UNKNOWN is not yet
  represented in the visual language.
- Backend server (Python, reads P9 SQLite) not yet written.
- No tests, no spec freeze. This is v0.1.0-scaffold, not v1.0.0.

### Ugly
- The old visualizer used 5-lens geometry for cubes. A cube has 6
  sides; 5 are painted. Extending to 6 faces is not "add a face" —
  it is a design decision about how dreams (UNKNOWN) appear. That
  decision is deferred to the next session with fresh eyes.
