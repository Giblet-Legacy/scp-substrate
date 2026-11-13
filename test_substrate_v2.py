"""
test_substrate_v2.py — SCP Substrate v2 (verified reader) test suite

Function:
    Executable expression of SPEC_V2.md. Written before serve_v2.py
    and run red first. Builds a substrate with P9 substrate_v3 and
    seals with P2, then reads it through a live serve_v2 server.

Functions in this file (pytest-collected):
    1. test_verified_claims_drawn
    2. test_tampered_claim_hidden_but_reachable
    3. test_attestation_glow_and_retraction
    4. test_tampered_attestation_does_not_glow
    5. test_page_methods_and_missing_db

Fixtures and helpers:
    6. db      — substrate with two claims
    7. server  — serve_v2 on a free port; yields a GET/POST helper
    8. _seal   — a P2-signed seal-shaped capsule
    9. _tamper — rewrite one stored capsule

Tier:     Tier 1 — Consumer (The Memory)
Spec:     SPEC_V2.md 2.0.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import os
import sqlite3
import sys
import threading
import urllib.error
import urllib.request

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = os.path.dirname(os.path.abspath(__file__))
for _p in (ROOT, os.path.join(ROOT, "..", "substrate-layer")):
    if os.path.abspath(_p) not in sys.path:
        sys.path.insert(0, os.path.abspath(_p))

import substrate_v3  # noqa: E402
import sign_v2  # noqa: E402
import serve_v2  # noqa: E402

KEY = Ed25519PrivateKey.generate()


# 8. _seal
def _seal(decision, ts, note="checked"):
    return sign_v2.sign_capsule({"decision": decision, "action_type": "publish", "subject_id": "x",
                                 "rationale": note, "timestamp": ts, "signature": None}, KEY)


# 9. _tamper
def _tamper(db, table, id_col, row_id, old, new):
    conn = sqlite3.connect(db)
    with conn:
        text = conn.execute(f"SELECT capsule FROM {table} WHERE {id_col}=?", (row_id,)).fetchone()[0]
        conn.execute(f"UPDATE {table} SET capsule=? WHERE {id_col}=?", (text.replace(old, new), row_id))
    conn.close()


# 6. db
@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "forge.db")
    substrate_v3.init_db(path)
    a = substrate_v3.write_claim(path, {"subject": "sky", "object": "blue", "FACT": "The sky is blue",
                                        "face": "FACT"}, KEY)
    b = substrate_v3.write_claim(path, {"subject": "tide", "object": "late", "UNKNOWN": "Why late?",
                                        "face": "UNKNOWN"}, KEY)
    return path, a, b


# 7. server
@pytest.fixture
def server(db):
    srv = serve_v2.make_server(db[0], port=0, quiet=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"

    def call(path, method="GET"):
        req = urllib.request.Request(base + path, method=method)
        try:
            with urllib.request.urlopen(req) as r:
                body = r.read()
                return r.status, body
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    yield call
    srv.shutdown()
    srv.server_close()


# 1. test_verified_claims_drawn
def test_verified_claims_drawn(db, server):
    status, body = server("/api/claims")
    claims = json.loads(body)
    assert status == 200 and len(claims) == 2
    assert all(c["verified"] is True for c in claims)
    assert {c["faces"]["UNKNOWN"] is not None for c in claims} == {True, False}


# 2. test_tampered_claim_hidden_but_reachable
def test_tampered_claim_hidden_but_reachable(db, server):
    path, a, b = db
    _tamper(path, "claims", "claim_id", b, "late", "early")
    claims = json.loads(server("/api/claims")[1])
    assert [c["claim_id"] for c in claims] == [a]
    health = json.loads(server("/api/health")[1])
    assert health["verified"] == 1 and health["unverified"] == 1
    status, body = server(f"/api/claims/{b}")
    one = json.loads(body)
    assert status == 200 and one["verified"] is False and one["verify_error"]


# 3. test_attestation_glow_and_retraction
def test_attestation_glow_and_retraction(db, server):
    path, a, _ = db
    substrate_v3.link_attestation(path, a, _seal("approve", 1_700_000_000.0), KEY)
    claim = [c for c in json.loads(server("/api/claims")[1]) if c["claim_id"] == a][0]
    assert claim["status"] == "attested"
    substrate_v3.link_attestation(path, a, _seal("refuse", 1_700_000_500.0, "withdrawn"), KEY)
    claim = [c for c in json.loads(server("/api/claims")[1]) if c["claim_id"] == a][0]
    assert claim["status"] == "retracted" and claim["attestation"]["retracted"] == "withdrawn"


# 4. test_tampered_attestation_does_not_glow
def test_tampered_attestation_does_not_glow(db, server):
    path, a, _ = db
    ev = substrate_v3.link_attestation(path, a, _seal("approve", 1_700_000_000.0), KEY)
    _tamper(path, "evidence", "evidence_id", ev, "checked", "forged!")
    claim = [c for c in json.loads(server("/api/claims")[1]) if c["claim_id"] == a][0]
    assert claim["status"] == "draft" and claim["evidence_count"] == 0


# 5. test_page_methods_and_missing_db
def test_page_methods_and_missing_db(db, server, tmp_path):
    assert server("/")[0] == 200
    assert server("/api/claims", method="POST")[0] == 405
    srv = serve_v2.make_server(str(tmp_path / "absent.db"), port=0, quiet=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{srv.server_address[1]}/api/claims"
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(url)
        assert e.value.code == 503
    finally:
        srv.shutdown()
        srv.server_close()
    assert not (tmp_path / "absent.db").exists()
