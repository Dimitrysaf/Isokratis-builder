# CLAUDE.md — Isokratis project guide

> Read this first, then `Isokratis-TODO.md` and `docs/Akoma-Ntoso-Greek-Legislation-Mapping.md`.
> This file is the durable context handed off from earlier design work. Trust it
> over guesses.

## What this project is

**Isokratis** is a durable editor that produces **Greek legislation as
schema-valid Akoma Ntoso (AKN) 3.0 XML**. It is *not* a drafting tool for
lawmakers and *not* a fork of LEOS — it's a standalone app for codifying,
structuring, and (eventually) consolidating Greek legal texts
(νόμος, προεδρικό διάταγμα, ΠΝΠ, υπουργική απόφαση, εγκύκλιος, κωδικοποίηση).

Stack: Python · SQLite (durable, on-disk persistence) · web app (`web_app.py`) ·
custom node/document model (`src/models`) · AKN renderer (`src/renderers/xml_renderer.py`).

## Why these choices (so you don't re-litigate them)

- **SQLite, not browser storage** — an earlier browser-based version
  (`legisleture-builder`, TypeScript) lost data and corrupted on power loss.
  Durability is non-negotiable; SQLite is the reason this version is trusted.
- **This repo, not LEOS** — LEOS is an EU *drafting* tool that models the EC
  legislative package (cover page, proposal wrapper). It fights Greek law.
  Abandoned deliberately.
- **AKN 3.0, not RDF, not a custom schema** — AKN is the interoperability target.
  (Nomothesia used RDF; we don't.)

## CURRENT STATUS (keep this updated)

- ✅ **B2 passes** — create → save to SQLite → restart process → reload works. Durable.
- ✅ **B3 passes** — export reaches the live document; AKN output matches the doc (no more empty file).
- ✅ Renderer produces well-formed AKN: FRBR triple, ΦΕΚ `publication`, hierarchical `eId`s, inline refs via `{{href|label}}`.
- ✅ **A1-FIX RESOLVED** — `schema/akomantoso30.xsd` is now the **authentic** AKN 3.0
  XSD bundled from the `io.legaldocml:legaldocml-test` Maven artifact (315 distinct
  element names, 1 `xsd:import` → `xml.xsd`). Not hand-authored. See `.agents/memory/akn-xsd-local.md`.
- ✅ **A4-FIX RESOLVED** — `sample.xml` validates VALID against the authentic schema;
  fixed signature placement, hierarchy either/or, alinea content model, amendment model.
- ✅ **A5 done** — golden file `tests/golden/nomos_min.akn.xml` locked, validates against the authentic schema.
- ✅ Renderer is lxml-based (C1); escaping/edge cases pass (C2); εδάφιο/περίπτωση mapping fixed (C3).
- 🔜 Remaining: optional D3 (AKN import / reverse renderer); broader UI for amendments.

## HARD RULES (do not violate)

1. **NEVER hand-author or expand the AKN XSD to make validation pass.**
   A schema you wrote yourself certifies nothing — you'd unconsciously shape it to
   accept your own output (player + referee). The current `schema/akomantoso30.xsd`
   subset is a *temporary structural check only* and must be labelled as such.
   It is NOT a substitute for A1-FIX.
2. **The official schema must come from a real artifact**, not a raw GitHub URL.
   Acceptable sources: `akomantoso-lib` (Java/Maven), AKN/LEOS distributions, or
   an AKN package on PyPI/npm/Maven that *bundles* the XSD. Pull it as a
   dependency, verify it's multi-file (`xs:import` > 0) and ~310 elements.
3. **A blocked task stays BLOCKED until genuinely resolved.** Do not fake a
   "done" by satisfying a proxy check (e.g. adding `xs:import` to a self-made
   file to pass a grep). Mark blockers honestly.
4. **Validate against the real schema only** before locking any golden file.
   Until then, use well-formedness checks + diff against the real LegalParser
   sample (`law_4330_2015.xml`) as an *honest interim* signal — never a self-made schema.
5. **Don't rewrite / switch languages / start a new repo.** The urge to do so is
   the signal you've hit a hard task — push through it here.

## Where things live

- Task list & priorities: `Isokratis-TODO.md`
- AKN→Greek element mapping (with provenance): `docs/Akoma-Ntoso-Greek-Legislation-Mapping.md`
- Renderer: `src/renderers/xml_renderer.py`  ·  Models: `src/models/`  ·  DB: `src/db/`
- Validator: `validate.py`  ·  Sample generator: `make_sample.py`  ·  Tests: `tests/`
- Working notes: `.agents/memory/MEMORY.md` (+ linked notes)

## Good first task for a new session

> Read CLAUDE.md, Isokratis-TODO.md, and MEMORY.md. Then attempt **A1-FIX**:
> obtain the authentic AKN 3.0 XSD from akomantoso-lib or a package registry
> (the GitHub URLs 404). Do NOT hand-author a schema. If you can't get the real
> one, leave A1-FIX BLOCKED and instead diff `sample.xml` against the LegalParser
> reference sample, reporting structural differences.
