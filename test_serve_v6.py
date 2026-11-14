"""
test_serve_v6.py — SCP Substrate v6 (dependencies as your links) test suite

Function:
    Executable expression of SPEC_V6.md. Written before serve_v6.py and
    run red first, on the v5 fixture's shape.

Functions in this file (pytest-collected):
    1. test_neighbours
    2. test_modes_without_all
    3. test_page_and_api
    6. test_frozen_view_untouched

Helpers:
    4. db     — fixture: claims on three subjects, dependency claims
    5. _claim — write one affirmed claim

Tier:     Tier 1 — Consumer (The Memory)
Spec:     SPEC_V6.md 6.0.0
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

import substrate_v4  # noqa: E402
import serve_v3  # noqa: E402
import serve_v6  # noqa: E402

KEY = Ed25519PrivateKey.generate()


# 5. _claim
def _claim(db, subject, obj, text, predicate=None):
    cap = {"subject": subject, "object": obj, "FACT": text, "face": "FACT", "polarity": "affirm"}
    if predicate:
        cap["predicate"] = predicate
    return substrate_v4.write_claim(db, cap, KEY)


# 4. db
@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "forge.db")
    substrate_v4.init_db(path)
    substrate_v4.add_entity(path, "James Gilbert", KEY, kind="person")
    ids = {"ledger": _claim(path, "ledger-layer", "P4 Ledger", "The hash-chained ledger."),
           "hal": _claim(path, "hal-layer", "P15 HAL", "Human accountability.")}
    ids["dep"] = _claim(path, "hal-layer", "ledger-layer", "HAL appends seals to the ledger.", "depends on")
    ids["dep_self"] = _claim(path, "hal-layer", "hal-layer", "Self.", "depends on")
    ids["dep_none"] = _claim(path, "hal-layer", "the moon", "Nothing.", "depends on")
    ids["legacy"] = _claim(path, "the-legacy", "hal-layer", "The Legacy shows HAL seals.", "depends on")
    return path, ids


# 1. test_neighbours
def test_neighbours(db):
    path, ids = db
    cubes = serve_v6.read_claims(path)
    serve_v6.link_dependencies(cubes)
    serve_v6.link_dependencies(cubes)  # idempotent
    by = {c["id"]: c for c in cubes}
    dep = by[ids["dep"]]
    assert dep["neighbours"] == [ids["ledger"]]
    assert dep["link_words"] == {ids["ledger"]: {"word": "depends on", "from": ids["dep"]}}
    assert dep["link_reasons"] == {ids["ledger"]: "HAL appends seals to the ledger"}  # frontend adds the stop
    assert by[ids["legacy"]]["neighbours"] == [ids["hal"]]
    for k in ("ledger", "hal", "dep_self", "dep_none"):
        assert by[ids[k]]["neighbours"] == [] and by[ids[k]]["link_words"] == {} and by[ids[k]]["link_reasons"] == {}


# 2. test_modes_without_all
def test_modes_without_all(db):
    path, _ = db
    assert set(serve_v6.modes(serve_v6.read_claims(path))) == {"KEYWORDS"}


# 3. test_page_and_api
def test_page_and_api(db):
    path, ids = db
    html = serve_v6.page(path)
    cubes = json.loads(re.search(r"const CUBES = (.*?);\n", html).group(1))
    assert [c["neighbours"] for c in cubes if c["id"] == ids["dep"]] == [[ids["ledger"]]]
    assert "const HUBS = [{" in html and '"ALL"' not in re.search(r"const MODES = (.*?);\n", html).group(1)
    assert serve_v6.read_claims(path) == serve_v3.read_claims(path)
    assert "view_v2 (SPEC_V6.md" in html and "function stepHubs" in html
    if shutil.which("node"):
        js = "\n".join(re.findall(r"<script>(.*?)</script>", html, re.S))
        script = os.path.join(os.path.dirname(path), "page.js")
        with open(script, "w", encoding="utf-8") as f:
            f.write(js)
        r = subprocess.run(["node", "--check", script], capture_output=True, text=True, timeout=60)
        assert r.returncode == 0, r.stderr


# 6. test_frozen_view_untouched
def test_frozen_view_untouched():
    r = subprocess.run(["git", "status", "--porcelain", "static/view"], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip() == ""
