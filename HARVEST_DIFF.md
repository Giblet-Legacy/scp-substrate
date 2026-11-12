# HARVEST_DIFF — Frontend changes for 6-face integration

HARVEST_DIFF.md — exact changes required to the harvested frontend
to align with P13 DataCube's six faces.

Function:
    Records the precise diffs needed in `static/view/*` to align the
    frontend with P13's six-face model. This is the design decision
    record and the implementation checklist for the frontend patch,
    written before the backend, per build discipline.

Tier:     Tier 1 — Consumer (SCP Substrate)
Decision: Six faces, one per cube side. UNKNOWN replaces HUMAN on
          the 6th side. Human attestation moves to the gold glow
          (CSS --seal). No new geometry.

## What the old frontend had

- 6 painted sides: FACT, COUNTER, OPINION, FICTION, CONTEXT, HUMAN
- 5 lenses were "knowledge"; HUMAN was "who validated it"
- Human attestation was drawn on the 6th side (green)
- A gold glow (--seal) already existed for attestation status

## What P13 says

- 6 faces, all equal in kind: FACT, COUNTER, OPINION, FICTION,
  CONTEXT, UNKNOWN
- UNKNOWN is the Dream Space — hypotheses that passed the Keystone
  Gate but not yet promoted
- Human validation is NEVER a face. It is a separate signed
  attestation, rendered as an overlay.

## The decision (locked)

Six faces, one per cube side. UNKNOWN takes the 6th side. Human
attestation is rendered as a gold glow (existing --seal colour),
not as a face colour.

## The changes required

### Change 1 — `view_field_world.js` line ~8 (RGB table)

Replace `HUMAN: [94, 198, 112]` with `UNKNOWN: [130, 130, 140]`.

A cool grey — reads as "hypothesis, not yet faced". Distinct from
all five other faces. Neutral enough to not imply a value
judgement (UNKNOWN is not "bad", it's "undecided").

### Change 2 — `view_field_world.js` line ~11 (SIDES table)

Replace `["HUMAN", [7, 6, 2, 3]]` with `["UNKNOWN", [7, 6, 2, 3]]`.

Same corner indices — the 6th side's geometry does not change.
Only the label changes.

### Change 3 — `view_field_world.js` line ~14 (OUT table)

Replace `HUMAN: [0, 1, 0]` with `UNKNOWN: [0, 1, 0]`.

Same normal vector.

### Change 4 — `view_field_world.js` line ~15 (NAMES table)

Remove the entry `HUMAN: "YOU"`. UNKNOWN has no special label.
The legend will show "UNKNOWN" via the normal face-name path.

### Change 5 — `view_field_world.js` (LENSES iteration)

The line `node.sats = [...LENSES, "HUMAN"].map(...)` becomes
`node.sats = [...LENSES].map(...)`.

LENSES (defined server-side) will now contain all six faces
including UNKNOWN. No trailing HUMAN special case.

### Change 6 — Server-side injection (when backend is written)

The Python server injects the LENSES array into the template.
The injected value changes from:
    LENSES = ["FACT", "COUNTER", "OPINION", "FICTION", "CONTEXT"]
to:
    LENSES = ["FACT", "COUNTER", "OPINION", "FICTION", "CONTEXT", "UNKNOWN"]

Or, to match the internal vocabulary, the whole frontend's "lens"
terminology becomes "face" throughout. That's a rename pass, not a
behaviour change. Can be deferred to a v1.1.0 if desired.

### No change required

- CSS `--seal` gold (already used for attestation glow)
- CSS `--human` green (leave in place; used by glow rendering
  paths that are already correct)
- `CORNERS`, `EDGES` (geometry does not change)
- `CORNER` projection maths
- Any `view_grid.js` list-view code (renders face names as strings;
  UNKNOWN will display naturally)
- `view_bar.js` (nav / chrome)
- `view_field_time.js` (time filtering uses `filled_at`, agnostic
  to face name)
- `view_field_move.js`, `view_field_hubs.js` (physics, layout)
- `view_edit.js` (write path — dropped in v1 anyway, read-only)

## Summary of edits to `static/view/`

- **`view_field_world.js`**: 5 small text edits (RGB, SIDES, OUT,
  NAMES, sats line)
- **All other files**: unchanged
- **`view_style.css`**: unchanged (--seal already correct)
- **Total surface**: ~15 lines in one file

## Why this is the right decision

- **Matches the data model 1:1.** Six faces, six sides. No impure
  geometry.
- **Respects P13.** Human validation is not a face. It is a signed
  attestation. The glow represents it faithfully.
- **Does not require new render code.** Same cube. Same corner
  projection. Different labels on the painted sides.
- **Does not lose the old system's value.** Human validation is
  still visible — as a gold glow, which the old system already
  had as a feature.

## Alternative designs, and why they were rejected

- **Glow for UNKNOWN**: would have made UNKNOWN look like an
  attestation. Conflates two different concepts.
- **Hover for UNKNOWN**: separates dreams from facts spatially.
  But it implies dreams aren't real claims — they are. They just
  passed a weaker gate. Same shelf, same cube.
- **Sixth face hidden**: makes UNKNOWN invisible by default. The
  Dream Space should be visible — the point is to see what hasn't
  been answered.
- **Separate view**: fragments the substrate. Claims are claims.
  Every cube is six faces.
