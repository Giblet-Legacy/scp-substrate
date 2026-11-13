"""
test_substrate.py — tests for SCP Substrate's read-only server (serve.py)

Function:
    Builds P9 databases from the schema in substrate-layer SPEC.md §2 and
    checks that serve.py starts, reports health, adapts claims faithfully,
    serves the page and static files, and never writes. When the sibling
    substrate-layer (P9) and the cryptography package are present, one
    test writes real signed claims through substrate_v2 and checks the API
    against them; otherwise that test is skipped.

    Tests (grouped):
        1. Start-up      — the process starts and listens; db path resolution
        2. Health        — 200 on a P9 database, 503 when missing or not P9
        3. Claims        — JSON, P9 columns, faces, attestation, bad rows
        4. Real P9       — claims written by substrate_v2 (skipped if absent)
        5. Page/static   — template filled, six faces injected, files served
        6. Read-only     — 405 on writes, database bytes unchanged

Tier:     Tier 1 — Consumer (SCP Substrate)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

import serve

HERE = Path(__file__).resolve().parent
STACK = HERE.parent

# substrate-layer SPEC.md §2, verbatim
P9_SCHEMA = """
CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY,
    signer TEXT NOT NULL,
    capsule TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    superseded_by TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evidence (
    evidence_id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL,
    capsule TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id)
);
CREATE INDEX IF NOT EXISTS idx_claims_signer ON claims(signer);
CREATE INDEX IF NOT EXISTS idx_evidence_claim ON evidence(claim_id);
"""
SIGNER = "did:key:z6MkTestSignerForScpSubstrateOnly"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_db(path, claims=(), evidence=()):
    """Create a P9 database at path. claims: (id, capsule, active, superseded_by,
    created_at); evidence: (id, claim_id, capsule, created_at). Capsules that
    are dicts are stored as JSON; strings are stored as given."""
    conn = sqlite3.connect(path)
    conn.executescript(P9_SCHEMA)
    enc = lambda c: c if isinstance(c, str) else json.dumps(c, sort_keys=True)
    for cid, cap, active, sup, at in claims:
        conn.execute("INSERT INTO claims VALUES (?,?,?,?,?,?)", (cid, SIGNER, enc(cap), active, sup, at))
    for eid, cid, cap, at in evidence:
        conn.execute("INSERT INTO evidence VALUES (?,?,?,?)", (eid, cid, enc(cap), at))
    conn.commit()
    conn.close()
    return str(path)


def signed(body):
    """A capsule with a P2-shaped signature object (not a real signature)."""
    return {**body, "signature": {"algorithm": "Ed25519", "key_id": SIGNER, "value": "00"}}


def sample_db(tmp_path):
    """A small substrate: a plain triple, a stored P13 cube with all six faces
    and an attestation, a face-tagged UNKNOWN, a superseded claim, evidence
    and an attestation carried as evidence."""
    cube = signed({"subject": "sky", "predicate": "is", "object": "blue",
                   "FACT": "Rayleigh scattering", "COUNTER": "Sunsets are red", "OPINION": "Lovely",
                   "FICTION": "Painted by giants", "CONTEXT": "Observed at noon", "UNKNOWN": "On Mars?",
                   "attestation": {"by": "James", "note": "I stand behind this", "at": "2026-11-02T10:00:00+00:00"}})
    return make_db(tmp_path / "forge.db", claims=[
        ("c-old", signed({"subject": "grass", "predicate": "is", "object": "blue"}), 0, "c-new", "2026-11-01T09:00:00+00:00"),
        ("c-new", signed({"subject": "grass", "predicate": "is", "object": "green"}), 1, None, "2026-11-01T10:00:00+00:00"),
        ("c-cube", cube, 1, None, "2026-11-01T11:00:00+00:00"),
        ("c-dream", signed({"subject": "sea", "predicate": "might be", "object": "warmer", "face": "UNKNOWN"}),
         1, None, "2026-11-01T12:00:00+00:00"),
        ("c-ev", signed({"subject": "fire", "predicate": "is", "object": "hot"}), 1, None, "2026-11-01T13:00:00+00:00"),
    ], evidence=[
        ("e-1", "c-new", signed({"source": "a photo"}), "2026-11-01T10:05:00+00:00"),
        ("e-2", "c-ev", signed({"kind": "attestation", "by": "James", "note": "Burnt my hand"}), "2026-11-01T13:05:00+00:00"),
    ])


@pytest.fixture
def server_for():
    """Start serve.py in-process on a free port; yields a function db -> base URL."""
    started = []

    def start(db_path):
        srv = serve.make_server(db_path, port=0, quiet=True)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        started.append(srv)
        return f"http://{serve.HOST}:{srv.server_address[1]}"

    yield start
    for srv in started:
        srv.shutdown()
        srv.server_close()


def fetch(url, method="GET", data=None):
    """Return (status, headers, body bytes); HTTP errors are returned, not raised."""
    req = urllib.request.Request(url, method=method, data=data)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()


def by_id(claims):
    """Index adapted claims by id."""
    return {c["id"]: c for c in claims}


# ---------------------------------------------------------------------------
# 1. Start-up
# ---------------------------------------------------------------------------
def test_process_starts_and_serves(tmp_path):
    """python serve.py starts, prints its URL, and answers health."""
    db = sample_db(tmp_path)
    proc = subprocess.Popen([sys.executable, str(HERE / "serve.py"), "--db", db, "--port", "0"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        line = proc.stdout.readline()
        url = re.search(r"http://\S+/", line).group(0)
        status, _, body = fetch(url + "api/health")
        assert status == 200 and json.loads(body)["status"] == "ok"
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def test_default_port_is_8085():
    """Q4: default port 8085, matching The Cockpit's future forge web."""
    assert serve.DEFAULT_PORT == 8085
    assert serve.HOST == "127.0.0.1"


def test_db_path_resolution(tmp_path):
    """--db wins, then FORGE_HOME/forge.db, then ~/.forge/forge.db."""
    assert serve.resolve_db_path(str(tmp_path / "x.db"), {"FORGE_HOME": "/elsewhere"}) == str(tmp_path / "x.db")
    assert serve.resolve_db_path(None, {"FORGE_HOME": str(tmp_path)}) == str(tmp_path / "forge.db")
    assert serve.resolve_db_path(None, {}) == str(Path.home() / ".forge" / "forge.db")


# ---------------------------------------------------------------------------
# 2. Health
# ---------------------------------------------------------------------------
def test_health_ok(tmp_path, server_for):
    """200 with row counts on a P9 database."""
    base = server_for(sample_db(tmp_path))
    status, headers, body = fetch(base + "/api/health")
    assert status == 200
    assert headers["Content-Type"].startswith("application/json")
    health = json.loads(body)
    assert health == {**health, "status": "ok", "read_only": True, "claims": 5, "active": 4, "evidence": 2}


def test_health_missing_db_is_503_and_not_created(tmp_path, server_for):
    """A missing database is reported, and read-only mode does not create it."""
    db = tmp_path / "absent.db"
    base = server_for(str(db))
    status, _, body = fetch(base + "/api/health")
    assert status == 503 and json.loads(body)["status"] == "error"
    assert fetch(base + "/api/claims")[0] == 503
    assert not db.exists()


def test_health_not_p9_is_503(tmp_path, server_for):
    """A SQLite file without P9's tables is not healthy."""
    db = tmp_path / "other.db"
    sqlite3.connect(db).execute("CREATE TABLE t (x)").connection.close()
    assert fetch(server_for(str(db)) + "/api/health")[0] == 503


# ---------------------------------------------------------------------------
# 3. Claims
# ---------------------------------------------------------------------------
def test_claims_match_p9_rows(tmp_path, server_for):
    """Every active row, and only those, comes back with its P9 columns and
    capsule fields intact."""
    db = sample_db(tmp_path)
    status, headers, body = fetch(server_for(db) + "/api/claims")
    assert status == 200 and headers["Content-Type"].startswith("application/json")
    claims = json.loads(body)
    assert isinstance(claims, list)
    conn = sqlite3.connect(db)
    rows = conn.execute("SELECT claim_id, signer, capsule, created_at FROM claims WHERE is_active=1").fetchall()
    conn.close()
    assert sorted(c["id"] for c in claims) == sorted(r[0] for r in rows)
    got = by_id(claims)
    for cid, signer, capsule, created in rows:
        cap, c = json.loads(capsule), got[cid]
        assert c["claim_id"] == cid and c["signer"] == signer and c["created_at"] == created
        assert c["is_active"] is True and c["superseded_by"] is None
        assert (c["subject"], c["predicate"], c["object"]) == (cap["subject"], cap["predicate"], cap["object"])


def test_claim_shape_fits_frontend(tmp_path, server_for):
    """Each claim carries the fields the frontend reads, with all six faces."""
    claims = json.loads(fetch(server_for(sample_db(tmp_path)) + "/api/claims")[2])
    for c in claims:
        for key in ("id", "content", "group", "tags", "faces", "status", "score", "filled",
                    "standing", "neighbours", "created", "attestation", "source"):
            assert key in c, key
        assert list(c["faces"]) == list(serve.FACES)
        assert "HUMAN" not in c["faces"] and "validation" not in c
        assert c["status"] in ("attested", "retracted", "draft")
        assert 0 <= c["score"] <= 1 and c["filled"] == sum(1 for f in c["faces"].values() if f)


def test_faces_and_attestation(tmp_path, server_for):
    """A stored P13 cube fills all six sides; a face tag fills one; attestation
    comes from the capsule or from attestation evidence, never a face."""
    got = by_id(json.loads(fetch(server_for(sample_db(tmp_path)) + "/api/claims")[2]))
    cube = got["c-cube"]
    assert cube["filled"] == 6 and cube["score"] == 1
    assert cube["faces"]["UNKNOWN"]["content"] == "On Mars?"
    assert cube["status"] == "attested" and cube["attestation"]["source"] == "James"
    dream = got["c-dream"]
    assert dream["filled"] == 1 and dream["faces"]["UNKNOWN"]["content"] == "sea might be warmer"
    assert dream["status"] == "draft" and dream["attestation"] is None
    assert got["c-ev"]["status"] == "attested" and got["c-ev"]["attestation"]["note"] == "Burnt my hand"
    assert got["c-new"]["filled"] == 0 and got["c-new"]["content"] == "grass is green"
    assert got["c-new"]["tags"] == ["grass"] and got["c-new"]["evidence_count"] == 1


def test_one_claim_with_evidence(tmp_path, server_for):
    """/api/claims/<id> returns one claim, superseded ones included."""
    base = server_for(sample_db(tmp_path))
    status, _, body = fetch(base + "/api/claims/c-new")
    one = json.loads(body)
    assert status == 200 and one["evidence"][0]["capsule"]["source"] == "a photo"
    old = json.loads(fetch(base + "/api/claims/c-old")[2])
    assert old["is_active"] is False and old["superseded_by"] == "c-new"
    assert fetch(base + "/api/claims/nope")[0] == 404


def test_bad_capsule_is_skipped(tmp_path, server_for):
    """A row whose capsule is not a JSON object does not break the list."""
    db = make_db(tmp_path / "forge.db", claims=[
        ("good", signed({"subject": "a", "predicate": "is", "object": "b"}), 1, None, "2026-11-01T00:00:00+00:00"),
        ("bad", "{not json", 1, None, "2026-11-01T00:00:01+00:00"),
        ("list", "[1, 2]", 1, None, "2026-11-01T00:00:02+00:00"),
    ])
    status, _, body = fetch(server_for(db) + "/api/claims")
    assert status == 200 and [c["id"] for c in json.loads(body)] == ["good"]


def test_empty_substrate(tmp_path, server_for):
    """An empty P9 database gives an empty list and a working page."""
    base = server_for(make_db(tmp_path / "forge.db"))
    assert json.loads(fetch(base + "/api/claims")[2]) == []
    assert fetch(base + "/")[0] == 200


# ---------------------------------------------------------------------------
# 4. Real P9 (substrate_v2), skipped when the sibling layer is not present
# ---------------------------------------------------------------------------
def test_real_p9_claims(tmp_path, server_for, monkeypatch):
    """Claims signed and stored by P9's own code come back faithfully."""
    for layer in ("substrate-layer", "envelope-layer", "sign-layer"):
        if not (STACK / layer).is_dir():
            pytest.skip(f"sibling {layer} not present")
        monkeypatch.syspath_prepend(str(STACK / layer))
    pytest.importorskip("cryptography")
    substrate_v2 = pytest.importorskip("substrate_v2")
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    db = str(tmp_path / "forge.db")
    key = Ed25519PrivateKey.generate()
    substrate_v2.init_db(db)
    old = substrate_v2.write_claim(db, {"subject": "sky", "predicate": "is", "object": "blue"}, key)
    new = substrate_v2.supersede_claim(db, old, {"subject": "sky", "predicate": "is", "object": "grey"}, key)
    dream = substrate_v2.write_claim(db, {"subject": "sky", "predicate": "might be", "object": "green",
                                          "face": "UNKNOWN"}, key)
    substrate_v2.link_evidence(db, new, {"kind": "attestation", "by": "James"}, key)

    base = server_for(db)
    claims = by_id(json.loads(fetch(base + "/api/claims")[2]))
    assert set(claims) == {new, dream}
    assert claims[new]["object"] == "grey" and claims[new]["status"] == "attested"
    assert claims[new]["signer"] == substrate_v2.get_claim(db, new)["signature"]["key_id"]
    assert claims[dream]["faces"]["UNKNOWN"]["content"] == "sky might be green"
    assert json.loads(fetch(base + f"/api/claims/{old}")[2])["superseded_by"] == new


def test_faces_match_p13():
    """serve.FACES is P13 DataCube's six faces, in order (if P13 is present)."""
    p13 = STACK / "datacube-layer" / "datacube.py"
    if not p13.exists():
        pytest.skip("sibling datacube-layer not present")
    match = re.search(r"^FACES = \((.*)\)$", p13.read_text(encoding="utf-8"), re.M)
    assert tuple(re.findall(r'"(\w+)"', match.group(1))) == serve.FACES


# ---------------------------------------------------------------------------
# 5. Page and static files
# ---------------------------------------------------------------------------
def test_page_is_filled(tmp_path, server_for):
    """/ is the template with every slot filled and six faces injected."""
    status, headers, body = fetch(server_for(sample_db(tmp_path)) + "/")
    page = body.decode("utf-8")
    assert status == 200 and headers["Content-Type"].startswith("text/html")
    for slot in ("STYLE", "GRID", "FIELD", "BAR", "EDIT", "CUBES", "MODES", "USER", "HUBS", "THINGS", "LENSES", "API"):
        assert f"/*{slot}*/" not in page, slot
    assert 'const LENSES = ["FACT","COUNTER","OPINION","FICTION","CONTEXT","UNKNOWN"];' in page
    assert "c-cube" in page and "HUMAN" not in page
    assert page.count("<script>") == 3


def test_page_escapes_claim_text(tmp_path, server_for):
    """Claim text cannot close the script element it is injected into."""
    db = make_db(tmp_path / "forge.db", claims=[
        ("x", signed({"subject": "</script><script>alert(1)</script>", "predicate": "/*FIELD*/", "object": "&"}),
         1, None, "2026-11-01T00:00:00+00:00")])
    page = fetch(server_for(db) + "/")[2].decode("utf-8")
    assert "alert(1)</script>" not in page
    assert page.count("<script>") == 3 and page.count("</script>") == 3


def test_page_scripts_parse(tmp_path):
    """The joined scripts are valid JavaScript (needs node; skipped otherwise)."""
    node = shutil.which("node")
    if not node:
        pytest.skip("node not installed")
    page = serve.render_page(serve.read_claims(sample_db(tmp_path)))
    for i, script in enumerate(re.findall(r"<script>(.*?)</script>", page, re.S)):
        path = tmp_path / f"script{i}.js"
        path.write_text(script, encoding="utf-8")
        result = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


def test_static_files_served(tmp_path, server_for):
    """Files in static/view/ are served as they are, with a content type."""
    base = server_for(sample_db(tmp_path))
    status, headers, body = fetch(base + "/view_style.css")
    assert status == 200 and headers["Content-Type"].startswith("text/css")
    assert body == (serve.STATIC_DIR / "view_style.css").read_bytes()
    status, headers, _ = fetch(base + "/view_field_world.js")
    assert status == 200 and headers["Content-Type"].startswith("text/javascript")


def test_static_cannot_escape(tmp_path, server_for):
    """Only files directly in static/view/ are reachable."""
    base = server_for(sample_db(tmp_path))
    for path in ("/../serve.py", "/%2e%2e/serve.py", "/..%2fserve.py", "/static/view/view_style.css", "/nope.js"):
        assert fetch(base + path)[0] == 404, path


def test_frontend_has_no_human_side():
    """The six-face patch is applied across static/view/: no HUMAN side,
    no validation, no write path."""
    for f in serve.STATIC_DIR.iterdir():
        text = f.read_text(encoding="utf-8")
        assert "HUMAN" not in text, f.name
        assert "validation" not in text.replace("human validation", ""), f.name
        assert "/api/do" not in text and "method: \"POST\"" not in text, f.name
    world = (serve.STATIC_DIR / "view_field_world.js").read_text(encoding="utf-8")
    assert "UNKNOWN: [130, 130, 140]" in world and '["UNKNOWN", [7, 6, 2, 3]]' in world
    assert "UNKNOWN: [0,1,0]" in world and "NAMES" not in world


# ---------------------------------------------------------------------------
# 6. Read-only
# ---------------------------------------------------------------------------
def test_writes_refused(tmp_path, server_for):
    """POST, PUT, PATCH and DELETE are 405 everywhere."""
    base = server_for(sample_db(tmp_path))
    for method in ("POST", "PUT", "PATCH", "DELETE"):
        for path in ("/api/claims", "/api/do", "/"):
            status, headers, _ = fetch(base + path, method=method, data=b"{}")
            assert status == 405 and headers["Allow"] == "GET, HEAD", (method, path)


def test_database_unchanged(tmp_path, server_for):
    """Serving every route leaves the database file byte-identical."""
    db = sample_db(tmp_path)
    before = hashlib.sha256(Path(db).read_bytes()).hexdigest()
    base = server_for(db)
    for path in ("/", "/api/health", "/api/claims", "/api/claims/c-new", "/view_grid.js"):
        fetch(base + path)
    fetch(base + "/api/claims", method="POST", data=b"{}")
    assert hashlib.sha256(Path(db).read_bytes()).hexdigest() == before


def test_connection_is_read_only(tmp_path):
    """SQLite itself refuses writes on serve.py's connection."""
    conn = serve.connect_ro(sample_db(tmp_path))
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("DELETE FROM claims")
    conn.close()


def test_head_has_no_body(tmp_path, server_for):
    """HEAD answers like GET without a body."""
    status, headers, body = fetch(server_for(sample_db(tmp_path)) + "/api/health", method="HEAD")
    assert status == 200 and body == b"" and int(headers["Content-Length"]) > 0
