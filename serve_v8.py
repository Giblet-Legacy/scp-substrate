"""
serve_v8.py — SCP Substrate v8, you at the centre of what is yours

Function:
    The entry point from v8 (SPEC_V8.md). As v7, except that a claim
    about the person ("James Gilbert is building SCPBot") is shown in
    the orb of its object, so each of the person's projects is an orb
    round them with its claims inside, and no orb is named after the
    person, who is the centre. A project that is also a registered
    subject is one orb. Your orbs are pink and held close round you
    (static/view_v4, SPEC_V8 §2). Only the page changes; the signed claims and
    the JSON API are v7's. serve.py, serve_v2–v7 and static/view/,
    view_v2/, view_v3/ are not edited.

Public API:
    1. orbits(cubes, found) -> (hubs, found, user)
    2. page(db_path) -> str
    3. read_claims, read_claim, link_dependencies, modes (v7's);
       OrbitHandlerV8, make_server, main

Internal helpers:
    4. _about_you — rewrite the page's copies of claims about the person
    5. _section   — the section a claim about the person belongs to
    6. _sections  — copy each claim's own `section` field onto its cube

Tier:      Tier 1 — Consumer (The Memory)
Depends:   serve_v7.py (7.0.0)
Spec:      SPEC_V8.md 8.0.0 (over SPEC_V7.md 7.0.0)
Version:   8.0.0 (frozen 2026-11-16)
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)
"""

import argparse
import os
import re
import sqlite3
import sys
from http.server import ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import serve as _v1  # noqa: E402
import serve_v5 as _v5  # noqa: E402
import serve_v7 as _v7  # noqa: E402

read_claims = _v7.read_claims
read_claim = _v7.read_claim
link_dependencies = _v7.link_dependencies
modes = _v7.modes
DEFAULT_PORT, HOST = _v7.DEFAULT_PORT, _v7.HOST
STATIC_V4 = _v7.STATIC_V3.parent / "view_v4"  # SPEC_V8 §2: yours pink and close
_CAPSULE = re.compile(r"Identity capsule [^,\s]+, ([^.|]+)\.")
_ABOUT = {"entity", "origin", "ethos", "can_build", "how_he_works", "how_he_codes"}


# ---------------------------------------------------------------------------
# 4. _about_you
#    SPEC_V8 §1. Mutates the page's cubes only.
# ---------------------------------------------------------------------------
def _about_you(cubes, found):
    person = next((e for e in found["entities"] if _v5._key(e.get("kind")) == "person" and e.get("name")), None)
    if person is None:
        return
    me = _v5._key(person["name"])
    registered = {_v5._key(s.get("name")) for s in found["subjects"]}
    for c in cubes:
        obj = c.get("object")
        if _v5._key(c.get("subject")) != me or not isinstance(obj, str) or not obj.strip():
            continue
        c["about_you"] = True
        if _v5._key(obj) in registered:  # §1: a project that is a repo joins the repo's orb
            c["subject"], c["object"] = obj.strip(), person["name"]
        else:  # §1.1: grouped by section, the project as a part
            c["subject"], c["object"], c["_part"] = _section(c, person["name"]), obj.strip(), obj.strip()


# ---------------------------------------------------------------------------
# 6. _sections
#    SPEC_V8 §1.1: a claim's own `section` field, read from P9 as signed
#    (the cubes carry only subject, predicate, object and faces).
# ---------------------------------------------------------------------------
def _sections(cubes, db_path):
    p9 = _v5._p9()
    own = {r["claim_id"]: (r["capsule"] or {}).get("section") for r in p9.list_claims(db_path)}
    for c in cubes:
        if isinstance(own.get(c.get("id")), str):
            c["section"] = own[c["id"]]


# ---------------------------------------------------------------------------
# 5. _section
#    SPEC_V8 §1.1: from the claim's CONTEXT.
# ---------------------------------------------------------------------------
def _section(cube, name):
    own = cube.get("section")
    if isinstance(own, str) and own.strip():  # the claim names its section itself
        section = own.strip()
        return f"about {name}" if section in _ABOUT else section
    context = ((cube.get("faces") or {}).get("CONTEXT") or {}).get("content") or ""
    m = _CAPSULE.search(context)
    if not m:
        return "other"
    section = m.group(1).strip()
    return f"about {name}" if section in _ABOUT else section


# ---------------------------------------------------------------------------
# 1. orbits
#    Claims about the person first, then v5's orbits; sections get
#    their own ids, parts and `yours` (SPEC_V8 §1.1).
# ---------------------------------------------------------------------------
def orbits(cubes, found):
    _about_you(cubes, found)
    hubs, found, user = _v5.orbits(cubes, found)
    by_id = {h["id"]: h for h in hubs}
    renamed = {}
    for c in cubes:
        part = c.pop("_part", None)
        if part is None or not c.get("hub"):
            continue
        old = c["hub"]["entity"]
        h = by_id[old]
        if old not in renamed:  # a section's orb: its own id and kind
            renamed[old] = f"section:{_v5._key(h['name'])}"
            h.update(id=renamed[old], kind="subject · section", yours=True)
        sid = renamed[old]
        pid = f"part:{_v5._key(h['name'])}/{_v5._key(part)}"
        if all(p["id"] != pid for p in h["parts"]):
            role = " ".join(str(c.get("predicate") or "").split()) or "about you"
            h["parts"].append({"id": pid, "name": part, "role": role})  # the panel shows it
        c["hub"] = {"entity": sid, "part": pid}
        c["subjects"] = [sid]
    for c in cubes:  # other cubes already in a renamed orb (none expected) follow it
        if c.get("hub") and c["hub"]["entity"] in renamed:
            c["hub"]["entity"] = renamed[c["hub"]["entity"]]
            c["subjects"] = [c["hub"]["entity"]]
    for e in found["entities"]:
        e["parts"] = [renamed.get(x, x) for x in e["parts"]]
    for s in found["subjects"]:
        if s["id"] in renamed:
            s.update(id=renamed[s["id"]], kind="subject · section")
    return hubs, found, user


# ---------------------------------------------------------------------------
# 2. page
#    v7's page, with claims about the person in their objects' orbs,
#    from view_v4.
# ---------------------------------------------------------------------------
def page(db_path):
    cubes = read_claims(db_path)
    _sections(cubes, db_path)
    hubs, found, user = orbits(cubes, _v5.things(db_path))
    link_dependencies(cubes)
    return _v5.render_page(cubes, modes(cubes), hubs, found, user, static_dir=STATIC_V4)


# ---------------------------------------------------------------------------
# 3. OrbitHandlerV8, make_server, main
# ---------------------------------------------------------------------------
class OrbitHandlerV8(_v7.OrbitHandlerV7):

    # 3.1 _route — the v8 page; everything else v7's.
    def _route(self, head_only):
        if unquote(urlsplit(self.path).path) in ("/", "/index.html"):
            try:
                html = page(self.db_path)
            except (sqlite3.Error, FileNotFoundError) as e:
                return self._json(503, {"error": "database unavailable", "detail": str(e)}, head_only)
            return self._send(200, html, _v1.TYPES[".html"], head_only)
        return super()._route(head_only)


def make_server(db_path, port=DEFAULT_PORT, quiet=False):
    handler = type("BoundOrbitHandlerV8", (OrbitHandlerV8,), {"db_path": db_path, "quiet": quiet})
    return ThreadingHTTPServer((HOST, port), handler)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only, verified SCP Substrate viewer (v8: you at the centre).")
    parser.add_argument("--db", help="P9 SQLite database (default: $FORGE_HOME/forge.db, else ~/.forge/forge.db)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"port on {HOST} (default {DEFAULT_PORT})")
    parser.add_argument("--quiet", action="store_true", help="do not log each request")
    args = parser.parse_args(argv)
    db_path = _v1.resolve_db_path(args.db)
    server = make_server(db_path, args.port, quiet=args.quiet)
    print(f"Serving {db_path} read-only and verified on http://{HOST}:{server.server_address[1]}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
