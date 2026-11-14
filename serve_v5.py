"""
serve_v5.py — SCP Substrate v5, subjects orbit you and their claims orbit them

Function:
    The entry point from v5 (SPEC_V5.md). Reads as v3 (verified,
    read-only) and reads P9 v4's entities and subjects read-only, then
    feeds the frozen frontend's hubs: the person entity is the centre,
    each subject is an orb on a strand from the centre with its claims
    gathered round it, and "depends on" claims become threads between
    subjects (MODES.ALL, the opening view). "Keywords" stays (v4).
    serve.py, serve_v2–v4 and static/view/ are not edited.

Public API:
    1. things(db_path) -> {"entities", "subjects"}
    2. orbits(cubes, things) -> (hubs, things_json, user)   — places every cube
    3. dependency_links(cubes) -> list
    4. modes(cubes) -> {"ALL", "KEYWORDS"}
    5. render_page(cubes, modes, hubs, things, user) -> str
    6. read_claims, read_claim (v3's, re-exported)
    7. OrbitHandler, make_server(db_path, port=8085, quiet=False), main(argv=None)

Internal helpers:
    8. _key       — a name's P9 v4 key
    9. _p9        — P9 substrate_v4 from ../substrate-layer

Tier:      Tier 1 — Consumer (The Memory)
Depends:   serve_v4.py (4.0.0), P9 substrate_v4 (4.0.0, read-only)
Spec:      SPEC_V5.md 5.0.0 (over SPEC_V4.md 4.0.0)
Version:   5.0.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)
"""

import argparse
import importlib
import os
import re
import sqlite3
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import serve as _v1  # noqa: E402
import serve_v4 as _v4  # noqa: E402

read_claims = _v4.read_claims
read_claim = _v4.read_claim
STATIC_DIR = _v1.STATIC_DIR
DEFAULT_PORT = _v1.DEFAULT_PORT
HOST = _v1.HOST
DEPENDS = "depends on"
_P9 = []


# ---------------------------------------------------------------------------
# 8. _key
# ---------------------------------------------------------------------------
def _key(name):
    return name.strip().casefold() if isinstance(name, str) else ""


# ---------------------------------------------------------------------------
# 9. _p9
# ---------------------------------------------------------------------------
def _p9():
    if not _P9:
        path = os.path.abspath(os.path.join(_HERE, "..", "substrate-layer"))
        if path not in sys.path:
            sys.path.insert(0, path)
        _P9.append(importlib.import_module("substrate_v4"))
    return _P9[0]


# ---------------------------------------------------------------------------
# 1. things
#    SPEC_V5 §2: P9 v4, read-only, verified rows.
# ---------------------------------------------------------------------------
def things(db_path):
    p9 = _p9()
    return {"entities": p9.list_entities(db_path, verify=True), "subjects": p9.list_subjects(db_path, verify=True)}


# ---------------------------------------------------------------------------
# 2. orbits
#    SPEC_V5 §3, §4, §6. Mutates each cube (hub, subjects, entities).
# ---------------------------------------------------------------------------
def orbits(cubes, found):
    person = next((e for e in found["entities"] if _key(e.get("kind")) == "person" and e.get("name")), None)
    user = person["name"] if person else "You"
    builders = [user] if person else []
    registered = {_key(s["name"]): s for s in found["subjects"] if s.get("name")}
    hubs, hub_of = [], {}
    for c in cubes:
        k = _key(c.get("subject"))
        if not k:
            continue
        if k not in hub_of:
            reg = registered.get(k)
            kind = "subject" + (f" · {reg['kind']}" if reg and reg.get("kind") else "")
            hub = {"id": reg["id"] if reg else f"subject:{k}", "name": reg["name"] if reg else c["subject"].strip(),
                   "kind": kind, "builders": list(builders), "parts": [], "nets": []}
            hub_of[k] = hub
            hubs.append(hub)
        c["hub"] = {"entity": hub_of[k]["id"], "part": None}
        c["subjects"] = [hub_of[k]["id"]]
        c["entities"] = []
    for c in cubes:
        c.setdefault("subjects", [])
        c.setdefault("entities", [])
    entities = [{"id": e["id"], "name": e["name"], "kind": e.get("kind"),
                 "parts": [h["id"] for h in hubs] if e is person else [], "links": [], "you": e is person}
                for e in found["entities"] if e.get("name")]
    subjects = [{"id": h["id"], "name": h["name"], "kind": h["kind"], "used_by": list(builders)} for h in hubs]
    return hubs, {"entities": entities, "subjects": subjects}, user


# ---------------------------------------------------------------------------
# 3. dependency_links
#    SPEC_V5 §5.
# ---------------------------------------------------------------------------
def dependency_links(cubes):
    first = {}
    for c in cubes:
        first.setdefault(_key(c.get("subject")), c["id"])
    links = []
    for c in cubes:
        predicate = " ".join(str(c.get("predicate") or "").lower().split())
        if predicate != DEPENDS:
            continue
        own, target = _key(c.get("subject")), _key(c.get("object"))
        if target and target != own and target in first:
            links.append({"a": c["id"], "b": first[target], "lens": "CONTEXT", "term": DEPENDS})
    return links


# ---------------------------------------------------------------------------
# 4. modes
#    SPEC_V5 §6: ALL (one cluster per subject, dependency links) and v4's KEYWORDS.
# ---------------------------------------------------------------------------
def modes(cubes):
    clusters = {}
    for c in cubes:
        clusters.setdefault(_key(c.get("subject")) or c["id"], {"name": c.get("subject") or "no subject", "members": []})
        clusters[_key(c.get("subject")) or c["id"]]["members"].append(c["id"])
    out = _v4.modes(cubes)
    out["ALL"] = {"clusters": list(clusters.values()), "links": dependency_links(cubes)}
    return out


# ---------------------------------------------------------------------------
# 5. render_page
#    v1's fill, with every data slot supplied.
# ---------------------------------------------------------------------------
def render_page(cubes, modes_, hubs, things_, user, static_dir=STATIC_DIR):
    read = lambda name: (Path(static_dir) / name).read_text(encoding="utf-8")  # noqa: E731
    data = {"CUBES": _v1.safe_json(cubes), "MODES": _v1.safe_json(modes_), "USER": _v1.safe_json(user),
            "HUBS": _v1.safe_json(hubs), "THINGS": _v1.safe_json(things_), "LENSES": _v1.safe_json(list(_v1.FACES))}
    grid = re.sub(r'/\*(CUBES|MODES|USER|HUBS|THINGS|LENSES)\*/(\[[^\]]*\]|\{\}|"[^"]*")',
                  lambda m: data[m.group(1)], read("view_grid.js"))
    field = "(() => {\n" + "\n".join(read(f"view_field_{p}.js") for p in _v1.FIELD_PARTS) + "\n})();\n"
    parts = {"STYLE": read("view_style.css"), "GRID": grid, "FIELD": field, "BAR": read("view_bar.js")}
    return re.sub(r"/\*(STYLE|GRID|FIELD|BAR)\*/", lambda m: parts[m.group(1)], read("view_template.html"))


# ---------------------------------------------------------------------------
# 7. OrbitHandler, make_server, main
# ---------------------------------------------------------------------------
class OrbitHandler(_v4.KeywordHandler):

    # 7.1 _route — the orbit page; everything else v4's.
    def _route(self, head_only):
        if unquote(urlsplit(self.path).path) in ("/", "/index.html"):
            try:
                cubes = read_claims(self.db_path)
                hubs, found, user = orbits(cubes, things(self.db_path))
            except (sqlite3.Error, FileNotFoundError) as e:
                return self._json(503, {"error": "database unavailable", "detail": str(e)}, head_only)
            return self._send(200, render_page(cubes, modes(cubes), hubs, found, user), _v1.TYPES[".html"], head_only)
        return super()._route(head_only)


def make_server(db_path, port=DEFAULT_PORT, quiet=False):
    handler = type("BoundOrbitHandler", (OrbitHandler,), {"db_path": db_path, "quiet": quiet})
    return ThreadingHTTPServer((HOST, port), handler)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only, verified SCP Substrate viewer (v5: subjects orbit you).")
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
