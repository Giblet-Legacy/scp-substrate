"""
test_serve_v3.py — SCP Substrate v3 (ISO timestamps for the field) test suite

Function:
    Executable expression of SPEC_V3.md. Written before serve_v3.py and
    run red first. Writes an attested claim with real P9 code, then
    checks what the field receives from v2 (the defect) and v3 (fixed).

Functions in this file (pytest-collected):
    1. test_attestation_time_is_iso
    2. test_every_time_is_a_string
    3. test_page_has_no_numeric_times
    4. test_frontend_stamps_run

Fixtures and helpers:
    5. db     — substrate with an attested claim and a plain one
    6. _seal  — a P2-signed seal-shaped capsule
    7. _times — every time field in one adapted claim

Tier:     Tier 1 — Consumer (The Memory)
Spec:     SPEC_V3.md 3.0.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = os.path.dirname(os.path.abspath(__file__))
for _p in (ROOT, os.path.join(ROOT, "..", "substrate-layer")):
    if os.path.abspath(_p) not in sys.path:
        sys.path.insert(0, os.path.abspath(_p))

import substrate_v3  # noqa: E402
import sign_v2  # noqa: E402
import serve_v2  # noqa: E402
import serve_v3  # noqa: E402

KEY = Ed25519PrivateKey.generate()
SEAL_TS = 1_794_607_496.9122221


# 6. _seal
def _seal():
    return sign_v2.sign_capsule({"decision": "approve", "action_type": "publish", "subject_id": "x",
                                 "rationale": "checked", "timestamp": SEAL_TS, "signature": None}, KEY)


# 7. _times
def _times(claim):
    out = [claim["created"], claim["created_at"]]
    for face in claim["faces"].values():
        if face:
            out += [face["at"], face["filled_at"]]
    if claim["attestation"]:
        out.append(claim["attestation"]["at"])
    return out


# 5. db
@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "forge.db")
    substrate_v3.init_db(path)
    sky = substrate_v3.write_claim(path, {"subject": "sky", "object": "blue", "FACT": "The sky is blue",
                                          "face": "FACT", "polarity": "affirm"}, KEY)
    substrate_v3.write_claim(path, {"subject": "sea", "object": "deep", "CONTEXT": "The sea is deep",
                                    "face": "CONTEXT", "polarity": "affirm"}, KEY)
    substrate_v3.link_attestation(path, sky, _seal(), KEY)
    return path, sky


# 1. test_attestation_time_is_iso
def test_attestation_time_is_iso(db):
    path, sky = db
    v2 = [c for c in serve_v2.read_claims(path) if c["claim_id"] == sky][0]
    assert isinstance(v2["attestation"]["at"], float)  # the defect, pinned
    v3 = [c for c in serve_v3.read_claims(path) if c["claim_id"] == sky][0]
    at = v3["attestation"]["at"]
    assert isinstance(at, str)
    assert datetime.fromisoformat(at) == datetime.fromtimestamp(SEAL_TS, timezone.utc)
    assert v3["status"] == "attested"
    one = serve_v3.read_claim(path, sky)
    assert isinstance(one["attestation"]["at"], str)


# 2. test_every_time_is_a_string
def test_every_time_is_a_string(db):
    path, _ = db
    for claim in serve_v3.read_claims(path):
        for t in _times(claim):
            assert isinstance(t, str) and datetime.fromisoformat(t), (claim["claim_id"], t)


# 3. test_page_has_no_numeric_times
def test_page_has_no_numeric_times(db):
    path, _ = db
    html = serve_v3.render_page(serve_v3.read_claims(path))
    assert '"at":' in html
    assert not re.search(r'"(at|filled_at|created|created_at)":\s*-?\d', html)


# 4. test_frontend_stamps_run
@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_frontend_stamps_run(db):
    path, _ = db
    cubes = json.dumps(serve_v3.read_claims(path))
    js = ("const CUBES = " + cubes + ";\n"
          "function stampsOf(c) { const faces = Object.values(c.faces).filter(Boolean).map(f => f.at);\n"
          "  return [c.created, ...faces, c.attestation && c.attestation.at].filter(Boolean); }\n"
          "const seen = new Set(CUBES.flatMap(stampsOf).map(t => t.slice(0, 16)));\n"
          "console.log(seen.size);\n")
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert int(r.stdout.strip()) >= 1
