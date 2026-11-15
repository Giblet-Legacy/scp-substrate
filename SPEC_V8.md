# SPEC V8 — scp-substrate (Tier 1: SCP Substrate, you at the centre of what is yours)

SPEC_V8.md — specification for serve_v8.py, the layer above SCP Substrate v7.

Function:
    James (2026-11-15): "i should be at the centre all the stuff about
    me should be as he first entity me and all my subjects and claims".
    His identity went into memory as claims whose subject is his own
    name ("James Gilbert is building SCPBot"). v7 makes one orb per
    claim subject, so all of them landed in a single "James Gilbert"
    orb circling him, and none of his projects had an orb. v8 shows a
    claim about the person in the orb of its object: SCPBot becomes an
    orb round him with that claim inside it. Only the page changes;
    the signed claims and the JSON API are untouched. Where this
    document is silent, SPEC_V7.md applies. serve.py, serve_v2–v7 and
    static/view/, view_v2/, view_v3/ are not edited.

Tier:      Tier 1 — Consumer (The Memory)
Depends:   serve_v7.py (7.0.0)
Version:   SPEC 8.0.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. Claims about you

The person is the first P9 v4 entity of kind "person" (as SPEC_V5 §4).
For each cube on the page whose subject equals the person's name
(ignoring case and surrounding spaces) and whose object is a non-empty
string:

- its `subject` becomes the object, stripped (so it joins, or makes,
  the orb of that name; a registered subject of the same name keeps
  its id and kind, so a project that is also a repo is one orb);
- its `object` becomes the person's name;
- it gains `about_you: true`; `predicate` and everything else are kept.

Then v7's orbits run. Without a person, or for claims about anyone
else, nothing changes. No orb is named after the person: the person is
the centre.

### 1.1 Sections, with your projects as their parts

James (2026-11-15, after screenshots: 78 one-claim orbs, most unnamed):
"yes build it". A claim about the person whose object is **not** a
registered subject is grouped by the section its CONTEXT names:

- A claim may name its section itself: a non-empty string `section`
  field on the signed capsule (read from P9, as signed) is used as is.
  Otherwise its CONTEXT is read, as below, so the 83 identity claims
  already signed (2026-11-15) need no re-signing. New claims about the
  person should carry `section`; the CONTEXT rule is the fallback.
- CONTEXT containing `Identity capsule <id>, <section>.` gives `<section>`, where
  `entity`, `origin`, `ethos`, `can_build`, `how_he_works` and
  `how_he_codes` (the capsule's sections about the person) all give
  `about <person's name>`; any other CONTEXT gives `other`.
- The cube's `subject` becomes the section and its `object` the
  project (the claim's object); its hub is
  `{"entity": <the section's orb id>, "part": "part:<section key>/<project key>"}`.
- The section's orb (id `section:<section key>`, kind
  `subject · section`) has one part per project, `{id, name, role}`
  (role: the claim's predicate, such as "is building", else
  "about you"; the panel shows it), in the
  order of each project's first claim, and `yours: true`.

A claim about the person whose object **is** a registered subject (a
project that is also a repo) joins that subject's orb, as in §1; that
orb is not marked yours (it stays on the outer shell with the repos).

## 2. The frontend layer: static/view_v4

James (2026-11-15): "my stuff should be a different coulr and tighter
to the centre". view_v4 is a copy of view_v3 (not edited) in which an
orb with `yours: true`:

- is drawn pink (`255,120,200`): its dot, its glow, its strand from you,
  its parts and its claims' clusters, a colour no face, link or glow
  already uses;
- is pulled to half the orbit radius (`0.5·ORBIT_R`, pull 2.4 instead of
  1.2), starts there on the golden-angle sphere, and is held between
  0.4 and 0.6 of it every step; other orbs are pulled to `ORBIT_R`
  (pull 3.0) and held between 0.9 and 1.1 of it, so the repos stay on
  the outer shell. Measured on the real memory before the hold: the
  orbs pushing apart carried the sections out to 1290–1390 (0.86–0.93
  of the radius) and the repos to 2130;
- has its parts on a ring of radius `max(190, 60 + 22·parts)`, and
  inside it (the orb you have opened) its parts are named, each keeping
  clear of every other name as orb names do (v7).

Everywhere:

- **You stay green.** The centre is drawn again after the orbs and the
  strands, so the pink never covers it.
- **The camera fits what is there.** The opening view frames the orbs
  where they settled (furthest orb plus its part ring, ×0.85, +80: at the default
  zoom the screen's shorter side shows ±0.53 of the camera distance,
  so the furthest orb and its name fit, a phone's narrow width
  included)
  instead of a fixed `1.6·ORBIT_R + 260`, so the field fills the
  screen, a phone's included.

The key gains "Pink orbs: yours, close round you".

## 3. Only the page

The rewrite is on the copies the page is built from. `/api/claims` and
`/api/claim/<id>` are v7's (v3's), and show each claim as signed.

## 4. Serving

`python serve_v8.py [--db PATH] [--port N] [--quiet]`, as v7. The page
is built from static/view_v4.

## 5. Tests (test_serve_v8.py)

- orbits: a claim about the person lands in its object's orb; no orb is
  named after the person; a project that is also a registered subject
  is one orb with the registered id; claims about others are unchanged;
  no person, no change; `yours` on exactly the orbs holding claims
  about the person.
- sections: projects become parts of their section's orb; the
  capsule's own sections gather in "about <name>"; anything else in
  "other"; a project that is a repo stays in the repo's orb; a
  `section` field on the claim wins over its CONTEXT.
- view_v4 differs from view_v3 only in view_field_hubs.js,
  view_field_world.js, view_field_draw.js and view_bar.js; view_v3 is
  unchanged; the page is built from view_v4; the page script parses.
- the page names the project orbs and not the person as an orb; the
  API still returns the signed subject.

---

## Document control

- **SPEC 8.0.0** — 2026-11-15, by the VS Code AI on James's delegation.
