"""
test_serve_v7.py — SCP Substrate v7 (the field on a phone) test suite

Function:
    Executable expression of SPEC_V7.md. Written before view_v3's fixes
    and run red first against an unmodified copy of view_v2.

Functions in this file (pytest-collected):
    1. test_page_and_api
    2. test_entity_link_opens_orb
    3. test_phone_width
    4. test_names_do_not_overlap
    5. test_frozen_view_untouched

Helpers:
    6. db       — fixture: twelve subjects, claims and dependency links
    7. _claim   — write one affirmed claim
    8. _browser — Edge or Chrome, else None
    9. _render  — open a page headless and read back what its probe wrote

Tier:     Tier 1 — Consumer (The Memory)
Spec:     SPEC_V7.md 7.0.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import html as _html
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
import serve_v7  # noqa: E402

KEY = Ed25519PrivateKey.generate()
NAMES = ["ledger-layer", "hal-layer", "the-legacy", "scp-substrate", "substrate-layer", "sign-layer",
         "envelope-layer", "record-layer", "explorer-d334-forge", "leighton-engine-layer", "the-weaver", "sc-os"]

# Writes what the page shows into document.title, which --dump-dom returns, and
# to the parent page when it is shown in a phone-sized frame
REPORT = """<script>function report(o) {
  var s = JSON.stringify(o); document.title = s;
  if (parent !== window) parent.postMessage(s, "*");
}</script>"""
# A phone: Edge headless will not make a window narrower than about 500 px,
# so the page is shown in a 412 x 915 frame inside a wider one
PHONE = """<!doctype html><title>waiting</title><iframe src="%s" style="width:412px;height:915px;border:0"></iframe>
<script>addEventListener("message", function (e) { document.title = e.data; });</script>"""
OVERFLOW = """<script>setTimeout(function () {
  var W = innerWidth, bad = [];
  document.querySelectorAll("body *").forEach(function (e) {
    var r = e.getBoundingClientRect();
    if (!r.width || !r.height || r.right <= W + 1) return;
    for (var p = e.parentElement; p && p !== document.body; p = p.parentElement) {
      var o = getComputedStyle(p).overflowX;
      if ((o === "auto" || o === "scroll") && p.getBoundingClientRect().right <= W + 1) return;
    }
    bad.push((e.id || e.className || e.tagName) + " ends at " + Math.round(r.right));
  });
  report({ W: W, bad: bad.slice(0, 20) });
}, %d);</script>"""
PANEL = """<script>setTimeout(function () {
  var p = document.getElementById("panel"), h = p.querySelector("h3");
  report({ open: !p.hidden, name: h ? h.textContent : null });
}, 1500);</script>"""
NAMED = """<script>setTimeout(function () {
  report({ boxes: window.cubeField.named ? window.cubeField.named() : null });
}, 2500);</script>"""


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
    substrate_v4.add_entity(path, "James Gilbert", KEY, kind="person")
    ids = {}
    for i, name in enumerate(NAMES):
        substrate_v4.add_subject(path, name, KEY)
        ids[name] = _claim(path, name, f"P{i} status", f"The {name} is built and green on the laptop.")
        _claim(path, name, "purpose", f"What the {name} is for, in a long sentence that wraps on a phone.")
    for a, b in zip(NAMES, NAMES[1:]):
        _claim(path, a, b, f"The {a} reads from the {b}.", "depends on")
    return path, ids


# 8. _browser
def _browser():
    for name in ("msedge", "chrome", "google-chrome", "chromium", "chromium-browser"):
        if shutil.which(name):
            return shutil.which(name)
    for path in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                 r"C:\Program Files\Google\Chrome\Application\chrome.exe"):
        if os.path.exists(path):
            return path
    return None


# 9. _render
def _render(tmp_path, page, probe, size, hash_="", phone=False):
    browser = _browser()
    if not browser:
        pytest.skip("no headless browser (Edge or Chrome) on this device")
    file = tmp_path / "page.html"
    file.write_text(page.replace("</body>", REPORT + probe + "</body>"), encoding="utf-8")
    url = file.as_uri() + hash_
    if phone:
        wrap = tmp_path / "phone.html"
        wrap.write_text(PHONE % ("page.html" + hash_), encoding="utf-8")
        url, size = wrap.as_uri(), "1000,1000"
    r = subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
                        f"--user-data-dir={tmp_path / 'profile'}", f"--window-size={size}",
                        "--virtual-time-budget=4000", "--enable-logging=stderr", "--v=0", "--dump-dom", url],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    title = re.search(r"<title>(.*?)</title>", r.stdout, re.S)
    errors = [line for line in r.stderr.splitlines() if "Uncaught" in line]
    try:
        return json.loads(_html.unescape(title.group(1))), errors
    except (AttributeError, ValueError):
        return None, errors


# 1. test_page_and_api
def test_page_and_api(db):
    path, ids = db
    html = serve_v7.page(path)
    assert "view_v3 (SPEC_V7.md" in html and "function stepHubs" in html
    assert serve_v7.read_claims(path) == serve_v3.read_claims(path)
    if shutil.which("node"):
        js = "\n".join(re.findall(r"<script>(.*?)</script>", html, re.S))
        script = os.path.join(os.path.dirname(path), "page.js")
        with open(script, "w", encoding="utf-8") as f:
            f.write(js)
        r = subprocess.run(["node", "--check", script], capture_output=True, text=True, timeout=60)
        assert r.returncode == 0, r.stderr


# 2. test_entity_link_opens_orb
def test_entity_link_opens_orb(db, tmp_path):
    path, _ = db
    hal = next(s["id"] for s in substrate_v4.list_subjects(path) if s["name"] == "hal-layer")
    shown, errors = _render(tmp_path, serve_v7.page(path), PANEL, "1400,900", "#entity:" + hal)
    assert not errors, errors
    assert shown == {"open": True, "name": "hal-layer"}


# 3. test_phone_width
def test_phone_width(db, tmp_path):
    path, _ = db
    shown, errors = _render(tmp_path, serve_v7.page(path), OVERFLOW % 2000, "412,915", phone=True)
    assert not errors, errors
    assert shown and shown["W"] == 412 and shown["bad"] == [], shown


# 4. test_names_do_not_overlap
@pytest.mark.parametrize("size,phone,least", [("1400,900", False, len(NAMES) // 2), ("412,915", True, 3)])
def test_names_do_not_overlap(db, tmp_path, size, phone, least):
    path, _ = db
    shown, errors = _render(tmp_path, serve_v7.page(path), NAMED, size, phone=phone)
    assert not errors, errors
    boxes = (shown or {}).get("boxes")
    assert boxes and len(boxes) >= least, shown
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            assert not (a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]), (a, b)


# 5. test_frozen_view_untouched
def test_frozen_view_untouched():
    r = subprocess.run(["git", "status", "--porcelain", "static/view"], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip() == ""
