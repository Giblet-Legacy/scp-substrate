"""
test_serve_v8.py — SCP Substrate v8 (you at the centre of what is yours) test suite

Function:
    Executable expression of SPEC_V8.md. Written before serve_v8.py and
    run red first.

Functions in this file (pytest-collected):
    1. test_claims_about_you_orbit_their_object
    2. test_no_person_no_change
    3. test_page_and_api
    4. test_view_v4_is_a_layer
    5. test_page_script_parses

Helpers:
    4. db     — fixture: the person, a repo subject, claims about both
    5. _claim — write one affirmed claim

Tier:     Tier 1 — Consumer (The Memory)
Spec:     SPEC_V8.md 8.0.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import os
import sys
import threading
import urllib.request
import json

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = os.path.dirname(os.path.abspath(__file__))
for _p in (ROOT, os.path.join(ROOT, "..", "substrate-layer")):
    if os.path.abspath(_p) not in sys.path:
        sys.path.insert(0, os.path.abspath(_p))

import substrate_v4  # noqa: E402
import serve_v5  # noqa: E402
import serve_v8  # noqa: E402

KEY = Ed25519PrivateKey.generate()
CAP = "Identity capsule giblets-forge/identity/james-the-giblet-v1"


# 5. _claim
def _claim(db, subject, obj, text, predicate=None, context=None, section=None):
    cap = {"subject": subject, "object": obj, "FACT": text, "face": "FACT", "polarity": "affirm"}
    if section:
        cap["section"] = section
    if context:
        cap["CONTEXT"] = context
    if predicate:
        cap["predicate"] = predicate
    return substrate_v4.write_claim(db, cap, KEY)


# 4. db
@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "forge.db")
    substrate_v4.init_db(path)
    substrate_v4.add_entity(path, "James Gilbert", KEY, kind="person")
    repo = substrate_v4.add_subject(path, "the-legacy", KEY, kind="repo")
    ids = {
        "repo": _claim(path, "the-legacy", "status", "The Legacy is frozen at 1.7.0."),
        "legacy": _claim(path, "James Gilbert", "The-Legacy ", "One page over every consumer.", "is building"),
        "robot": _claim(path, " james gilbert", "SCPBot", "M5StickC, PCA9685, 8 MG90S servos.", "is building",
                        f"{CAP}, hardware and robotics."),
        "nova": _claim(path, "James Gilbert", "Nova_bot", "ESP32 2WD robot.", "built",
                       f"{CAP}, hardware and robotics. repo: x"),
        "origin": _claim(path, "James Gilbert", "origin", "Carpenter by trade.", None, f"{CAP}, origin."),
        "why": _claim(path, "James Gilbert", "why he builds", "For the love of building.", None, f"{CAP}, ethos."),
        "loose": _claim(path, "James Gilbert", "Cockpit", "Rebuilt on the frozen layers.", "built",
                        "Drafted by the VS Code AI; not in the identity capsule."),
        "named": _claim(path, "James Gilbert", "PocketLearner", "M5StickC maze learner.", "built",
                        "Written by hand, no capsule wording.", section="hardware and robotics"),
        "other": _claim(path, "hal-layer", "James Gilbert", "HAL seals carry James's key."),
    }
    return path, repo, ids


# 1. test_claims_about_you_orbit_their_object
def test_claims_about_you_orbit_their_object(db):
    path, repo, ids = db
    cubes = serve_v8.read_claims(path)
    serve_v8._sections(cubes, path)
    hubs, found, user = serve_v8.orbits(cubes, serve_v5.things(path))
    names = sorted(h["name"] for h in hubs)
    assert names == ["about James Gilbert", "hal-layer", "hardware and robotics", "other", "the-legacy"]
    assert user == "James Gilbert"
    by_id = {c["id"]: c for c in cubes}
    legacy_hub = next(h for h in hubs if h["name"] == "the-legacy")
    assert legacy_hub["id"] == repo and "repo" in legacy_hub["kind"]
    assert by_id[ids["legacy"]]["hub"]["entity"] == repo == by_id[ids["repo"]]["hub"]["entity"]
    hw = next(h for h in hubs if h["name"] == "hardware and robotics")
    assert hw["id"] == "section:hardware and robotics" and hw["kind"] == "subject · section"
    assert [(p["name"], p["role"]) for p in hw["parts"]] == [("SCPBot", "is building"), ("Nova_bot", "built"),
                                                             ("PocketLearner", "built")]
    robot = by_id[ids["robot"]]
    assert robot["subject"] == "hardware and robotics" and robot["object"] == "SCPBot"
    assert robot["predicate"] == "is building" and robot["about_you"] is True
    assert robot["hub"] == {"entity": hw["id"], "part": "part:hardware and robotics/scpbot"}
    assert robot["subjects"] == [hw["id"]]
    me = next(h for h in hubs if h["name"] == "about James Gilbert")
    assert [(p["name"], p["role"]) for p in me["parts"]] == [("origin", "about you"), ("why he builds", "about you")]
    assert by_id[ids["why"]]["hub"]["entity"] == me["id"]
    other_hub = next(h for h in hubs if h["name"] == "other")
    assert [p["name"] for p in other_hub["parts"]] == ["Cockpit"]
    assert by_id[ids["legacy"]]["subject"] == "The-Legacy" and by_id[ids["legacy"]]["hub"]["part"] is None
    other = by_id[ids["other"]]
    assert other["subject"] == "hal-layer" and other["object"] == "James Gilbert" and "about_you" not in other
    assert "about_you" not in by_id[ids["repo"]]
    yours = sorted(h["name"] for h in hubs if h.get("yours"))
    assert yours == ["about James Gilbert", "hardware and robotics", "other"]
    you = next(e for e in found["entities"] if e["you"])
    assert you["name"] == "James Gilbert" and len(you["parts"]) == 5


# 2. test_no_person_no_change
def test_no_person_no_change(tmp_path):
    path = str(tmp_path / "forge.db")
    substrate_v4.init_db(path)
    _claim(path, "James Gilbert", "SCPBot", "No person entity is registered.", "is building")
    cubes = serve_v8.read_claims(path)
    hubs, _, user = serve_v8.orbits(cubes, serve_v5.things(path))
    assert [h["name"] for h in hubs] == ["James Gilbert"] and user == "You" and not hubs[0].get("yours")
    assert "about_you" not in cubes[0] and cubes[0]["subject"] == "James Gilbert"


# 3. test_page_and_api
def test_page_and_api(db):
    path, _, ids = db
    html = serve_v8.page(path)
    assert "Pink orbs: yours" in html and "Pink orbs: yours" not in serve_v8._v7.page(path)
    assert "SCPBot" in html and '"about_you": true' in html.replace('"about_you":true', '"about_you": true')
    server = serve_v8.make_server(path, 0, quiet=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        base = f"http://127.0.0.1:{server.server_address[1]}"
        page = urllib.request.urlopen(base + "/").read().decode("utf-8")
        assert "SCPBot" in page
        claims = json.loads(urllib.request.urlopen(base + "/api/claims").read())
        claims = claims.get("claims", claims) if isinstance(claims, dict) else claims
        robot = next(c for c in claims if c["id"] == ids["robot"])
        assert robot["subject"].strip().casefold() == "james gilbert" and "about_you" not in robot
    finally:
        server.shutdown()
        server.server_close()


# 4. test_view_v4_is_a_layer
def test_view_v4_is_a_layer():
    import filecmp
    import subprocess
    v3, v4 = os.path.join(ROOT, "static", "view_v3"), os.path.join(ROOT, "static", "view_v4")
    cmp = filecmp.dircmp(v3, v4)
    assert sorted(cmp.diff_files) == ["view_bar.js", "view_field_draw.js", "view_field_hubs.js",
                                      "view_field_world.js"]
    assert not cmp.left_only and not cmp.right_only
    out = subprocess.run(["git", "status", "--porcelain", "--", "static/view_v3"], cwd=ROOT,
                         capture_output=True, text=True)
    if out.returncode == 0:
        assert out.stdout.strip() == ""


# 5. test_page_script_parses
def test_page_script_parses(db, tmp_path):
    import re
    import shutil
    import subprocess
    node = shutil.which("node")
    if not node:
        pytest.skip("no node on this device")
    path, _, _ = db
    scripts = re.findall(r"<script>(.*?)</script>", serve_v8.page(path), re.S)
    js = tmp_path / "page.js"
    js.write_text("\n;\n".join(scripts), encoding="utf-8")
    r = subprocess.run([node, "--check", str(js)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
