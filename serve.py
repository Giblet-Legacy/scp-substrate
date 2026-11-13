"""
serve.py — read-only HTTP server for SCP Substrate (Tier 1 Consumer)

Function:
    Reads P9 Substrate's SQLite (claims and evidence tables, SPEC.md §2 of
    substrate-layer) and renders it as the cube field in static/view/.
    Standard library only. Read-only: the database is opened with SQLite's
    mode=ro, and every method other than GET and HEAD returns 405.

    Endpoints:
        GET /                  the cube field page, data injected
        GET /<file>            a file from static/view/, served as is
        GET /api/health        probes the database (200 ok, 503 not)
        GET /api/claims        every active claim, adapted for the frontend
        GET /api/claims/<id>   one claim (active or superseded) with evidence

    Functions:
        1.  resolve_db_path   — --db flag, else $FORGE_HOME/forge.db, else ~/.forge/forge.db
        2.  connect_ro        — open the database read-only
        3.  check_health      — probe tables and count rows
        4.  claim_text        — the sentence a claim says
        5.  faces_of          — the six P13 faces a capsule carries
        6.  attestation_of    — the human attestation, if any
        7.  adapt_claim       — one P9 row into the frontend's cube shape
        8.  read_claims       — every active claim, adapted
        9.  read_claim        — one claim with its evidence
        10. safe_json         — JSON that is safe inside a <script> element
        11. render_page       — fill the template's slots
        12. SubstrateHandler  — the request handler (GET/HEAD only)
        13. make_server       — build a bound server
        14. main              — command line entry point

Tier:     Tier 1 — Consumer (SCP Substrate)
Depends:  P8 Store (SQLite), P9 Substrate (claims/evidence), read only
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

# The six faces, in P13 DataCube's order (datacube.py FACES). Human
# validation is a separate signed attestation, never a face.
FACES = ("FACT", "COUNTER", "OPINION", "FICTION", "CONTEXT", "UNKNOWN")

DEFAULT_PORT = 8085
HOST = "127.0.0.1"  # localhost only in v1 (SPEC §3)
STATIC_DIR = Path(__file__).resolve().parent / "static" / "view"
# The field fragments share one scope and must be joined in this order
FIELD_PARTS = ("world", "form", "hubs", "draw", "time", "move")
GROUP = "Claims"
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".json": "application/json"}


# ---------------------------------------------------------------------------
# 1. resolve_db_path
#    The --db flag wins, then $FORGE_HOME/forge.db, then ~/.forge/forge.db.
# ---------------------------------------------------------------------------
def resolve_db_path(flag=None, env=None):
    env = os.environ if env is None else env
    if flag:
        return str(Path(flag).expanduser())
    home = env.get("FORGE_HOME")
    base = Path(home).expanduser() if home else Path.home() / ".forge"
    return str(base / "forge.db")


# ---------------------------------------------------------------------------
# 2. connect_ro
#    Opens the database read-only. SQLite refuses every write on this
#    connection, and a missing file raises instead of being created.
# ---------------------------------------------------------------------------
def connect_ro(db_path):
    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# 3. check_health
#    Returns (ok, body). ok is True when both P9 tables can be read.
# ---------------------------------------------------------------------------
def check_health(db_path):
    try:
        conn = connect_ro(db_path)
        try:
            claims = conn.execute("SELECT COUNT(*), COALESCE(SUM(is_active), 0) FROM claims").fetchone()
            evidence = conn.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
        finally:
            conn.close()
    except sqlite3.Error as e:
        return False, {"status": "error", "db": db_path, "error": str(e)}
    return True, {"status": "ok", "db": db_path, "read_only": True,
                  "claims": claims[0], "active": claims[1], "evidence": evidence}


# ---------------------------------------------------------------------------
# 4. claim_text
#    A capsule's own "content" if it has one, else subject predicate object.
# ---------------------------------------------------------------------------
def claim_text(capsule):
    content = capsule.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    parts = [capsule.get(k) for k in ("subject", "predicate", "object")]
    words = [str(p) for p in parts if p not in (None, "")]
    return " ".join(words) or "(empty claim)"


# ---------------------------------------------------------------------------
# 5. faces_of
#    The faces a capsule carries, as {FACE: {content, at, filled_at} | None}.
#    Read from, in order: a "faces" dict, top-level face keys (a stored P13
#    cube), then the claim's own "face" tag, which fills that one face with
#    the claim's sentence. Non-string or empty content counts as missing,
#    as P13 says empty faces are None.
# ---------------------------------------------------------------------------
def faces_of(capsule, at):
    nested = capsule.get("faces") if isinstance(capsule.get("faces"), dict) else {}
    out = {}
    for face in FACES:
        text = nested.get(face, capsule.get(face))
        ok = isinstance(text, str) and text.strip()
        out[face] = {"content": text, "at": at, "filled_at": at} if ok else None
    tagged = capsule.get("face")
    if tagged in FACES and out[tagged] is None:
        out[tagged] = {"content": claim_text(capsule), "at": at, "filled_at": at}
    return out


# ---------------------------------------------------------------------------
# 6. attestation_of
#    Human attestation (P13: a separate signed attestation, never a face).
#    Taken from the capsule's "attestation" dict, else the latest evidence
#    capsule with kind "attestation". Returns {source, note, at, retracted}
#    or None.
# ---------------------------------------------------------------------------
def attestation_of(capsule, at, evidence):
    found, when = capsule.get("attestation"), at
    if not isinstance(found, dict):
        found = None
        for item in evidence:
            if item["capsule"].get("kind") == "attestation":
                found, when = item["capsule"], item["created_at"]
    if found is None:
        return None
    sig = found.get("signature") if isinstance(found.get("signature"), dict) else {}
    source = found.get("by") or found.get("source") or sig.get("key_id") or "unknown"
    retracted = found.get("retracted")
    return {"source": str(source), "note": found.get("note") or "", "at": found.get("at") or when,
            "retracted": retracted if isinstance(retracted, str) and retracted else None}


# ---------------------------------------------------------------------------
# 7. adapt_claim
#    One P9 claims row (with its parsed capsule and evidence) into the shape
#    view_grid.js and view_field_*.js expect. P9 columns are kept as is.
# ---------------------------------------------------------------------------
def adapt_claim(row, capsule, evidence):
    at = row["created_at"]
    faces = faces_of(capsule, at)
    filled = sum(1 for f in faces.values() if f)
    attestation = attestation_of(capsule, at, evidence)
    status = ("draft" if attestation is None
              else "retracted" if attestation["retracted"] else "attested")
    subject = capsule.get("subject")
    tags = capsule.get("tags")
    tags = ([t for t in tags if isinstance(t, str)] if isinstance(tags, list)
            else [str(subject)] if subject not in (None, "") else [])
    signer = row["signer"]
    return {
        # P9 columns
        "id": row["claim_id"], "claim_id": row["claim_id"], "signer": signer,
        "is_active": bool(row["is_active"]), "superseded_by": row["superseded_by"],
        "created": at, "created_at": at,
        # The claim itself
        "subject": subject, "predicate": capsule.get("predicate"), "object": capsule.get("object"),
        "content": claim_text(capsule), "faces": faces, "filled": filled,
        "attestation": attestation, "status": status, "score": filled / len(FACES),
        "evidence_count": len(evidence),
        # Frontend layout fields P9 does not have
        "group": GROUP, "tags": tags, "source": "Signed by " + (signer[:24] + "…" if len(signer) > 25 else signer),
        "standing": 0, "neighbours": [],
    }


def _evidence_by_claim(conn, claim_id=None):
    """Evidence rows grouped by claim_id, oldest first (P9 v2 order).
    Unparseable evidence capsules are skipped."""
    sql = "SELECT evidence_id, claim_id, capsule, created_at FROM evidence"
    args = ()
    if claim_id is not None:
        sql, args = sql + " WHERE claim_id = ?", (claim_id,)
    grouped = {}
    for r in conn.execute(sql + " ORDER BY created_at, rowid", args):
        try:
            cap = json.loads(r["capsule"])
        except ValueError:
            continue
        if isinstance(cap, dict):
            grouped.setdefault(r["claim_id"], []).append(
                {"evidence_id": r["evidence_id"], "capsule": cap, "created_at": r["created_at"]})
    return grouped


# ---------------------------------------------------------------------------
# 8. read_claims
#    Every active claim (is_active = 1), oldest first, adapted. A row whose
#    capsule is not a JSON object is skipped and reported on stderr, so one
#    bad row cannot blank the field.
# ---------------------------------------------------------------------------
def read_claims(db_path):
    conn = connect_ro(db_path)
    try:
        evidence = _evidence_by_claim(conn)
        rows = conn.execute("SELECT * FROM claims WHERE is_active = 1 ORDER BY created_at, rowid").fetchall()
    finally:
        conn.close()
    out = []
    for row in rows:
        try:
            capsule = json.loads(row["capsule"])
        except ValueError:
            capsule = None
        if not isinstance(capsule, dict):
            print(f"serve.py: skipped claim {row['claim_id']}: capsule is not a JSON object", file=sys.stderr)
            continue
        out.append(adapt_claim(row, capsule, evidence.get(row["claim_id"], [])))
    return out


# ---------------------------------------------------------------------------
# 9. read_claim
#    One claim by id, active or superseded, with its evidence capsules.
#    Returns None if not found or the capsule cannot be read.
# ---------------------------------------------------------------------------
def read_claim(db_path, claim_id):
    conn = connect_ro(db_path)
    try:
        row = conn.execute("SELECT * FROM claims WHERE claim_id = ?", (claim_id,)).fetchone()
        evidence = _evidence_by_claim(conn, claim_id).get(claim_id, []) if row else []
    finally:
        conn.close()
    if row is None:
        return None
    try:
        capsule = json.loads(row["capsule"])
    except ValueError:
        return None
    if not isinstance(capsule, dict):
        return None
    claim = adapt_claim(row, capsule, evidence)
    claim["capsule"] = capsule
    claim["evidence"] = evidence
    return claim


# ---------------------------------------------------------------------------
# 10. safe_json
#     JSON for a <script> element: <, >, & and the two JavaScript line
#     separators are escaped, so claim text cannot close the script.
# ---------------------------------------------------------------------------
def safe_json(value):
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    for raw, esc in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026"),
                     (" ", "\\u2028"), (" ", "\\u2029")):
        text = text.replace(raw, esc)
    return text


# ---------------------------------------------------------------------------
# 11. render_page
#     Fills view_grid.js's data slots, joins the field fragments inside one
#     function, and fills the template. Each fill is one regex pass, so text
#     inside injected data is never mistaken for a slot. Files are read on
#     every call, so edits to static/view/ show without a restart.
# ---------------------------------------------------------------------------
def render_page(cubes, static_dir=STATIC_DIR, user="You"):
    read = lambda name: (Path(static_dir) / name).read_text(encoding="utf-8")
    data = {"CUBES": safe_json(cubes), "MODES": "{}", "USER": safe_json(user),
            "HUBS": "[]", "THINGS": "{}", "LENSES": safe_json(list(FACES))}
    # Each slot is a marker followed by its default literal: /*CUBES*/[] etc.
    grid = re.sub(r'/\*(CUBES|MODES|USER|HUBS|THINGS|LENSES)\*/(\[[^\]]*\]|\{\}|"[^"]*")',
                  lambda m: data[m.group(1)], read("view_grid.js"))
    field = "(() => {\n" + "\n".join(read(f"view_field_{p}.js") for p in FIELD_PARTS) + "\n})();\n"
    parts = {"STYLE": read("view_style.css"), "GRID": grid, "FIELD": field, "BAR": read("view_bar.js")}
    return re.sub(r"/\*(STYLE|GRID|FIELD|BAR)\*/", lambda m: parts[m.group(1)], read("view_template.html"))


# ---------------------------------------------------------------------------
# 12. SubstrateHandler
#     GET and HEAD only. Everything else is 405: the browser cannot write.
# ---------------------------------------------------------------------------
class SubstrateHandler(BaseHTTPRequestHandler):
    server_version = "scp-substrate/1.0"
    db_path = None      # set by make_server
    quiet = False

    def log_message(self, fmt, *args):
        """Request log to stderr, unless the server is quiet (tests)."""
        if not self.quiet:
            super().log_message(fmt, *args)

    def _send(self, status, body, ctype, head_only=False):
        """Send one response with no-store caching and nosniff."""
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if status == 405:
            self.send_header("Allow", "GET, HEAD")
        self.end_headers()
        if not head_only:
            self.wfile.write(data)

    def _json(self, status, value, head_only=False):
        """Send a JSON response."""
        self._send(status, json.dumps(value, ensure_ascii=False), "application/json; charset=utf-8", head_only)

    def _route(self, head_only):
        """Answer a GET or HEAD request."""
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
                return self._send(200, render_page(read_claims(self.db_path)), TYPES[".html"], head_only)
        except sqlite3.Error as e:
            return self._json(503, {"error": "database unavailable", "detail": str(e)}, head_only)
        # Static files: only names that exist directly in static/view/
        name = path.lstrip("/")
        if name and "/" not in name and "\\" not in name and name in os.listdir(STATIC_DIR):
            file = STATIC_DIR / name
            return self._send(200, file.read_bytes(), TYPES.get(file.suffix, "application/octet-stream"), head_only)
        return self._json(404, {"error": "not found"}, head_only)

    def do_GET(self):
        """GET: routes, pages and static files."""
        self._route(head_only=False)

    def do_HEAD(self):
        """HEAD: as GET, without the body."""
        self._route(head_only=True)

    def _refuse(self):
        """Any write method: 405, read-only in v1."""
        self._json(405, {"error": "read-only: all writes go through The Cockpit"})

    do_POST = do_PUT = do_PATCH = do_DELETE = _refuse


# ---------------------------------------------------------------------------
# 13. make_server
#     A threading server bound to localhost. Port 0 picks a free port; read
#     it back from server.server_address.
# ---------------------------------------------------------------------------
def make_server(db_path, port=DEFAULT_PORT, quiet=False):
    handler = type("BoundHandler", (SubstrateHandler,), {"db_path": db_path, "quiet": quiet})
    return ThreadingHTTPServer((HOST, port), handler)


# ---------------------------------------------------------------------------
# 14. main
#     python serve.py [--db PATH] [--port N]. Prints the URL once listening.
# ---------------------------------------------------------------------------
def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only SCP Substrate viewer for P9 claims.")
    parser.add_argument("--db", help="P9 SQLite database (default: $FORGE_HOME/forge.db, else ~/.forge/forge.db)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"port on {HOST} (default {DEFAULT_PORT})")
    args = parser.parse_args(argv)
    db_path = resolve_db_path(args.db)
    server = make_server(db_path, args.port)
    print(f"Serving {db_path} read-only on http://{HOST}:{server.server_address[1]}/", flush=True)
    ok, body = check_health(db_path)
    if not ok:
        print(f"Warning: database not readable yet: {body['error']}", file=sys.stderr, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
