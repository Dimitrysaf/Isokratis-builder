---
name: AKN 3.0 meta element ordering
description: Normative child order inside <meta> per AKN 3.0 §5.2 — wrong order is the most common schema error
---

The <meta> element must have children in this exact sequence:

1. identification (required)
2. publication (0..*)
3. classification (0..*)   ← BEFORE lifecycle
4. lifecycle (0..*)
5. workflow (0..*)
6. analysis (0..*)
7. temporalData (0..*)
8. notes (0..*)
9. proprietary (0..*)
10. presentation (0..*)
11. references (0..*)
12. amendment (0..*)

**Why:** XSD uses xs:sequence so order is strictly enforced. The original string renderer had lifecycle before classification, causing the first validation error.

**How to apply:** The lxml renderer (xml_renderer.py) now writes children in exactly this order. Any future meta additions must slot into this sequence. The local XSD at schema/akomantoso30.xsd enforces this — run `python validate.py <file>` to check.
