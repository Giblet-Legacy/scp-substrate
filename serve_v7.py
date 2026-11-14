"""
serve_v7.py — SCP Substrate v7, the field on a phone

Function:
    The entry point from v7 (SPEC_V7.md). As v6 (you at the centre, each
    subject an orb moving in 3D with its claims round it, "depends on"
    claims as your own links), with the page from static/view_v3: a link
    to one orb (#entity:<id>) opens it instead of crashing, nothing runs
    off the right edge at phone width, and orb names never overlap.
    serve.py, serve_v2–v6, static/view/ and static/view_v2/ are not edited.

Public API:
    1. page(db_path) -> str
    2. read_claims, read_claim, link_dependencies, modes (v6's);
       OrbitHandlerV7, make_server, main

Tier:      Tier 1 — Consumer (The Memory)
Depends:   serve_v6.py (6.0.0)
Spec:      SPEC_V7.md 7.0.0 (over SPEC_V6.md 6.0.0)
Version:   7.0.0
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
import serve_v5 as _v5  # noqa: E402
import serve_v6 as _v6  # noqa: E402

read_claims = _v6.read_claims
read_claim = _v6.read_claim
link_dependencies = _v6.link_dependencies
modes = _v6.modes
DEFAULT_PORT, HOST = _v6.DEFAULT_PORT, _v6.HOST
STATIC_V3 = _v1.STATIC_DIR.parent / "view_v3"  # SPEC_V7: the field on a phone


# ---------------------------------------------------------------------------
# 1. page
#    v6's page, from view_v3.
# ---------------------------------------------------------------------------
def page(db_path):
    cubes = read_claims(db_path)
    hubs, found, user = _v5.orbits(cubes, _v5.things(db_path))
    link_dependencies(cubes)
    return _v5.render_page(cubes, modes(cubes), hubs, found, user, static_dir=STATIC_V3)


# ---------------------------------------------------------------------------
# 2. OrbitHandlerV7, make_server, main
# ---------------------------------------------------------------------------
class OrbitHandlerV7(_v6.OrbitHandlerV6):

    # 2.1 _route — the v7 page; everything else v6's.
    def _route(self, head_only):
        if unquote(urlsplit(self.path).path) in ("/", "/index.html"):
            try:
                html = page(self.db_path)
            except (sqlite3.Error, FileNotFoundError) as e:
                return self._json(503, {"error": "database unavailable", "detail": str(e)}, head_only)
            return self._send(200, html, _v1.TYPES[".html"], head_only)
        return super()._route(head_only)


def make_server(db_path, port=DEFAULT_PORT, quiet=False):
    handler = type("BoundOrbitHandlerV7", (OrbitHandlerV7,), {"db_path": db_path, "quiet": quiet})
    return ThreadingHTTPServer((HOST, port), handler)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only, verified SCP Substrate viewer (v7).")
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
