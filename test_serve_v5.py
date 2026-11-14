"""
test_serve_v5.py — SCP Substrate v5 (subjects orbit you) test suite

Function:
    Executable expression of SPEC_V5.md. Written before serve_v5.py and
    run red first, on a real P9 v4 database.

Functions in this file (pytest-collected):
    1. test_orbs
    2. test_centre
    3. test_dependency_links
    4. test_page
    5. test_api_claims_unchanged

Helpers:
    6. db     — fixture: P9 v4 with a person, one registered subject,
                claims on three subjects and two dependency claims
    7. _claim — write one affirmed claim

Tier:     Tier 1 — Consumer (The Memory)
Spec:     SPEC_V5.md 5.0.0
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
import serve_v5  # noqa: E402

KEY = Ed25519PrivateKey.generate()


# 7. _claim
def _claim(db, subject, obj, text, predicate=None):
    cap = {"subject": subject, "object": obj, "FACT": text, "face": "FACT", "polarity": "affirm"}
    if predicate:
        cap["predicate"] = predicate
    return substrate_v4.write_claim(db, cap, KEY)


# 6. db
@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "forge.db")
    substrate_v4.init_db(path)
    ids = {"person": substrate_v4.add_entity(path, "James Gilbert", KEY, kind="person"),
           "hal_subject": substrate_v4.add_subject(path, "hal-layer", KEY, kind="repo")}
    ids["ledger"] = _claim(path, "ledger-layer", "P4 Ledger", "The hash-chained ledger.")
    ids["hal"] = _claim(path, "HAL-layer", "P15 HAL", "Human accountability.")
    ids["hal2"] = _claim(path, "hal-layer", "status", "hal_v2 at 1.1.0.")
    ids["dep"] = _claim(path, "hal-layer", "ledger-layer", "HAL appends seals to the ledger.", "depends on")
    ids["dep_self"] = _claim(path, "hal-layer", "hal-layer", "Self.", "Depends On")
    ids["dep_none"] = _claim(path, "hal-layer", "the moon", "Nothing.", "depends on")
    ids["legacy"] = _claim(path, "the-legacy", "hal-layer", "The Legacy shows HAL seals.", " depends  on ")
    return path, ids


# 1. test_orbs
def test_orbs(db):
    path, ids = db
    cubes = serve_v5.read_claims(path)
    hubs, things, user = serve_v5.orbits(cubes, serve_v5.things(path))
    assert [h["name"] for h in hubs] == ["ledger-layer", "hal-layer", "the-legacy"]
    hal = hubs[1]
    assert hal["id"] == ids["hal_subject"] and hal["kind"] == "subject · repo"
    assert hubs[0]["id"] == "subject:ledger-layer" and hubs[0]["kind"] == "subject"
    assert all(h["parts"] == [] and h["nets"] == [] for h in hubs)
    by_id = {c["id"]: c for c in cubes}
    assert by_id[ids["hal"]]["hub"] == {"entity": hal["id"], "part": None}  # "HAL-layer" is the same subject
    assert all(c["subjects"] == [c["hub"]["entity"]] and c["entities"] == [] for c in cubes)
    assert [s["id"] for s in things["subjects"]] == [h["id"] for h in hubs]


# 2. test_centre
def test_centre(db, tmp_path):
    path, ids = db
    cubes = serve_v5.read_claims(path)
    hubs, things, user = serve_v5.orbits(cubes, serve_v5.things(path))
    assert user == "James Gilbert" and all(h["builders"] == ["James Gilbert"] for h in hubs)
    [me] = things["entities"]
    assert me["you"] is True and me["parts"] == [h["id"] for h in hubs] and me["kind"] == "person"
    bare = str(tmp_path / "bare.db")
    substrate_v4.init_db(bare)
    _claim(bare, "sky", "blue", "The sky is blue over the sea.")
    hubs, things, user = serve_v5.orbits(serve_v5.read_claims(bare), serve_v5.things(bare))
    assert user == "You" and hubs[0]["builders"] == [] and things["entities"] == []


# 3. test_dependency_links
def test_dependency_links(db):
    path, ids = db
    cubes = serve_v5.read_claims(path)
    hubs, _, _ = serve_v5.orbits(cubes, serve_v5.things(path))
    links = serve_v5.dependency_links(cubes)
    assert links == [{"a": ids["dep"], "b": ids["ledger"], "lens": "CONTEXT", "term": "depends on"},
                     {"a": ids["legacy"], "b": ids["hal"], "lens": "CONTEXT", "term": "depends on"}]


# 4. test_page
def test_page(db):
    path, _ = db
    cubes = serve_v5.read_claims(path)
    hubs, things, user = serve_v5.orbits(cubes, serve_v5.things(path))
    modes = serve_v5.modes(cubes)
    assert set(modes) == {"ALL", "KEYWORDS"} and len(modes["ALL"]["links"]) == 2
    assert sorted(m for cl in modes["ALL"]["clusters"] for m in cl["members"]) == sorted(c["id"] for c in cubes)
    html = serve_v5.render_page(cubes, modes, hubs, things, user)
    for slot in ("HUBS", "THINGS", "MODES"):
        assert json.loads(re.search(rf"const {slot} = (.*?);\n", html).group(1))
    assert re.search(r'const USER = "James Gilbert";', html)
    assert not re.search(r'"(at|filled_at|created|created_at)":\s*-?\d', html)
    if shutil.which("node"):
        js = "\n".join(re.search(rf"(const {s} = .*?;)\n", html).group(1) for s in ("HUBS", "THINGS", "MODES", "USER"))
        r = subprocess.run(["node", "-e", js + "\nconsole.log(HUBS.length)"], capture_output=True, text=True, timeout=60)
        assert r.returncode == 0 and r.stdout.strip() == "3", r.stderr


# 5. test_api_claims_unchanged
def test_api_claims_unchanged(db):
    path, _ = db
    assert serve_v5.read_claims(path) == serve_v3.read_claims(path)
