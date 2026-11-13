"""
serve_v4.py — SCP Substrate v4, keyword clusters

Function:
    The layer above SCP Substrate v3.0.0 (serve_v3.py), and the entry
    point to run from v4 on. Reads exactly as v3, then works out a
    KEYWORDS cluster mode from the cubes' own words and injects it as the
    frontend's MODES, so the field's "Cluster by" bar gains "Keywords"
    beside "Tags" (SPEC_V4.md).

    serve.py, serve_v2.py, serve_v3.py and static/view/ are frozen and
    not edited.

Public API:
    1. keywords(cube) -> set[str]
    2. modes(cubes) -> dict          — subjects grouped by shared keywords
    3. render_page(cubes, modes=None, static_dir=STATIC_DIR, user="You") -> str
    4. read_claims, read_claim       (v3's, re-exported)
    5. KeywordHandler                — v3's handler, page from 3
    6. make_server(db_path, port=8085, quiet=False)
    7. main(argv=None)

Internal helpers:
    8. _words — the raw words of one string
    9. _stem  — a light suffix stemmer

Tier:      Tier 1 — Consumer (The Memory)
Depends:   serve_v3.py (SPEC_V3 3.0.0), serve.py (template, safe_json)
Spec:      SPEC_V4.md 4.0.0 (over SPEC_V3.md 3.0.0)
Version:   4.0.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)
"""

import argparse
import math
import os
import re
import sqlite3
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import serve as _v1  # noqa: E402
import serve_v3 as _v3  # noqa: E402

read_claims = _v3.read_claims
read_claim = _v3.read_claim
STATIC_DIR = _v1.STATIC_DIR
DEFAULT_PORT = _v1.DEFAULT_PORT
HOST = _v1.HOST

STOP = frozenset("""that with from this have their only every each into when what will
than then them they also does over under after before about which there where while
being been were your more most some such same other just tests test pass frozen layer
version built claim claims cube cubes depends depend notes note writes write never
should could would must still nothing twice zero three four five first last next none
using used uses make makes made like need needs want work works import imports between
live read reads""".split())
SHARE = 0.3  # SPEC_V4 §2: a candidate is in no more than 30% of cubes


# ---------------------------------------------------------------------------
# 8. _words
# ---------------------------------------------------------------------------
def _words(text):
    return re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", str(text or "").lower())


# ---------------------------------------------------------------------------
# 9. _stem
#    SPEC_V4 §2: -ied → -y, then -ing, -ed or -s (not -ss) off, only when
#    at least 4 characters remain. "signed", "signs", "signing" → "sign".
# ---------------------------------------------------------------------------
def _stem(w):
    if w.endswith("ied") and len(w) >= 6:
        return w[:-3] + "y"
    for suffix in ("ing", "ed", "s"):
        if w.endswith(suffix) and not w.endswith("ss") and len(w) - len(suffix) >= 4:
            return w[:-len(suffix)]
    return w


# ---------------------------------------------------------------------------
# 1. keywords
#    SPEC_V4 §2: subject, object and every filled face; ≥ 4 characters;
#    hyphenated words also count their parts; stop words dropped; stemmed.
# ---------------------------------------------------------------------------
def keywords(cube):
    texts = [cube.get("subject"), cube.get("object")]
    texts += [f.get("content") for f in (cube.get("faces") or {}).values() if f]
    out = set()
    for text in texts:
        for word in _words(text):
            for w in [word] + (word.split("-") if "-" in word else []):
                if len(w) >= 4 and w not in STOP and _stem(w) not in STOP:
                    out.add(_stem(w))
    return out


# ---------------------------------------------------------------------------
# 2. modes
#    SPEC_V4 §2–3: a subject (a repo) is one unit with all its claims.
#    Greedy clusters of subjects by the most-shared candidate, the rest in
#    "other"; links between subjects in different clusters sharing ≥ 2
#    candidates, drawn between each subject's first claim.
# ---------------------------------------------------------------------------
def modes(cubes):
    claims = {}  # subject -> claim ids, in cube order
    kws = {}
    for c in cubes:
        subj = c.get("subject") or c["id"]
        claims.setdefault(subj, []).append(c["id"])
        kws.setdefault(subj, set()).update(keywords(c))
    subjects = list(claims)
    holders = {}
    for subj in subjects:
        for w in kws[subj]:
            holders.setdefault(w, set()).add(subj)
    cap = max(2, math.ceil(SHARE * len(subjects)))
    cand = {w: h for w, h in holders.items() if 2 <= len(h) <= cap}

    groups, placed = [], set()
    while True:
        best = min(cand, key=lambda w: (-len(cand[w] - placed), w), default=None)
        if best is None or len(cand[best] - placed) < 2:
            break
        members = [x for x in subjects if x in cand[best] and x not in placed]
        groups.append((best, members))
        placed.update(members)
    rest = [x for x in subjects if x not in placed]
    if rest:
        groups.append(("other", rest))
    clusters = [{"name": name, "members": [cid for x in members for cid in claims[x]]} for name, members in groups]

    home = {x: name for name, members in groups for x in members}
    skw = {x: kws[x] & cand.keys() for x in subjects}
    links = []
    for i, a in enumerate(subjects):
        for b in subjects[i + 1:]:
            shared = skw[a] & skw[b]
            if home[a] != home[b] and len(shared) >= 2:
                links.append({"a": claims[a][0], "b": claims[b][0], "lens": "CONTEXT", "term": min(shared)})
    return {"KEYWORDS": {"clusters": clusters, "links": links}}


# ---------------------------------------------------------------------------
# 3. render_page
#    v1's render_page, restated with MODES filled (v1 always injects {}).
# ---------------------------------------------------------------------------
def render_page(cubes, modes=None, static_dir=STATIC_DIR, user="You"):
    read = lambda name: (Path(static_dir) / name).read_text(encoding="utf-8")
    data = {"CUBES": _v1.safe_json(cubes), "MODES": _v1.safe_json(modes or {}), "USER": _v1.safe_json(user),
            "HUBS": "[]", "THINGS": "{}", "LENSES": _v1.safe_json(list(_v1.FACES))}
    grid = re.sub(r'/\*(CUBES|MODES|USER|HUBS|THINGS|LENSES)\*/(\[[^\]]*\]|\{\}|"[^"]*")',
                  lambda m: data[m.group(1)], read("view_grid.js"))
    field = "(() => {\n" + "\n".join(read(f"view_field_{p}.js") for p in _v1.FIELD_PARTS) + "\n})();\n"
    parts = {"STYLE": read("view_style.css"), "GRID": grid, "FIELD": field, "BAR": read("view_bar.js")}
    return re.sub(r"/\*(STYLE|GRID|FIELD|BAR)\*/", lambda m: parts[m.group(1)], read("view_template.html"))


# ---------------------------------------------------------------------------
# 5. KeywordHandler
#    v3's handler; only the page route changes.
# ---------------------------------------------------------------------------
class KeywordHandler(_v3.IsoHandler):

    # 5.1 _route
    def _route(self, head_only):
        if unquote(urlsplit(self.path).path) in ("/", "/index.html"):
            try:
                cubes = read_claims(self.db_path)
            except (sqlite3.Error, FileNotFoundError) as e:
                return self._json(503, {"error": "database unavailable", "detail": str(e)}, head_only)
            return self._send(200, render_page(cubes, modes(cubes)), _v1.TYPES[".html"], head_only)
        return super()._route(head_only)


# ---------------------------------------------------------------------------
# 6. make_server
# ---------------------------------------------------------------------------
def make_server(db_path, port=DEFAULT_PORT, quiet=False):
    handler = type("BoundKeywordHandler", (KeywordHandler,), {"db_path": db_path, "quiet": quiet})
    return ThreadingHTTPServer((HOST, port), handler)


# ---------------------------------------------------------------------------
# 7. main
#    python serve_v4.py [--db PATH] [--port N].
# ---------------------------------------------------------------------------
def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only, verified SCP Substrate viewer (v4, keyword clusters).")
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
