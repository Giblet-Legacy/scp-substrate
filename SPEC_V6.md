# SPEC V6 — scp-substrate (Tier 1: SCP Substrate, dependencies as your links)

SPEC_V6.md — specification for serve_v6.py, the layer above SCP Substrate v5.

Function:
    James (2026-11-14), on clicking a dependency thread: "links together
    are weak". v5 sent each "depends on" claim to the frozen frontend
    as a word-match ("lens") link: faint, shown only in the opening
    view, and explained as "a match on words, so it can be a
    coincidence". v6 sends it as the frontend's **neighbour** link,
    the kind for links the owner made: the strongest thread (amber,
    with a pulse), drawn in every view, explained as "You linked
    these: … depends on …. The reason given: <the claim's FACT>".
    Where this document is silent, SPEC_V5.md applies. serve.py,
    serve_v2–v5 and static/view/ are not edited.

Tier:      Tier 1 — Consumer (The Memory)
Depends:   serve_v5.py (5.0.0)
Version:   SPEC 6.0.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. Dependency links as neighbours

For each dependency claim (SPEC_V5 §5) with target subject T, on the
dependency claim's cube:

- `neighbours` gains the id of T's first claim (once);
- `link_words[<that id>] = {"word": "depends on", "from": <this claim's id>}`;
- `link_reasons[<that id>]` = the claim's FACT text, if it has one,
  without a trailing full stop (the frontend adds one).

Cubes without dependencies keep `neighbours: []` and get empty
`link_words` and `link_reasons`.

## 2. Modes

v6 does not send `MODES.ALL`, so the field opens on its own "Tags"
view, where the hubs (SPEC_V5 §4) still gather each subject's claims
round its orb. `MODES.KEYWORDS` (v4) stays. Neighbour links are drawn
in every view.

## 3. The frontend layer: static/view_v2

James (2026-11-14): "the subjects seem to only be rotating flat … move
freely and let natural clusters form … 360 degree movement". The frozen
frontend pins orbs to a flat ring. view_v2 is a copy of static/view
(which is not edited) with three changes:

- **Orbs move freely in 3D** (view_field_hubs.js). Each orb is a body:
  it starts on a sphere (golden angle) of radius
  `ORBIT_R = max(520, √n × 260)`; every frame, orbs repel
  (`0.12·ORBIT_R³ / d²`), a spring holds each near `ORBIT_R` from you,
  each pair of orbs joined by your links is a spring (rest
  `0.45·ORBIT_R`), a slow drift keeps them moving, velocity is damped
  (`e^(−2.5·dt)`, capped at 320/s), and the whole system turns at
  0.04 rad/s on a tilted axis. 600 steps run before the first frame,
  so the clusters have already formed. Motion stops while you are
  inside an orb. The camera frames `1.6·ORBIT_R + 260`.
- **Your links at full strength**: neighbour threads in amber at a fixed
  opacity of 0.62 and width 1.3, whatever the zoom.
- **Each orb named once**: an orb's claim cluster is not labelled again
  unless you are inside it.

Checked in a standalone simulation with the 23 repos and 45 dependency
links: orbs spread from −1939 to +1478 in height (not a disc); linked
orbs settle about half as far apart as unlinked ones (1164 vs 2246);
the closest pair stays 760 apart; they keep moving at about 50/s.

## 4. Serving

`python serve_v6.py [--db PATH] [--port N] [--quiet]`, as v5.

## 5. Tests (test_serve_v6.py)

- Neighbours, words and reasons on dependency cubes only; self and
  unknown targets give none; no duplicates.
- `modes` has KEYWORDS and no ALL.
- The page injects the neighbours and is built from view_v2; its
  script parses (if node); static/view is unchanged; `/api/claims` is v3's.

---

## Document control

- **SPEC 6.0.0** — 2026-11-14, by the VS Code AI on James's delegation.
