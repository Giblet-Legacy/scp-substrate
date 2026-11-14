# SPEC V7 — scp-substrate (Tier 1: SCP Substrate, the field on a phone)

SPEC_V7.md — specification for serve_v7.py and static/view_v3, the layer above SCP Substrate v6.

Function:
    James (2026-11-14) asked for screenshots and a report, then said yes
    to fixing what they found. Two faults in v6's page (view_v2): a
    link that opens the field on one orb (`#entity:<id>`) crashed the
    page blank; and orb names were drawn on top of each other wherever
    orbs lined up, worst on a phone, where most names were unreadable.
    v7 serves the page from static/view_v3, a copy of view_v2 with both
    fixed. Where this document is silent,
    SPEC_V6.md applies. serve.py, serve_v2–v6, static/view/ and
    static/view_v2/ are not edited.

Tier:      Tier 1 — Consumer (The Memory)
Depends:   serve_v6.py (6.0.0)
Version:   SPEC 7.0.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. Opening on one orb

`#entity:<id>` (a subject or entity in HUBS) opens the field on that
orb, as if it had been clicked: the camera on it, its panel open. The
frozen frontend switched to an "Entities" mode for this; v5 and later
do not send that mode, so view_v2 failed with "Cannot read properties
of undefined (reading 'clusters')" and drew nothing. view_v3 uses the
"Entities" mode only when the server sends it, otherwise it opens the
orb in the current view. An unknown id opens the field as normal.

## 2. Phone width

No change. The report said the bars ran off the right edge at phone
width; that came from the screenshot, not the page (headless Edge will
not make a window narrower than about 500 px, so the 412 px shot was a
496 px page cut short). Measured in a true 412 px frame, nothing runs
off the edge. The test below keeps it that way.

## 3. Each orb's name readable

Your name (at the centre) and the group titles are placed first; orb
names are then drawn nearest first. A name whose box would overlap a
name already placed is left out of that frame, unless it is the orb you
are in. The orbs keep moving, so a hidden name comes back as soon as
its orb is clear. `window.cubeField.named()` returns the boxes drawn in
the last frame (for tests).

## 4. Serving

`python serve_v7.py [--db PATH] [--port N] [--quiet]`, as v6.

## 5. Tests (test_serve_v7.py)

- The page is built from view_v3; its script parses (if node);
  static/view is unchanged; `/api/claims` is v3's.
- In a headless browser (Edge or Chrome; skipped if neither is
  installed):
  - `#entity:<id>` opens the orb's panel with no script error;
  - at 412 × 915 no visible element ends past the right edge, unless it
    is inside a box that scrolls sideways;
  - at 1400 × 900 no two drawn orb names overlap, and at least half of
    the orbs are named; at 412 × 915 (in a frame) no two overlap.

---

## Document control

- **SPEC 7.0.0** — 2026-11-14, by the VS Code AI on James's delegation
  ("take a bunch of screenshots and report", then "yes" to the fixes).
