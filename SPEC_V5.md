# SPEC V5 — scp-substrate (Tier 1: SCP Substrate, subjects orbit you)

SPEC_V5.md — specification for serve_v5.py, the layer above SCP Substrate v4.0.0.

Function:
    Draws James's model in the field: he (an entity) is the centre;
    each subject (a repo) is its own orb orbiting him, with its claims
    orbiting the orb; subjects that depend on each other are joined by
    threads. Uses the frozen frontend's hubs (HUBS, THINGS) and a
    server mode (MODES.ALL); static/view/ is not edited. serve.py and
    serve_v2–v4 are not edited. Where this document is silent,
    SPEC_V4.md applies.

Tier:      Tier 1 — Consumer (The Memory)
Depends:   serve_v4.py (4.0.0), P9 substrate_v4 (4.0.0, read-only)
Version:   SPEC 5.0.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. Why v5

James (2026-11-13): "i am an entity … hal layer is a subject … the
subjects need their own orb with their claims orbiting them as the
subject orbits me … there would be connections between each other as
they are part of the same system and rely on each other."

## 2. Things

`things(db_path)` reads P9 v4 read-only: `{"entities": [...],
"subjects": [...]}` (thing rows). A database made before P9 v4 has
none.

## 3. The centre

The **person** is the first registered entity whose kind is "person"
(case-insensitive). USER (the centre's name) is the person's name, else
"You".

## 4. Orbs (HUBS)

One hub per distinct claim subject (by P9 v4 name key), in the order
of each subject's first claim:

- `id`: the registered subject's id, or `subject:<key>` if the name is
  not registered (claims need no registration).
- `name`: the registered name, else the first claim's subject text.
- `kind`: "subject" plus " · <kind>" when registered with a kind.
- `builders`: [the person's name] when there is a person, else [].
- `parts`: [], `nets`: [].

Every cube gets `hub = {"entity": <hub id>, "part": null}`,
`subjects = [<hub id>]` and `entities = []`, so the frontend gathers a
subject's claims round its orb and draws the orb on a strand from the
centre.

## 5. Connections

A **dependency claim** is an active claim whose predicate, normalised,
is "depends on" and whose object names another subject in the field.
Each gives one link `{a: <the claim>, b: <the target subject's first
claim>, lens: "CONTEXT", term: "depends on"}`. Self-references and
unknown targets give none.

## 6. MODES and THINGS

- `MODES.ALL` (the frontend's opening mode): one cluster per subject
  (its claims) and the dependency links. `MODES.KEYWORDS` is v4's.
- `THINGS`: `entities` — each registered entity as `{id, name, kind,
  parts, links: [], you}`, where the person's `parts` are every hub id
  and `you` is true for the person only; `subjects` — every hub as
  `{id, name, kind, used_by}` (`used_by` = [person's name] or []).

`render_page(cubes, modes, hubs, things, user)` fills all six data
slots exactly as v1 fills them. `python serve_v5.py [--db PATH] [--port N]
[--quiet]`; `--quiet` stops the per-request log (The Legacy's boot.py uses it).

## 7. Tests (test_serve_v5.py)

- One hub per subject, first-claim order; registered ids and kinds;
  unregistered `subject:<key>` ids; every cube placed.
- USER is the person's name, else "You"; builders follow.
- Dependency links from "depends on" claims; unknown and self targets
  ignored.
- The page injects HUBS, THINGS, USER and MODES (ALL, KEYWORDS); no
  numeric times; the injected data parses as JavaScript (if node).
- `/api/claims` is v3's.

---

## Document control

- **SPEC 5.0.0** — 2026-11-13, by the VS Code AI on James's delegation.
