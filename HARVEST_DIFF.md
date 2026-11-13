# HARVEST_DIFF — Frontend changes for 6-face integration

HARVEST_DIFF.md — the record of changes made to the harvested
frontend to align it with P13 DataCube's six faces. APPLIED in v1.0.0.

Function:
    Records the design decision and the edits made in `static/view/`.
    The first draft of this file said the change was ~15 lines in one
    file. Reading the code showed HUMAN and validation in six files,
    LENSES hard-coded rather than injected, and "5 faces" built into
    scoring. This version records what was actually done.

Tier:     Tier 1 — Consumer (SCP Substrate)
Decision: Six faces, one per cube side. UNKNOWN replaces HUMAN on
          the 6th side. Human attestation is the gold glow (CSS
          --seal). No new geometry.

## What the old frontend had

- 6 painted sides: FACT, COUNTER, OPINION, FICTION, CONTEXT, HUMAN.
- HUMAN drew `c.validation` (a note, "stale" when a face changed).
- A separate `c.attestation` drew the gold glow.
- Statuses: attested, validated, stale, retracted, draft. Score was
  `filled * .16 + .2 if validated`, and "validated" needed exactly 5
  faces.
- A write path (`view_edit.js`): unlock, new cube, fill, validate,
  attest, accept links, via POST `/api/do`.

## What P13 says

- 6 faces, all equal in kind, UNKNOWN the Dream Space.
- Human validation is NEVER a face. It is a separate signed
  attestation. So the old "validation" and "attestation" are one
  thing here.

## The edits made

### view_field_world.js (the five planned changes, plus three)

1. RGB: `HUMAN: [94, 198, 112]` → `UNKNOWN: [130, 130, 140]`.
2. SIDES: `["HUMAN", [7, 6, 2, 3]]` → `["UNKNOWN", [7, 6, 2, 3]]`.
3. OUT: `HUMAN: [0, 1, 0]` → `UNKNOWN: [0, 1, 0]`.
4. NAMES (`HUMAN: "YOU"`) removed; nothing else used it.
5. `node.sats = [...LENSES, "HUMAN"]` → `[...LENSES]`.
6. *(missed by the draft)* the second sats line in `update()`.
7. Removed the old project's hard-coded tags (`"pca9685"`,
   `"hardware"`) from the bridge links.
8. File header.

### view_grid.js

- `LENSES` is now a slot: `/*LENSES*/[...six faces...]`, filled by
  serve.py (the draft wrongly assumed it was already injected).
- VAR, POSE: HUMAN → UNKNOWN (same CSS side).
- LABEL: attested, retracted, draft ("Not attested").
- Cube, strip and legend loop over LENSES only; the HUMAN
  VALIDATION row in the detail view is gone; the attestation line
  stays. Legend adds "Gold glow: attested".
- Filters: All, Attested, Not attested, Open questions (has an
  UNKNOWN face), Foundational. Validated, Drafts and Overlaps
  removed (no such data in P9).
- Stats: cubes, attested, not attested, open questions.
- Facts line: "n of 6 faces" instead of "% complete · standing".
- "Group by source/entity" button and the cubeEdit hook removed.

### view_field_time.js

- `asOf` no longer uses validation. Status is attested / retracted
  / draft; `score = filled / LENSES.length`; `filled` is set.

### view_field_draw.js, view_field_move.js, view_field_hubs.js

- No HUMAN face in the face map, satellites or labels.
- The green strand from the centre marks attested claims.
- Panels: no validation row, no "standing", no edit buttons.

### view_bar.js

- Key: the six faces, then a key text matching what v1 draws.

### view_style.css

- `--unknown` (#6e6e7a light, #9a9aa6 dark), `.f-UNKNOWN`,
  `.fill-UNKNOWN` replace the HUMAN side. `--human` stays (centre,
  strands). `.pill.validated` and the write-path styles removed.

### view_template.html, view_edit.js

- Read-only v1: unlock and new-cube dialogs, edit buttons, the
  drafts chip and the `/*EDIT*/` slot removed; `view_edit.js`
  deleted. Subtitle rewritten for six faces.

### All JS fragments

- Headers now say serve.py joins them, and in what order.

## Why this is the right decision

- **Matches the data model 1:1.** Six faces, six sides.
- **Respects P13.** Human validation is a signed attestation, shown
  as the glow.
- **No new render code.** Same cube, same corners, new labels.
- **Keeps the old system's value.** Attestation is still visible.

## Alternatives rejected

- **Glow for UNKNOWN:** would make UNKNOWN look like an attestation.
- **Hover for UNKNOWN:** implies dreams aren't real claims. They are.
- **Sixth face hidden:** the Dream Space should be visible.
- **Separate view:** fragments the substrate. Every cube is six faces.
