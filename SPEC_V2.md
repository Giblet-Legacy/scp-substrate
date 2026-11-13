# SPEC V2 — scp-substrate (Tier 1: SCP Substrate, verified reader)

SPEC_V2.md — specification for serve_v2.py, the layer above SCP Substrate v1.0.0.

Function:
    Moves the viewer onto P9 substrate_v3's read-only API, so what the
    field draws has been verified, and onto P9 SPEC_V3 §3's attestation
    rule, so a real HAL approval lights the gold glow. serve.py v1.0.0
    is frozen and not edited; its adapter, page rendering, static
    serving and read-only rules are reused. Where this document is
    silent, SPEC.md 1.0.0 applies.

Tier:      Tier 1 — Consumer (The Memory)
Depends:   P9 substrate_v3 (read-only API, attestation rule)
Consumed:  The operator, The Legacy
Version:   SPEC 2.0.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. Why v2

- v1 reads `forge.db` with its own SQL and never verifies a signature
  (SPEC.md §6: "the server trusts the database file"). A tampered row
  is drawn like any other.
- v1's attestation source was its own convention (SPEC.md §3, §6). P9
  SPEC_V3 §3 now defines it: evidence of kind `attestation` or
  `refusal` carrying the signed HAL seal. An unverified evidence row
  could light the glow in v1.

## 2. Reading

- `read_claims(db)`: `substrate_v3.list_claims(db, verify=True)`. A
  claim that does not verify is **not drawn**; it is named on stderr
  and counted (§4). Each drawn claim is adapted with v1's
  `adapt_claim` and gains `verified: true`.
- Evidence comes from `substrate_v3.read_evidence(db, id,
  verify=True)`; evidence that does not verify is dropped before
  adaptation, so it can never light the glow or count.
- `read_claim(db, id)`: any claim, active or superseded, verified or
  not, with `verified`, `verify_error`, `capsule` and its verified
  `evidence`. 404 if absent.

## 3. Attestation (P9 SPEC_V3 §3)

v1's `attestation_of` still finds the newest `kind: "attestation"`
evidence. v2 then looks at the newest decision of either kind: if it
is a `refusal` dated after that attestation, the attestation is
marked `retracted` with the refusal's note, so the cube shows the
frontend's existing "retracted" status, not the gold glow.

## 4. Health

`GET /api/health` is v1's body plus `verified` and `unverified`
(active claim counts). A missing database is 503, as in v1.

## 5. Unchanged

Host 127.0.0.1, port 8085, `--db` / `$FORGE_HOME` resolution, GET and
HEAD only (405 otherwise), static files only from `static/view/`,
escaped JSON in the page.

## 6. Tests (test_substrate_v2.py)

- Claims written by P9 substrate_v3 are drawn with `verified: true`.
- A tampered claim is not drawn, is counted in health, and is still
  reachable (unverified) at `/api/claims/<id>`.
- `link_attestation` approve → status `attested`; a later refusal →
  `retracted`; a tampered attestation row → `draft`.
- `/` renders 200; POST is 405; a missing database is 503.

---

## Document control

- **SPEC 2.0.0** — 2026-11-13, by the VS Code AI on James's delegation
  ("fix all 11 issues").
