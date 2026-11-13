"""
serve_v2.py — SCP Substrate v2, the verified reader over the frozen viewer

Function:
    The layer above SCP Substrate v1.0.0 (serve.py), and the entry
    point to run from v2 on. Reads P9 through substrate_v3's read-only
    API with verify-on-read: unverified claims are not drawn and
    unverified evidence never lights the glow. Applies P9 SPEC_V3 §3's
    attestation rule, so a later refusal shows as "retracted". Reuses
    v1's adapter, page rendering, static serving and read-only rules
    (SPEC_V2.md).

    serve.py is frozen and not edited.

Public API:
    1. read_claims(db_path) -> list[dict]
    2. read_claim(db_path, claim_id) -> dict | None
    3. check_health(db_path) -> (ok, body)
    4. VerifiedHandler — v1's handler, routed through 1–3
    5. make_server(db_path, port=8085, quiet=False)
    6. main(argv=None)

Internal helpers (not exported):
    7. _substrate — import P9 substrate_v3 from the sibling layer
    8. _evidence  — verified evidence rows in v1's shape
    9. _adapt     — v1 adapt_claim plus verification and retraction

Tier:      Tier 1 — Consumer (The Memory)
Depends:   P9 substrate_v3; serve.py v1.0.0
Spec:      SPEC_V2.md 2.0.0 (over SPEC.md 1.0.0)
Version:   2.0.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)
"""

import argparse
import importlib
import os
import sqlite3
import sys
from http.server import ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import serve as _v1  # noqa: E402

DEFAULT_PORT = _v1.DEFAULT_PORT
HOST = _v1.HOST


# ---------------------------------------------------------------------------
# 7. _substrate
# ---------------------------------------------------------------------------
def _substrate():
    path = os.path.abspath(os.path.join(_HERE, "..", "substrate-layer"))
    if path not in sys.path:
        sys.path.insert(0, path)
    return importlib.import_module("substrate_v3")


# ---------------------------------------------------------------------------
# 8. _evidence
#    SPEC_V2 §2: unverified or non-object evidence is dropped.
# ---------------------------------------------------------------------------
def _evidence(db_path, claim_id):
    return [{"evidence_id": e["evidence_id"], "capsule": e["capsule"], "created_at": e["created_at"]}
            for e in _substrate().read_evidence(db_path, claim_id, verify=True)
            if e["verified"] and isinstance(e["capsule"], dict)]


# ---------------------------------------------------------------------------
# 9. _adapt
#    SPEC_V2 §3: a refusal newer than the attestation retracts it.
# ---------------------------------------------------------------------------
def _adapt(row, evidence):
    claim = _v1.adapt_claim(row, row["capsule"], evidence)
    decisions = [e["capsule"] for e in evidence if e["capsule"].get("kind") in ("attestation", "refusal")]
    if claim["attestation"] is not None and decisions and decisions[-1].get("kind") == "refusal":
        claim["attestation"]["retracted"] = decisions[-1].get("note") or "refused"
        claim["status"] = "retracted"
    claim["verified"] = row.get("verified", True)
    return claim


# ---------------------------------------------------------------------------
# 1. read_claims
#    SPEC_V2 §2. Unverified claims are named on stderr and not drawn.
# ---------------------------------------------------------------------------
def read_claims(db_path):
    out = []
    for row in _substrate().list_claims(db_path, verify=True):
        if not row["verified"] or not isinstance(row["capsule"], dict):
            print(f"serve_v2.py: not drawn, failed verification: {row['claim_id']}", file=sys.stderr)
            continue
        out.append(_adapt(row, _evidence(db_path, row["claim_id"])))
    return out


# ---------------------------------------------------------------------------
# 2. read_claim
#    Any claim, verified or not, flagged; None if absent or unreadable.
# ---------------------------------------------------------------------------
def read_claim(db_path, claim_id):
    row = _substrate().read_claim(db_path, claim_id, verify=True)
    if row is None or not isinstance(row["capsule"], dict):
        return None
    evidence = _evidence(db_path, claim_id)
    claim = _adapt(row, evidence)
    claim.update(verified=row["verified"], verify_error=row["verify_error"],
                 capsule=row["capsule"], evidence=evidence)
    return claim


# ---------------------------------------------------------------------------
# 3. check_health
#    SPEC_V2 §4: v1's body plus verified / unverified active counts.
# ---------------------------------------------------------------------------
def check_health(db_path):
    ok, body = _v1.check_health(db_path)
    if ok:
        rows = _substrate().list_claims(db_path, verify=True)
        body["verified"] = sum(1 for r in rows if r["verified"])
        body["unverified"] = len(rows) - body["verified"]
    return ok, body


# ---------------------------------------------------------------------------
# 4. VerifiedHandler
#    v1's handler (methods, static files, JSON, 405) with v2's readers.
# ---------------------------------------------------------------------------
class VerifiedHandler(_v1.SubstrateHandler):

    # 4.1 _route — as v1 _route, reading through §2–§4; a missing database is 503.
    def _route(self, head_only):
        path = unquote(urlsplit(self.path).path)
        try:
            if path == "/api/health":
                ok, body = check_health(self.db_path)
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
                return self._send(200, _v1.render_page(read_claims(self.db_path)), _v1.TYPES[".html"], head_only)
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
    handler = type("BoundVerifiedHandler", (VerifiedHandler,), {"db_path": db_path, "quiet": quiet})
    return ThreadingHTTPServer((HOST, port), handler)


# ---------------------------------------------------------------------------
# 6. main
#    python serve_v2.py [--db PATH] [--port N].
# ---------------------------------------------------------------------------
def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only, verified SCP Substrate viewer (v2).")
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
