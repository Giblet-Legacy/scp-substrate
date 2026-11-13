# SPEC — scp-substrate (Tier 1: SCP Substrate)

SPEC.md — the specification for SCP Substrate v1.0.0.

Function:
    Records the frozen behaviour of SCP Substrate v1.0.0: a read-only
    viewer that renders P9 Substrate claims as a 3D field of six-faced
    cubes. Behaviour not written here is not promised.

Tier:      Tier 1 — Consumer
Depends:   P8 Store (SQLite), P9 Substrate (claims/evidence), read only
Consumed:  The operator (visual exploration), The Legacy
Version:   SPEC 1.0.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

## 1. Six faces, one per cube side

Every cube shows P13 DataCube's six faces, one per side: FACT,
COUNTER, OPINION, FICTION, CONTEXT, UNKNOWN. UNKNOWN (the Dream
Space) is a cool grey, rgb(130, 130, 140), on the side that was HUMAN
in the harvested frontend.

Human attestation is never a face (P13 §2). It is drawn as the gold
glow (CSS `--seal`) on the cube, and a green strand from the centre.
The harvested build's separate "validation" concept is removed: in
P13, human validation *is* the signed attestation.

Rationale and the full list of frontend edits: HARVEST_DIFF.md.

## 2. Server

- `serve.py`, Python standard library only (`http.server`).
- Binds 127.0.0.1 only. Default port 8085 (`--port`).
- Database: `--db PATH`, else `$FORGE_HOME/forge.db`, else
  `~/.forge/forge.db`.
- Opens SQLite with `mode=ro`. A missing file is reported, never
  created. GET and HEAD only; every other method returns 405 with
  `Allow: GET, HEAD`.
- Static files and the template are read on each request.

### 2.1 Endpoints

| Route | Answer |
| --- | --- |
| `GET /` | The cube field page with data injected (§4) |
| `GET /<file>` | A file directly inside `static/view/`, as is. Nothing outside it. |
| `GET /api/health` | 200 `{status: "ok", db, read_only, claims, active, evidence}` when both P9 tables read; 503 `{status: "error", db, error}` otherwise |
| `GET /api/claims` | Array of every active claim (`is_active = 1`), oldest first, adapted (§3) |
| `GET /api/claims/<id>` | One claim, active or superseded, adapted, plus `capsule` and `evidence`; 404 if absent |

Database errors on the claim routes and `/` return 503.

## 3. Adapting a P9 claim

Each `claims` row, with its `capsule` parsed as JSON, becomes:

- **P9 columns, unchanged:** `claim_id` (also `id`), `signer`,
  `is_active`, `superseded_by`, `created_at` (also `created`).
- **The claim:** `subject`, `predicate`, `object`; `content` is the
  capsule's `content` string if present, else "subject predicate
  object".
- **Faces:** `faces` has all six keys. A face is
  `{content, at, filled_at}` (both times = `created_at`) or `null`.
  Content is read from, in order: a `faces` object in the capsule,
  top-level face keys (a stored P13 cube), then the capsule's `face`
  tag, which fills that one face with the claim's sentence. Empty or
  non-string content is `null` (P13: empty faces are None).
- **`filled`** = faces present; **`score`** = filled / 6.
- **Attestation:** the capsule's `attestation` object, else the
  latest evidence capsule with `kind: "attestation"`. Normalised to
  `{source, note, at, retracted}`; `source` is `by`, else `source`,
  else the signature's `key_id`.
- **`status`:** `attested`, `retracted` (attestation has a
  `retracted` string), or `draft`.
- **`evidence_count`:** evidence rows for the claim.
- **Layout fields P9 does not have:** `group` = "Claims", `tags` = the
  capsule's `tags` list, else `[subject]`; `source` = "Signed by"
  and the signer; `standing` = 0; `neighbours` = [].

A row whose capsule is not a JSON object is skipped and named on
stderr. Unparseable evidence is skipped.

## 4. The page

`serve.py` joins `view_field_{world,form,hubs,draw,time,move}.js`, in
that order, inside one function, and fills `view_template.html`'s
`/*STYLE*/ /*GRID*/ /*FIELD*/ /*BAR*/` slots, plus `view_grid.js`'s
data slots: `CUBES`, `MODES` (`{}`), `USER` ("You"), `HUBS` (`[]`),
`THINGS` (`{}`), and `LENSES` (the six faces). Each fill is one
regex pass, so injected text is never read as a slot. Injected JSON
escapes `<`, `>`, `&`, U+2028 and U+2029.

The page has no forms, no unlock and no write calls.

## 5. Decisions on the open questions

- **Q1 Faces:** §1.
- **Q2 Time axis:** each cube's `created_at`, and the `at` of its
  faces and attestation. Superseded claims are not shown in v1.
- **Q3 Links:** none stored. Claims cluster by subject (their
  default tag), and the field draws its own threads within a
  cluster. No `claim_links` table.
- **Q4 Port and database:** §2.

## 6. Known limitations (v1.0.0)

- Read-only. All writes go through The Cockpit.
- No auth. Localhost only.
- No cross-substrate linking. No multi-user.
- Signatures are not verified on read (P9 v2 `verify=True` is not
  called: this consumer reads SQLite directly).
- Where an attestation lives is not yet defined by P9 or P13. §3's
  two sources are this consumer's convention until it is.
- No trust weighting (`standing` is always 0) and no P13 inspection
  grade shown.
- Entity/subject hubs (`THINGS`, `HUBS`) and cluster modes (`MODES`)
  stay in the frontend but are always empty.
- Superseded history is reachable only through
  `/api/claims/<id>`, not the field.

---

## Document control

- Status: FROZEN at 1.0.0. Verified by `test_substrate.py`
  (including claims written by P9 `substrate_v2` when the sibling
  layer is present).
- Changes after freeze are new layers (Immutable Rule), recorded in a
  new SPEC version.
