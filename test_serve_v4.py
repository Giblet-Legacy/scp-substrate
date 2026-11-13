"""
test_serve_v4.py — SCP Substrate v4 (keyword clusters) test suite

Function:
    Executable expression of SPEC_V4.md. Written before serve_v4.py and
    run red first. Uses adapted cubes built by hand (the shape v3 serves)
    for the clustering rules, and a real P9 substrate for the page.

Functions in this file (pytest-collected):
    1. test_every_cube_in_one_cluster
    2. test_stop_and_common_words_never_cluster
    3. test_links
    4. test_page_injects_modes
    5. test_modes_parse_as_javascript
    8. test_subject_is_the_unit

Helpers:
    6. _cube — a minimal adapted cube
    7. CUBES — six cubes with known shared words

Tier:     Tier 1 — Consumer (The Memory)
Spec:     SPEC_V4.md 4.0.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import os
import re
import shutil
import subprocess
import sys

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = os.path.dirname(os.path.abspath(__file__))
for _p in (ROOT, os.path.join(ROOT, "..", "substrate-layer")):
    if os.path.abspath(_p) not in sys.path:
        sys.path.insert(0, os.path.abspath(_p))

import substrate_v3  # noqa: E402
import serve_v4  # noqa: E402


# 6. _cube
def _cube(cid, subject, obj, **faces):
    full = {f: None for f in ("FACT", "COUNTER", "OPINION", "FICTION", "CONTEXT", "UNKNOWN")}
    for k, v in faces.items():
        full[k] = {"content": v, "at": "2026-11-13T00:00:00+00:00", "filled_at": "2026-11-13T00:00:00+00:00"}
    return {"id": cid, "claim_id": cid, "subject": subject, "object": obj, "faces": full}


# 7. CUBES
CUBES = [
    _cube("a", "envelope-layer", "P1 Envelope", FACT="Canonical JSON and Ed25519 signing", CONTEXT="Frozen layer"),
    _cube("b", "sign-layer", "P2 Sign", FACT="Signing capsules with Ed25519", CONTEXT="Frozen layer"),
    _cube("c", "ledger-layer", "P4 Ledger", FACT="The hash-chained ledger", CONTEXT="Frozen layer"),
    _cube("d", "store-layer", "P8 Store", FACT="A mirror of the ledger in SQLite", CONTEXT="Frozen layer"),
    _cube("e", "the-weaver", "the Weaver", FACT="A morning briefing from fading dreams"),
    _cube("f", "lllm", "the Voice", FACT="Answers with citations and a trace"),
]


# 1. test_every_cube_in_one_cluster
def test_every_cube_in_one_cluster():
    mode = serve_v4.modes(CUBES)["KEYWORDS"]
    members = [m for cl in mode["clusters"] for m in cl["members"]]
    assert sorted(members) == sorted(c["id"] for c in CUBES)
    names = {cl["name"]: cl["members"] for cl in mode["clusters"]}
    assert set(names["ed25519"]) == {"a", "b"} and set(names["ledger"]) == {"c", "d"}
    assert set(names["other"]) == {"e", "f"}
    for cl in mode["clusters"]:
        if cl["name"] != "other":
            assert len(cl["members"]) >= 2
            for m in cl["members"]:
                assert cl["name"] in serve_v4.keywords([c for c in CUBES if c["id"] == m][0])


# 2. test_stop_and_common_words_never_cluster
def test_stop_and_common_words_never_cluster():
    names = [cl["name"] for cl in serve_v4.modes(CUBES)["KEYWORDS"]["clusters"]]
    assert "frozen" not in names and "layer" not in names  # stop words
    common = CUBES + [_cube(f"x{i}", f"thing{i}", "widget", FACT="common widget") for i in range(10)]
    assert "widget" not in [cl["name"] for cl in serve_v4.modes(common)["KEYWORDS"]["clusters"]]  # > 40%
    assert serve_v4.modes(CUBES) == serve_v4.modes(list(CUBES))
    kw = serve_v4.keywords(CUBES[2])
    assert {"ledger-layer", "ledger", "hash-chain", "hash", "chain"} <= kw and "the" not in kw
    assert {"sign"} == serve_v4.keywords(_cube("s", "signs", "signed", FACT="signing"))


# 3. test_links
def test_links():
    cubes = CUBES + [_cube("g", "canon-verify", "P6", FACT="Checks Ed25519 signing over the hash-chained ledger")]
    mode = serve_v4.modes(cubes)["KEYWORDS"]
    home = {m: cl["name"] for cl in mode["clusters"] for m in cl["members"]}
    for link in mode["links"]:
        assert home[link["a"]] != home[link["b"]] and link["lens"] == "CONTEXT" and link["term"]
    assert any({link["a"], link["b"]} & {"g"} for link in mode["links"])


# 4. test_page_injects_modes
def test_page_injects_modes(tmp_path):
    db = str(tmp_path / "forge.db")
    substrate_v3.init_db(db)
    key = Ed25519PrivateKey.generate()
    for subject, obj, fact in [("sky", "blue", "The sky is blue over the ledger"),
                               ("sea", "blue", "The sea is blue beside the ledger"),
                               ("moon", "cheese", "The moon is cheese")]:
        substrate_v3.write_claim(db, {"subject": subject, "object": obj, "FACT": fact, "face": "FACT",
                                      "polarity": "affirm"}, key)
    cubes = serve_v4.read_claims(db)
    html = serve_v4.render_page(cubes, serve_v4.modes(cubes))
    m = re.search(r"const MODES = (\{.*?\});\n", html)
    assert m and json.loads(m.group(1))["KEYWORDS"]["clusters"]
    assert not re.search(r'"(at|filled_at|created|created_at)":\s*-?\d', html)


# 5. test_modes_parse_as_javascript
@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_modes_parse_as_javascript():
    js = "const MODES = " + json.dumps(serve_v4.modes(CUBES)) + ";\nconsole.log(Object.keys(MODES).join());"
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0 and r.stdout.strip() == "KEYWORDS", r.stderr


# 8. test_subject_is_the_unit
def test_subject_is_the_unit():
    cubes = CUBES + [_cube("c2", "ledger-layer", "status", CONTEXT="Append-only"),
                     _cube("e2", "the-weaver", "status", CONTEXT="Morning dreams fade")]
    mode = serve_v4.modes(cubes)["KEYWORDS"]
    home = {m: cl["name"] for cl in mode["clusters"] for m in cl["members"]}
    assert home["c2"] == home["c"] == "ledger"
    assert home["e2"] == home["e"] == "other"  # "morning", "dream" shared only within the-weaver
