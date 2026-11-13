"""
serve_v3.py — SCP Substrate v3, ISO timestamps so attested claims draw

Function:
    The layer above SCP Substrate v2.0.0 (serve_v2.py), and the entry
    point to run from v3 on. Reads exactly as v2 (verified, read-only),
    then makes every time an ISO 8601 string before the field sees it
    (SPEC_V3.md). Fixes the field not drawing at all once any claim was
    attested: P9 stores the HAL seal time in epoch seconds, and the
    frontend calls `.slice()` on every time.

    serve.py, serve_v2.py and static/view/ are frozen and not edited.

Public API:
    1. read_claims(db_path) -> list[dict]
    2. read_claim(db_path, claim_id) -> dict | None
    3. render_page(cubes)            (v1's, re-exported)
    4. IsoHandler                    — v2's handler, routed through 1–2
    5. make_server(db_path, port=8085, quiet=False)
    6. main(argv=None)

Internal helpers:
    7. _iso       — one time value → ISO 8601 string, or a fallback
    8. _normalise — every time in one adapted claim

Tier:      Tier 1 — Consumer (The Memory)
Depends:   serve_v2.py (SPEC_V2 2.0.0), serve.py (render_page, static serving)
Spec:      SPEC_V3.md 3.0.0 (over SPEC_V2.md 2.0.0)
Version:   3.0.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)
"""

import argparse
import math
import os
import sqlite3
import sys
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import serve as _v1  # noqa: E402
import serve_v2 as _v2  # noqa: E402

render_page = _v1.render_page
DEFAULT_PORT = _v1.DEFAULT_PORT
HOST = _v1.HOST


# ---------------------------------------------------------------------------
# 7. _iso
#    SPEC_V3 §2: number → epoch seconds → ISO UTC; string kept; anything
#    else → the fallback (the claim's created_at).
# ---------------------------------------------------------------------------
def _iso(value, fallback):
    if isinstance(value, str) and value:
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
        return datetime.fromtimestamp(value, timezone.utc).isoformat()
    return fallback


# ---------------------------------------------------------------------------
# 8. _normalise
# ---------------------------------------------------------------------------
def _normalise(claim):
    base = _iso(claim.get("created_at"), None) or _iso(claim.get("created"), "")
    claim["created_at"] = base
    claim["created"] = _iso(claim.get("created"), base)
    for face in (claim.get("faces") or {}).values():
        if face:
            face["at"] = _iso(face.get("at"), base)
            face["filled_at"] = _iso(face.get("filled_at"), face["at"])
    if claim.get("attestation"):
        claim["attestation"]["at"] = _iso(claim["attestation"].get("at"), base)
    return claim


# ---------------------------------------------------------------------------
# 1. read_claims
# ---------------------------------------------------------------------------
def read_claims(db_path):
    return [_normalise(c) for c in _v2.read_claims(db_path)]


# ---------------------------------------------------------------------------
# 2. read_claim
# ---------------------------------------------------------------------------
def read_claim(db_path, claim_id):
    claim = _v2.read_claim(db_path, claim_id)
    return None if claim is None else _normalise(claim)


# ---------------------------------------------------------------------------
# 4. IsoHandler
#    v2's handler with v3's readers (v2 calls its own module functions,
#    so its 20-line router is restated here, as v2 did over v1).
# ---------------------------------------------------------------------------
class IsoHandler(_v2.VerifiedHandler):

    # 4.1 _route
    def _route(self, head_only):
        path = unquote(urlsplit(self.path).path)
        try:
            if path == "/api/health":
                ok, body = _v2.check_health(self.db_path)
                return self._json(200 if ok else 503, body, head_only)
            if path == "/api/claims":
                return self._json(200, read_claims(self.db_path), head_only)
            if path.startswith("/api/claims/"):
                claim = read_claim(self.db_path, path[len("/api/claims/"):])
                if claim is None:
                    return self._json(404, {"error": "no such claim"}, head_only)
                return self._json(200, claim, head_only)
            if path.startswith("/api/"):
                return self._json(404, {"error": "no such endpoint"}, head_only)
            if path in ("/", "/index.html"):
                return self._send(200, render_page(read_claims(self.db_path)), _v1.TYPES[".html"], head_only)
        except (sqlite3.Error, FileNotFoundError) as e:
            return self._json(503, {"error": "database unavailable", "detail": str(e)}, head_only)
        name = path.lstrip("/")
        if name and "/" not in name and "\\" not in name and name in os.listdir(_v1.STATIC_DIR):
            file = _v1.STATIC_DIR / name
            return self._send(200, file.read_bytes(), _v1.TYPES.get(file.suffix, "application/octet-stream"), head_only)
        return self._json(404, {"error": "not found"}, head_only)


# ---------------------------------------------------------------------------
# 5. make_server
# ---------------------------------------------------------------------------
def make_server(db_path, port=DEFAULT_PORT, quiet=False):
    handler = type("BoundIsoHandler", (IsoHandler,), {"db_path": db_path, "quiet": quiet})
    return ThreadingHTTPServer((HOST, port), handler)


# ---------------------------------------------------------------------------
# 6. main
#    python serve_v3.py [--db PATH] [--port N].
# ---------------------------------------------------------------------------
def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only, verified SCP Substrate viewer (v3).")
    parser.add_argument("--db", help="P9 SQLite database (default: $FORGE_HOME/forge.db, else ~/.forge/forge.db)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"port on {HOST} (default {DEFAULT_PORT})")
    args = parser.parse_args(argv)
    db_path = _v1.resolve_db_path(args.db)
    server = make_server(db_path, args.port)
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
