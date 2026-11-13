# SPEC V3 — scp-substrate (Tier 1: SCP Substrate, ISO timestamps for the field)

SPEC_V3.md — specification for serve_v3.py, the layer above SCP Substrate v2.0.0.

Function:
    Makes every time the field receives an ISO 8601 string, so an
    attested claim no longer stops the 3D field from drawing.
    serve.py (v1) and serve_v2.py (v2) are frozen and not edited, nor is
    the frontend in static/view/. Where this document is silent,
    SPEC_V2.md and SPEC.md apply.

Tier:      Tier 1 — Consumer (The Memory)
Depends:   serve_v2.py (SPEC_V2 2.0.0), P9 substrate_v3
Consumed:  The operator, The Legacy (embedded Field)
Version:   SPEC 3.0.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. The defect

P9 SPEC_V3 §3 stores a HAL decision as evidence whose `at` is the
seal's timestamp in **epoch seconds** (a number). SPEC_V2 passes it
through, so an attested claim reaches the page with
`attestation.at = 1794607496.91`. The frontend's `stampsOf` and
`loadMoments` treat every time as a string (`t.slice(0, 16)`), so the
first attested claim throws `TypeError: t.slice is not a function` and
the field draws nothing. Found 2026-11-13 when James looked at the
Field in The Legacy ("Field is not showing the substrate display").

## 2. The rule

Every time in an adapted claim is an ISO 8601 UTC string: `created`,
`created_at`, each face's `at` and `filled_at`, and `attestation.at`.
A number is read as epoch seconds and converted with
`datetime.fromtimestamp(x, timezone.utc).isoformat()`. A string is
kept as it is. Anything else (missing, bool, not finite) becomes
`created_at`, so a cube always has a usable time. This applies to
`/api/claims`, `/api/claims/<id>` and the page's injected `CUBES`.

## 3. Unchanged

Every SPEC_V2 rule: verified reads, unverified claims not drawn,
attestation and retraction (SPEC_V2 §3), health, read-only, port 8085,
GET/HEAD only.

## 4. Tests (test_serve_v3.py)

- An attested claim written through P9 substrate_v3: v2's output has
  a numeric `attestation.at` (the defect, pinned); v3's is an ISO
  string that `datetime.fromisoformat` reads back to the same instant.
- Every time in every v3 claim is a string.
- The page served by v3 has no numeric `"at"` in its injected data.
- If `node` is installed, the frontend's own `stampsOf` + `.slice`
  runs over v3's `CUBES` without throwing.

---

## Document control

- **SPEC 3.0.0** — 2026-11-13, by the VS Code AI. The fix is a layer
  (James: "make sure you are not over writing and versioning like the
  claude.md requires").
