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

## A1-FIX — RESOLVED (was the open blocker)

- **Authentic XSD obtained.** `schema/akomantoso30.xsd` is now the real AKN 3.0
  schema bundled from the `io.legaldocml:legaldocml-test:0.5.0` Maven artifact
  (`repo1.maven.org`). 315 distinct element names, 1 `xsd:import` (`xml.xsd`),
  `xsd:` prefix, targetNamespace `…/ns/akn/3.0`. Authored by F. Vitali et al.
- **Acquisition route:** OASIS docs host + raw GitHub URLs 404; Maven Central
  (`repo1.maven.org/maven2/io/legaldocml/`) is reachable — pulled the jar, extracted
  `xsd/akomantoso30.xsd` + `xsd/xml.xsd`. This satisfies the hard rule (real artifact,
  not self-authored, not a raw GitHub URL).
- **Golden file locked** (`tests/golden/nomos_min.akn.xml`) — validates against this
  authentic schema. A4-FIX errors (signature/inline, hierarchy either/or, alinea,
  amendment model) all fixed; all 5 renderer tests pass.

## DISCIPLINE NOTE

- Never hand-author/expand the XSD to make validation pass (player ≠ referee).
- Never fake a "done" by satisfying a proxy metric.
- Don't rewrite / switch languages / start a new repo — that urge = a hard task,
  not a wrong project.
