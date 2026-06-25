---
name: AKN 3.0 XSD — local only, no network download
description: All OASIS and GitHub CDN URLs for the AKN 3.0 XSD return HTML 404 in this environment
---

Tried and failed (all return HTML pages, not XSD):
- https://docs.oasis-open.org/legaldocml/akn-core/v1.0/os/schemas/akomantoso30.xsd
- https://docs.oasis-open.org/legaldocml/akn-core/v1.0/csd02/schemas/akomantoso30.xsd
- Multiple raw.githubusercontent.com paths
- pip install akomantoso — no PyPI package exists

**Resolution:** Schema written from spec at schema/akomantoso30.xsd (~500 lines, covers act, doc, full meta, preface, preamble, body/mainBody, all hierarchical elements, inline refs, textualMod/amendments).

**How to apply:** Always use the local path. Run `python validate.py <file>` to validate. Do not attempt network download of the XSD — it will fail silently (return HTML) and corrupt the schema object.
