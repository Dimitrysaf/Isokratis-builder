---
name: AKN act→body vs doc→mainBody
description: Which body element to use depends on the top-level element type
---

Per AKN 3.0 §5.4:
- `act` contains `<body>`
- `doc` contains `<mainBody>`

In this project:
- nomos, pd, pnp, ya, kodikop → akn_el="act" → use `<body>`
- egkykl → akn_el="doc" → use `<mainBody>`

**Why:** The XSD models them as separate elements with different parent constraints. Using `<body>` inside `<doc>` fails schema validation.

**How to apply:** In xml_renderer.py the body_tag is computed as:
  body_tag = "body" if akn_el == "act" else "mainBody"
Always derive from INSTRUMENT_TYPES[itype]["akn_el"], never hardcode.
