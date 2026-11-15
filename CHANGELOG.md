# CHANGELOG — scp-substrate (Tier 1: SCP Substrate)

CHANGELOG.md — build history for SCP Substrate, latest entry at top.

## [Unreleased]

### Good

- `SPEC_V8.md`, `serve_v8.py`, `test_serve_v8.py` (3 tests, run red
  first): you at the centre of what is yours. A claim about the person
  ("James Gilbert is building SCPBot") is shown in the orb of its
  object, so each project orbits James with its claims inside; no orb
  is named after him. A project that is also a registered repo is one
  orb (the-legacy, scp-substrate, sc-os, lllm). Only the page's copies
  change; signed claims and the API are v7's. On the real memory: 24
  orbs (one of them "James Gilbert") become 102, James at the centre.
  Built on James's delegation ("i should be at the centre …").
- `static/view_v4` (a copy of view_v3, which is untouched; only
  view_field_hubs.js and view_bar.js differ): your orbs (`yours: true`
  in HUBS) are pink and held at half the orbit radius with twice the
  pull, so they ring you closely and the repos form the outer shell
  (James: "my stuff should be a different coulr and tighter to the
  centre"). 5 tests, including one that parses the whole page script.
- Sections (SPEC_V8 §1.1, after screenshots showed 78 one-claim orbs,
  most unnamed): your projects are now parts of eight section orbs
  (hardware and robotics, games, writing and story engines, …) plus
  "about James Gilbert" and "other", from each claim's CONTEXT; no
  claim re-signed. Inside a section every project circles it, named,
  with its status in the panel (shipped, built, is building…). On the
  real memory: 102 orbs become 33 (10 yours, 23 repos).
- view_v4 also: you stay green (drawn again over the strands); orbs are
  held to their shells (yours 0.4–0.6 of the radius, repos 0.9–1.1);
  the camera frames where the orbs settled, so the field fills the
  screen; part names keep clear of every other name.
- A claim about the person can name its own section: a `section` field
  on the signed capsule (read from P9) wins over the CONTEXT wording,
  which stays as the fallback for the 83 identity claims already
  signed. The camera's margin now fits the furthest orb and its name
  on the shorter side, so nothing is cut off at phone width (checked
  at 412 px). Not frozen (NOTES).

### Bad

- v5–v7 made one orb per claim subject, so the 83 identity claims about
  James sat in a single "James Gilbert" orb circling James himself.
- view_v4's first build named a helper `reach`, which view_field_form.js
  already declares; the joined page script failed and the field drew
  nothing. Caught on a screenshot, renamed (`orbitOf`), and the v8 tests
  now run the whole page script through `node --check`.
- Springs alone did not hold "yours" close: measured in the page, the
  orbs pushing apart carried the sections out to 0.86–0.93 of the
  radius and the repos to 1.43, and the camera framed that, so the
  field looked smaller than before. Now each kind is held in a band.

### Ugly

- The 83 identity claims signed on 2026-11-15 carry no `section` field,
  so they are grouped by their CONTEXT wording ("Identity capsule <id>,
  <section>."). New claims about the person should carry `section`.


## [v7.0.0 (with v5.0.0 and v6.0.0)] — 2026-11-14 — FROZEN

### Good

- `SPEC_V7.md`, `serve_v7.py`, `static/view_v3` (a copy of view_v2, which
  is untouched), `test_serve_v7.py` (6 tests, run red first against a
  plain copy of view_v2, in headless Edge): a link to one orb
  (`#entity:<id>`) opens it with its panel instead of a blank page (it
  asked for an "Entities" mode v5+ never sends); orb names are placed
  nearest first and a name that would land on another waits until its
  orb moves clear, so the field reads on a phone. 54/54 pass. Built on
  James's delegation ("take a bunch of screenshots and report", "yes").
  Not frozen (NOTES).
- `SPEC_V6.md`, `serve_v6.py`, `test_serve_v6.py` (3 tests; written with the
  code, not run red first): "depends on" claims become the frozen
  frontend's neighbour links (James: "links together are weak"): the
  strongest thread, drawn in every view, explained as "You linked these:
  ... depends on ... The reason given: <FACT>" instead of "a match on
  words, so it can be a coincidence". No server "All lenses" view; the
  field opens on "Tags". Built, not frozen (NOTES).
- `static/view_v2`, a frontend layer (a copy of the frozen static/view,
  which is untouched; James: "move freely and let natural clusters form
  ... 360 degree movement"): orbs are bodies moving in 3D round you,
  pushed apart, held at orbit distance and pulled together by your
  links, turning slowly on a tilted axis, so related subjects cluster
  (datacube with rules; trust, weight and the Leighton Engine; ledger,
  HAL, envelope and sign); your links in amber at full strength at any
  zoom; each orb named once. serve_v6 renders from it. 48/48 pass.
- `SPEC_V5.md`, `test_serve_v5.py` (5 tests, run red first) and
  `serve_v5.py`: the field draws James's model. The person entity (P9
  v4) is the centre; each subject is an orb on a strand from the centre
  with its claims gathered round it; "depends on" claims are threads
  between subjects in the opening view. Uses the frozen frontend's hubs
  (HUBS, THINGS) and MODES.ALL; static/view/ untouched.
- 44/44 pass. serve.py and v2-v4 untouched. Built on James's delegation
  ("the subjects need their own orb with their claims orbiting them as
  the subject orbits me … connections between each other"). Not frozen
  (NOTES).

### Bad

- My screenshot report said the field's bars ran off a phone's right
  edge. Wrong: headless Edge will not make a window narrower than about
  500 px, so the "412 px" shot was a 496 px page cut short. The v7 tests
  measure phone width in a true 412 px frame instead.
- The frozen frontend names the opening view "All lenses", and labels
  each orb twice (the orb's name and its cluster's "#name"); changing
  either needs a new frontend layer.

### Ugly

- With 23 subjects the ring of orbs is wide, so the opening view is
  zoomed out; zoom or click an orb to read its claims.

## [v4.0.0] — 2026-11-13 — FROZEN

### Good

- serve_v4.py (SPEC_V4.md 4.0.0): a "Keywords" choice in the field's
  "Cluster by" bar. A subject (a repo) is the unit: all its claims stay
  together, and subjects group by their claims' own words (stemmed, stop
  words dropped, words in more than 30% of subjects skipped), so repos
  group without tags: ledger, capsule, attestation, ed25519, weight,
  block, lllm. Open `#mode:KEYWORDS` to start there. 39/39 tests pass.
  Built as a layer: serve.py, serve_v2.py, serve_v3.py and static/view/
  untouched. Frozen at 4.0.0 (James: "freeze commmit and push", 2026-11-13); laptop run, S24 run
  still to be confirmed.

### Bad

- Clustering is greedy, one cluster per subject: a subject that fits two
  topics shows in the first and is linked to the other.
- In "Tags" mode, 24 subjects make 24 small clusters packed close round
  the centre, with labels overlapping until you zoom; the spacing is in
  the frozen frontend.

### Ugly

- v4 restates v1's render_page (about ten lines) because v1 hardcodes
  `MODES = {}`.

## [v3.0.0] — 2026-11-13 — FROZEN

### Good

- `SPEC_V3.md`, `test_serve_v3.py` (4 tests, run red first) and `serve_v3.py`: every time the field receives is an ISO 8601 string. Fixes the field drawing nothing once any claim was attested (`TypeError: t.slice is not a function`): P9 SPEC_V3 §3 stores the seal time in epoch seconds and v2 passed the number through. Checked in headless Edge: no console errors, 8 cubes drawn, the attested claim's green strand shown. 33/33 pass.
- Built as a layer: serve.py, serve_v2.py and static/view/ untouched. Frozen at 3.0.0 (James: "freeze", 2026-11-13); confirmed on the S24 by James, 2026-11-13.

### Bad

- v2 (frozen) still breaks the field on any attested claim; run serve_v3. v2's tests checked the API, never the page's JavaScript; v3's test 4 runs the frontend's own stampsOf in node.

### Ugly

- (none)

## [v2.0.0] — 2026-11-13 — FROZEN

### Good

- `SPEC_V2.md`, `test_substrate_v2.py` (5 tests, run red first) and `serve_v2.py`: reads P9 through substrate_v3's read-only API with verify-on-read. Unverified claims are not drawn (named on stderr, counted in `/api/health`); unverified evidence never lights the glow. v1's adapter, page, static serving and 405 rules reused. 29/29 pass.
- Attestations follow P9 SPEC_V3 §3, so a Cockpit v1.1 `approve` lights the gold glow and a later `refuse` shows as retracted.
- Built on James's delegation ("fix all 11 issues"). Frozen at 2.0.0 on James's sign-off ("freeze all", 2026-11-13).

### Bad

- Frozen on the laptop run alone (2026-11-13); confirmed on the S24 by James, 2026-11-13.

### Ugly

- serve_v2 copies v1's 20-line `_route` to swap in the verified readers, because v1 calls its own module functions. Safe while serve.py is frozen.

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
