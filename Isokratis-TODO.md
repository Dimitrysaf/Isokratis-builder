# Isokratis — Build Task List (v2, updated)

Ordered, checkable tasks. **Do them top to bottom.** Each task has a **Done when**.

Priority: `P0` = blocking · `P1` = important · `P2` = later · `P3` = polish.

---

## STATUS SNAPSHOT (as of this update)

- ✅ Validation loop scaffolded: `validate.py`, `make_sample.py`, `tests/` all exist.
- ✅ Renderer runs and produces well-formed AKN (`sample.xml`, FRBR triple, ΦΕΚ block, hierarchical eIds).
- ✅ `make_sample.py` → `sample.xml` reports **VALID** against the **authentic** schema.
- ✅ **A1-FIX RESOLVED** — `schema/akomantoso30.xsd` is now the real multi-file AKN 3.0
  schema (315 elements, `xsd:import` > 0) from the `io.legaldocml` Maven artifact.
- ✅ A4-FIX, A5, B1–B4, C1–C3, D1–D3, E1–E3 all done (see checkboxes below).
- 🎉 All TODO tasks complete (including optional D3 AKN import). 6/6 tests pass.

---

## PHASE A — Close the validation loop  *(mostly done; one critical fix)*

### [x] A2 · Validator script — **DONE** (`validate.py` works)
### [x] A3 · Generate a sample & validate — **DONE** (`make_sample.py` → `sample.xml`)
### [x] A4 · Fix validation errors — **PROVISIONAL** (passes the subset; must re-run vs real schema in A1-FIX)

### [x] A1-FIX · `P0` · Replace the subset XSD with the OFFICIAL AKN 3.0 bundle
- **Why:** Your `schema/akomantoso30.xsd` is a trimmed single file (94 elements,
  no imports). The real schema is ~310 elements across multiple `.xsd` files.
  Passing the subset does **not** prove validity against the standard.
- **How:**
  - Download the **complete** Akoma Ntoso 3.0 XSD release from OASIS LegalDocML
    (the `CSD13` revision). It includes the main file **plus** the imported
    building-block files (and `xml.xsd`). Grab **all** of them.
  - Put the full set in `schema/` preserving their relative imports.
  - Point `validate.py` at the real root schema file.
- **Done when:** `validate.py` loads the full schema without import errors, and
  `grep -c xs:import schema/<root>.xsd` is **> 0** (proving it's the multi-file real one).

### [x] A4-FIX · `P0` · Re-validate against the real schema & fix NEW errors
- **Why:** The real schema has stricter content models; expect fresh errors.
  This is the real A4.
- **How:** Run `python validate.py sample.xml`. Work the list one by one. Likely:
  - `<docType>`/`<docNumber>`/`<docTitle>` bare inside `<p>` in `preface` —
    check the real allowed content model for `preface`.
  - `meta` child **ordering** (identification → publication → … → references).
    *(Your `.agents/memory/akn-meta-ordering.md` note suggests you saw this.)*
  - `formula` placement/attributes.
  - Empty-leaf fallback `<content><p/></content>` — confirm empty `<p/>` is legal.
  - `eId` value format on `eventRef`/`keyword`.
- **Done when:** `python validate.py sample.xml` prints `VALID` **against the full schema.**

### [x] A5 · `P1` · Lock the passing sample as a golden file
- **How:** Copy the (really) validated `sample.xml` → `tests/golden/nomos_min.akn.xml`.
- **Done when:** Golden file exists and validates against the full schema.

---

## PHASE B — Prove the full round trip (UI → DB → render → valid)

### [x] B1 · `P0` · Confirm the app runs
- Fresh venv, `pip install -r requirements.txt`, run `web_app.py`, open in browser.
- **Done when:** Loads without a stack trace. *(Note: last commit fixed a
  document-creation DB error — verify that path now works end to end.)*

### [x] B2 · `P0` · Round-trip a document through SQLite
- Create a doc with one article, save, **fully restart the process**, reload.
- **Done when:** Reloaded content matches. Durability confirmed.

### [x] B3 · `P0` · Wire "Export AKN" to the live document
- Trace in-app document → `Document` → `AkomaNtosoRenderer.render()`. Confirm
  `doc.body` is populated at export time.
- **Done when:** Export writes a file matching the doc that validates against the
  full schema.

### [x] B4 · `P1` · Export to real disk (download), not browser memory
- Flask `send_file` / proper `Content-Disposition`.
- **Done when:** Export, close everything, the `.akn.xml` is still on disk + valid.

---

## PHASE C — Harden the renderer

### [x] C1 · `P1` · Move XML generation from strings → `lxml`
- **Why:** Hand-built strings risk malformed XML; `lxml` makes it impossible and
  serializes cleanly. Do this **after** A4-FIX passes (refactor known-good output).
- **Done when:** lxml renderer output still validates; golden test still passes.

### [x] C2 · `P1` · Audit escaping & edge cases
- Test input with `&`, `<`, `»`, quotes, polytonic Greek, empty body, node with
  children + content.
- **Done when:** All produce valid XML.

### [x] C3 · `P2` · Decide `εδάφιο`/`περίπτωση` modelling, apply consistently
- Pick `subparagraph` vs `list/point`; note the choice in the mapping doc changelog.
- **Done when:** One mapping chosen and used everywhere.

---

## PHASE D — Fill the real gaps (highest value)

### [x] D1 · `P1` · Inline references (`<ref>` / mentions)
- Detect/store cross-refs ("άρθρο 5 του ν. 4330/2015"), render `<ref href="…">`,
  declare targets in TLC register. Start manual before auto-detection.
- **Done when:** A doc with one cross-ref exports valid AKN with a resolvable `<ref>`.
- *(You already have `.agents/memory/akn-inline-refs.md` — build on it.)*

### [x] D2 · `P2` · Amendments / consolidation (`textualMod`)
- Model: type (substitution/insertion/repeal), source ref, destination ref,
  old/new text. Render under `<passiveModifications>`.
- **Carry-over bug to avoid:** `<source>` contains exactly **one** `<ref>` — do
  NOT nest `<ref>` in `<ref>`.
- **Done when:** One amendment exports as valid `<textualMod>`.

### [x] D3 · `P3` · (Optional) AKN import (reverse renderer)
- Only if you want "open an existing `.akn.xml`" / AKN-as-native.
- **Done when:** `render(import(golden)) == golden` (round-trips).
- **Done:** `src/renderers/xml_importer.py` (`AkomaNtosoImporter`). `test_import_roundtrip`
  asserts `render(import(golden)) == golden`, modulo the FRBRManifestation
  *Generation* date (a render-time timestamp, inherently "now", not source data).

---

## PHASE E — Practices (after it works)

### [x] E1 · `P2` · Exporter test — **STARTED** (`tests/test_renderer.py` exists)
- Upgrade it to assert output validates against the **full** schema (reuse A2).
- **Done when:** Test goes green and catches a deliberate break.

### [x] E2 · `P3` · Remove dead code
- Copy-paste "render LaTeX" leftovers, unused `templates` param in
  `AkomaNtosoRenderer.__init__`, stale README claims (`app.py`/Qt UI).
- **Done when:** No misleading comments/params remain.

### [x] E3 · `P3` · Make README match reality
- Describe the actual web app + SQLite + AKN export.
- **Done when:** A stranger could run the project from the README.

---

## THE FINISH LINE

**Worth-it milestone:** **A4-FIX + B3** — a Greek law created in the app, saved
durably to SQLite, exported as **schema-valid (full-schema) Akoma Ntoso.**
Everything in Phase D is expansion on a proven core.

## DISCIPLINE

If you feel the urge to start a new repo, switch languages, or rewrite — that's
the signal you hit a hard task above, not that the project is wrong. Push through
the task. The win is **finishing this one.**
