# SPEC V4 — scp-substrate (Tier 1: SCP Substrate, keyword clusters)

SPEC_V4.md — specification for serve_v4.py, the layer above SCP Substrate v3.0.0.

Function:
    Gives the field a second way to cluster: by keywords drawn from the
    cubes' own text, as a "Keywords" choice beside "Tags" in the field's
    "Cluster by" bar. serve.py, serve_v2.py, serve_v3.py and the frontend
    in static/view/ are frozen and not edited. Where this document is
    silent, SPEC_V3.md applies.

Tier:      Tier 1 — Consumer (The Memory)
Depends:   serve_v3.py (SPEC_V3 3.0.0)
Consumed:  The operator, The Legacy (embedded Field)
Version:   SPEC 4.0.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. Why v4

The frontend already supports server-supplied cluster modes (a `MODES`
object: each mode a list of clusters with member ids, and optional
links), and clusters by `tags` by default. v1's `render_page` always
injects `MODES = {}`, and claims written by the Cockpit carry no tags,
so the field fell back to one cluster per subject. James asked for
clusters "based on key words or tags".

## 2. Keywords

For each cube, its **keywords** are the distinct words of its subject,
object and every filled face, lower-cased, at least 4 characters,
made of letters, digits and hyphens. A hyphenated word also counts each
of its parts ("ledger-layer" → "ledger-layer", "ledger", "layer").
Words in the stop list (§2.1) are dropped. Each keyword is then lightly
stemmed so inflections meet: "-ied" becomes "-y", otherwise "-ing",
"-ed" or "-s" (but not "-ss") comes off, only when at least 4 characters
remain ("signed", "signs", "signing" → "sign"; "verified" → "verify").

**A subject is the unit** (James: "a repo is a subject with its own
cluster of claims"). Every claim with the same subject stays together;
a subject's keywords are the union of its claims' keywords. A claim
with no subject is its own unit.

A keyword is a **candidate** if it occurs in at least 2 subjects and in
no more than 30% of them (rounded up, at least 2). Clusters are chosen
greedily: repeatedly take the candidate shared by the most subjects not
yet placed (ties alphabetical); if it covers fewer than 2 unplaced
subjects, stop. Every subject left over goes in a cluster named `other`.
A cluster's members are all the claims of its subjects. The result is
deterministic for the same cubes.

**Links:** two subjects in different clusters that share at least 2
candidate keywords are linked, drawn between each subject's first
claim; the link's `term` is their alphabetically first shared candidate.

In the field's default "Tags" mode a claim with no tags is tagged with
its subject, so each subject with 2 or more claims already forms its own
cluster there; "Keywords" then groups those subjects.

### 2.1 Stop list

Common English words and stack boilerplate that would join everything
(a word is dropped if it, or its stem, is listed):
`that with from this have their only every each into when what will
than then them they also does over under after before about which
there where while being been were your more most some such same
other just tests test pass frozen layer version built claim claims
cube cubes depends depend notes note writes write never should could
would must still nothing twice zero three four five first last next
none using used uses make makes made like need needs want work works
import imports between live read reads`.

## 3. MODES

`modes(cubes)` returns `{"KEYWORDS": {"clusters": [{"name", "members":
[id, …]}, …], "links": [{"a", "b", "lens": "CONTEXT", "term"}, …]}}`
(the frontend's own mode shape). Every cube is a member of exactly one
cluster. `render_page(cubes, modes)` fills the template exactly as v1
does, but injects `MODES` instead of `{}`. The field then shows
"Keywords" in its "Cluster by" bar; "Tags" stays the default.

## 4. Tests (test_serve_v4.py)

- Every cube is in exactly one KEYWORDS cluster; claims of one subject
  are always in the same cluster, and a word shared only within one
  subject never forms a cluster; every cluster but
  `other` has at least 2 members, and its name occurs in each member's
  keywords.
- Stop words and over-common words never name a cluster; the result is
  deterministic; inflections stem to one keyword.
- Links join cubes in different clusters sharing at least 2 candidates.
- The page served by v4 injects `MODES` with KEYWORDS (and still no
  numeric times, as v3); `/api/claims` is v3's.
- If `node` is installed, the injected `MODES` parses as JavaScript.

---

## Document control

- **SPEC 4.0.0** — 2026-11-13, by the VS Code AI (James: "lets see if
  we can get them to cluster based on key words or tags").
