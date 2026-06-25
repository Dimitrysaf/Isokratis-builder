- [AKN 3.0 meta ordering](akn-meta-ordering.md) — classification must precede lifecycle in meta; wrong order is the #1 schema error
- [AKN body vs mainBody](akn-body-vs-mainbody.md) — act→body, doc→mainBody; egkykl maps to doc so needs mainBody
- [AKN XSD local only](akn-xsd-local.md) — all OASIS/GitHub URLs return HTML 404; schema lives at schema/akomantoso30.xsd written from spec
- [Inline refs syntax](akn-inline-refs.md) — {{href|label}} in content fields → <ref href="href">label</ref> via _mixed() in xml_renderer

---

## Project decisions (handoff context — June 2026)

- **Spine = this repo (Isokratis, Python/SQLite).** Chosen over `legisleture-builder`
  (TS/browser) because browser storage corrupted on power loss. SQLite = durable.
- **LEOS rejected** as a base — it models the EU legislative *package* (cover page,
  proposal wrapper) and fights Greek law. Don't revisit.
- **Target format = Akoma Ntoso 3.0** (OASIS v1.0, namespace akn/3.0). Not RDF,
  not a custom schema. "AKN4" = AKN4EU (an EU *profile*), NOT a version 4.
- **Milestone reached:** B2 (durable SQLite round-trip) and B3 (export matches live
  doc) both PASS. The empty-export bug and the data-durability problem are resolved.

## OPEN BLOCKER

- **A1-FIX (official XSD) is BLOCKED.** `schema/akomantoso30.xsd` is a hand-written
  ~94-element subset, NOT the real schema. It catches gross errors only; a `VALID`
  against it does NOT prove standard conformance.
- **Resolve by:** pulling the authentic XSD from a real artifact (akomantoso-lib /
  Maven / a PyPI/npm AKN package that bundles the schema) — never a raw GitHub URL,
  never a self-authored schema. Verify multi-file (`xs:import` > 0), ~310 elements.
- **Until resolved:** do NOT lock a golden file; validate well-formedness + diff
  against the real LegalParser sample (`law_4330_2015.xml`) as an honest interim.

## DISCIPLINE NOTE

- Never hand-author/expand the XSD to make validation pass (player ≠ referee).
- Never fake a "done" by satisfying a proxy metric.
- Don't rewrite / switch languages / start a new repo — that urge = a hard task,
  not a wrong project.
