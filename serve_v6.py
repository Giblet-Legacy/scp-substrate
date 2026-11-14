"""
serve_v6.py — SCP Substrate v6, "depends on" claims drawn as your own links

Function:
    The entry point from v6 (SPEC_V6.md). As v5 (you at the centre, each
    subject an orb with its claims round it), but each "depends on"
    claim becomes the frozen frontend's neighbour link to the target
    subject: the strongest thread, drawn in every view, explained as
    "You linked these: … depends on …" with the claim's FACT as the
    reason. No server "All lenses" view: the field opens on "Tags".
    The page comes from static/view_v2 (a copy of the frozen static/view):
    orbs move freely in 3D, pushed apart, held at orbit distance and
    pulled together by your links, so natural clusters form; your links
    are drawn at full strength; each orb is named once.
    serve.py, serve_v2–v5 and static/view/ are not edited.

Public API:
    1. link_dependencies(cubes) -> cubes   — neighbours, link_words, link_reasons
    2. modes(cubes) -> {"KEYWORDS"}
    3. page(db_path) -> str
    4. read_claims, read_claim (v3's); OrbitHandlerV6, make_server, main

Tier:      Tier 1 — Consumer (The Memory)
Depends:   serve_v5.py (5.0.0)
Spec:      SPEC_V6.md 6.0.0 (over SPEC_V5.md 5.0.0)
Version:   6.0.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)
"""

import argparse
import os
import sqlite3
import sys
from http.server import ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import serve as _v1  # noqa: E402
import serve_v4 as _v4  # noqa: E402
import serve_v5 as _v5  # noqa: E402

read_claims = _v5.read_claims
read_claim = _v5.read_claim
DEFAULT_PORT, HOST = _v5.DEFAULT_PORT, _v5.HOST
STATIC_V2 = _v1.STATIC_DIR.parent / "view_v2"  # SPEC_V6 §3: orbs that move freely in 3D


# ---------------------------------------------------------------------------
# 1. link_dependencies
#    SPEC_V6 §1. Idempotent.
# ---------------------------------------------------------------------------
def link_dependencies(cubes):
    first = {}
    for c in cubes:
        first.setdefault(_v5._key(c.get("subject")), c["id"])
        c.setdefault("link_words", {})
        c.setdefault("link_reasons", {})
        c["neighbours"] = list(c.get("neighbours") or [])
    for link in _v5.dependency_links(cubes):
        c = next(x for x in cubes if x["id"] == link["a"])
        target = link["b"]
        if target not in c["neighbours"]:
            c["neighbours"].append(target)
        c["link_words"][target] = {"word": _v5.DEPENDS, "from": c["id"]}
        fact = (c.get("faces") or {}).get("FACT")
        if fact and fact.get("content"):
            c["link_reasons"][target] = fact["content"].strip().rstrip(".")  # the frontend adds its own full stop
    return cubes


# ---------------------------------------------------------------------------
# 2. modes
#    SPEC_V6 §2: v4's KEYWORDS only.
# ---------------------------------------------------------------------------
def modes(cubes):
    return _v4.modes(cubes)


# ---------------------------------------------------------------------------
# 3. page
# ---------------------------------------------------------------------------
def page(db_path):
    cubes = read_claims(db_path)
    hubs, found, user = _v5.orbits(cubes, _v5.things(db_path))
    link_dependencies(cubes)
    return _v5.render_page(cubes, modes(cubes), hubs, found, user, static_dir=STATIC_V2)


# ---------------------------------------------------------------------------
# 4. OrbitHandlerV6, make_server, main
# ---------------------------------------------------------------------------
class OrbitHandlerV6(_v5.OrbitHandler):

    # 4.1 _route — the v6 page; everything else v5's.
    def _route(self, head_only):
        if unquote(urlsplit(self.path).path) in ("/", "/index.html"):
            try:
                html = page(self.db_path)
            except (sqlite3.Error, FileNotFoundError) as e:
                return self._json(503, {"error": "database unavailable", "detail": str(e)}, head_only)
            return self._send(200, html, _v1.TYPES[".html"], head_only)
        return super()._route(head_only)


def make_server(db_path, port=DEFAULT_PORT, quiet=False):
    handler = type("BoundOrbitHandlerV6", (OrbitHandlerV6,), {"db_path": db_path, "quiet": quiet})
    return ThreadingHTTPServer((HOST, port), handler)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only, verified SCP Substrate viewer (v6).")
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
