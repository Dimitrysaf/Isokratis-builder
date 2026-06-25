# Akoma Ntoso → Greek Legislation Mapping Reference

A structural and semantic mapping reference for representing Greek legislative
instruments (νόμος, προεδρικό διάταγμα, πράξη νομοθετικού περιεχομένου,
υπουργική απόφαση, εγκύκλιος, κωδικοποίηση) in the Akoma Ntoso (AKN) XML
vocabulary.

| | |
|---|---|
| **Document status** | Unofficial working reference (community documentation) |
| **Version** | 0.1.0 |
| **Target standard** | Akoma Ntoso / OASIS LegalDocML, Core v1.0 — XML schema namespace `akn/3.0` |
| **Audience** | Implementers building ΦΕΚ → AKN converters / editors |
| **Scope** | Legislative documents (`act`). Judicial (`judgment`) and debate (`debate`) document types are out of scope. |

> **This is not a normative standard.** AKN itself is the normative source
> ([N1]–[N3]). This document is an *application reference*: it records which AKN
> elements correspond to Greek legislative constructs, and — critically — the
> **provenance** of each mapping (whether it is fixed by the standard, an
> established convention, or derived from a specific Greek research artifact).
> Where this document and the AKN schema disagree, **the schema wins**.

---

## 1. Scope and conformance

This reference covers the AKN elements needed to mark up the *structure*,
*metadata*, *references*, and *amendments* of Greek primary and secondary
legislation as published in the Government Gazette (Εφημερίδα της Κυβερνήσεως,
ΦΕΚ).

A document is **conformant to this reference** if it (a) validates against the
official AKN 3.0 schema [N1] for a fixed schema revision (see §3), and (b) uses
the element-to-construct correspondences in §5–§9 where applicable. Conformance
to this reference does **not** imply conformance to AKN4EU [I6], which adds
EU-specific constraints; see §10.

---

## 2. Provenance legend

Every mapping row carries a **Source** marker. This is the core of the document:
it separates fact from convention.

| Marker | Meaning |
|---|---|
| `[STD]` | Element and its role are defined by the AKN standard itself [N1]–[N3]. Fixed. |
| `[STD-CM]` | Standard element, but its *placement* in the Greek hierarchy is governed by AKN content models — verify against schema. |
| `[CONV]` | **Convention only.** The element is standard AKN, but the choice to use it for this particular Greek construct is a practical convention, not standardized by any Greek authority. No official Greek AKN profile exists (see §11). |
| `[GR-AKN]` | Mapping proposed in the Greek modelling literature, principally Angelidis et al. [I1]. |
| `[GR-LP]` | Mapping evidenced by the LegalParser / Koniaris et al. line of work [I3], which emits AKN-conformant output ("LegalDocML schema"). |
| `[GR-ELI]` | Mapping informed by the ELI↔AKN interoperability work under ManyLaws [I5]. |

> **Honesty note.** No Greek public body has published an element-by-element
> ΦΕΚ→AKN dictionary. The Greek artifacts that reach AKN ([I1], [I3]) publish
> *descriptions and samples*, not a runnable element map; the Greek artifacts
> that publish runnable code (Nomothesia [I2]) target **RDF, not AKN**. Rows
> marked `[GR-*]` are therefore *derived from* those works, not transcribed from
> an authoritative table. Rows marked `[CONV]` are the author's reasoned
> convention. Treat both as engineering guidance, not as legal authority.

---

## 3. Namespaces and schema versions

There is frequent confusion over AKN "version numbers." For the record:

- The **OASIS standard** is **Akoma Ntoso Version 1.0**, approved 29 August 2018
  [N1][N2].
- The **XML namespace / schema** it defines is **3.0**:
  `http://docs.oasis-open.org/legaldocml/ns/akn/3.0`. "AKN 3.0" (schema) and
  "AKN v1.0" (standard) denote the same artifact on different numbering axes.
- **There is no "Akoma Ntoso 4.0."** References to "AKN4" in Greek/EU material
  almost always mean **AKN4EU** — the European Commission *profile* of AKN
  ("4EU" = "for EU"), not a version 4 [I6].
- The 3.0 namespace has dated working-draft revisions (e.g. `CSD13`, `WD17`).
  Pick **one** revision and validate against it consistently. Existing Greek AKN
  output (the LegalParser sample) used the `CSD13` revision.

The schema defines on the order of **310 element names and 69 attributes** [N1];
this reference documents only the subset relevant to Greek legislation.

Recommended root declaration:

```xml
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
```

---

## 4. Naming and identifier conventions

- AKN uses **lower camelCase** for elements and attributes (`mainBody`,
  `refersTo`) [N1]. Do not invent Greek-named elements; use AKN names and put
  Greek text in content and `@showAs`/labels.
- Identifiers (`eId`) and IRIs follow the **AKN Naming Convention** [N3]. `eId`
  values should be **hierarchical** (e.g. `art_5__para_2__pnt_a`), not globally
  flat counters.
- Work/Expression/Manifestation IRIs should align with **ELI** where possible
  [I4][I5], e.g. `/gr/act/2015/4330`, so that the FRBR URIs double as ELI URIs.

---

## 5. Element catalog

Elements are grouped by AKN functional role. Each table: AKN element · Greek
construct · Greek term · Need · Source · Notes.

`Need`: `CORE` (almost every document) · `COMMON` · `OPTIONAL` · `RARE`.

### 5.1 Document-type wrappers

| AKN | Greek construct | Greek term | Need | Source | Notes |
|---|---|---|---|---|---|
| `akomaNtoso` | document root | — | CORE | `[STD]` | Required semantic root [I-overview]. |
| `act` | enacted legislative instrument | νόμος / προεδρικό διάταγμα / ΠΝΠ | CORE | `[STD]` `[GR-LP]` | `@name` distinguishes the instrument. LegalParser output uses `act`. |
| `doc` | non-act issuance | εγκύκλιος / ορισμένες υπουργικές αποφάσεις | OPTIONAL | `[STD-CM]` `[CONV]` | For prescriptive-neutral issuances that are not formal "acts". |
| `documentCollection` | multi-document gazette issue | τεύχος ΦΕΚ (πολλαπλά κείμενα) | OPTIONAL | `[STD]` | A single ΦΕΚ issue often contains several autonomous acts; model with `components`/`interstitial` [I-overview]. |
| `portion` | isolated fragment | απόσπασμα (π.χ. ένα άρθρο) | RARE | `[STD]` | Storing/citing a single provision outside its act. |

### 5.2 Metadata — the `<meta>` block

| AKN | Purpose | Need | Source | Notes |
|---|---|---|---|---|
| `meta` | metadata container | CORE | `[STD]` | Schema-required. |
| `identification` | FRBR identity | CORE | `[STD]` | `@source` → tool/agent id. |
| `FRBRWork` | abstract work | CORE | `[STD]` | The law across all versions. |
| `FRBRExpression` | a version | CORE | `[STD]` | Point-in-time version — basis of consolidation. |
| `FRBRManifestation` | a format | CORE | `[STD]` | This XML rendering. |
| `FRBRuri` | work/expression IRI | CORE | `[STD]` `[GR-ELI]` | Align with ELI: `/gr/act/{year}/{number}` [I4][I5]. |
| `FRBRdate` | a relevant date | CORE | `[STD]` | `@name`: `enacted`, `published`, … |
| `FRBRauthor` | author/enactor | CORE | `[STD]` | href → TLC reference. |
| `FRBRcountry` | jurisdiction | CORE | `[STD]` | `value="gr"`. |
| `FRBRlanguage` | language | COMMON | `[STD]` | `value="ell"`. |
| `FRBRnumber` | instrument number | COMMON | `[STD]` | e.g. `4330`. |
| `FRBRname` / `FRBRalias` | common name | OPTIONAL | `[STD]` | |
| `FRBRsubtype` | sub-classification | OPTIONAL | `[STD]` `[CONV]` | Distinguish ΠΔ vs νόμος. |
| `publication` | gazette publication data | COMMON | `[STD]` `[GR-ELI]` | The **ΦΕΚ block**: series (τεύχος), number, date. |
| `lifecycle` / `eventRef` | event timeline | COMMON | `[STD]` | Enacted/amended/repealed — drives consolidation. |
| `classification` / `keyword` | subject indexing | COMMON | `[STD]` `[GR-AKN]` | Thematic keywords for search [I1]. |
| `references` | TLC register | COMMON | `[STD]` | Declares referenced entities (see §5.8). |
| `proprietary` | non-AKN metadata | OPTIONAL | `[STD]` | Legal home for Greek-specific metadata (see §7). |
| `notes` / `note` | editorial notes | OPTIONAL | `[STD]` | Footnotes / editor remarks. |

### 5.3 Preface and preamble

| AKN | Greek construct | Greek term | Need | Source | Notes |
|---|---|---|---|---|---|
| `preface` | front/title area | — | COMMON | `[STD-CM]` | Title-bearing front matter. |
| `longTitle` / `shortTitle` | titles | τίτλος | COMMON | `[STD]` | |
| `docTitle` | title (inline) | τίτλος | COMMON | `[STD]` `[GR-LP]` | Present in LegalParser sample. |
| `docNumber` | act number (inline) | αριθμός | COMMON | `[STD]` `[GR-LP]` | |
| `docDate` | act date (inline) | ημερομηνία | COMMON | `[STD]` `[GR-LP]` | |
| `docType` | type label | — | OPTIONAL | `[STD]` `[CONV]` | "ΝΟΜΟΣ", "ΠΡΟΕΔΡΙΚΟ ΔΙΑΤΑΓΜΑ". |
| `preamble` | preamble | προοίμιο | COMMON | `[STD-CM]` `[GR-LP]` | The "Έχοντας υπόψη…" block. |
| `formula` | enacting formula | — | OPTIONAL | `[STD]` | "Εκδίδομε τον ακόλουθο νόμο…". |
| `citations` / `citation` | legal bases | (έχοντας υπόψη) | COMMON | `[STD]` `[CONV]` | Each numbered basis item. |
| `recitals` / `recital` | recitals | σκέψεις | OPTIONAL | `[STD]` | More EU-style than domestic Greek. |

### 5.4 Hierarchical body structure

| AKN | Greek construct | Greek term | Need | Source | Notes |
|---|---|---|---|---|---|
| `body` | main container | — | CORE | `[STD]` | Holds the hierarchy. |
| `part` | part | μέρος | COMMON | `[STD]` `[GR-AKN]` | Top division. |
| `title` (hcontainer) | title-division | τίτλος (διαίρεση) | OPTIONAL | `[STD-CM]` | Division named "Τίτλος". |
| `chapter` | chapter | κεφάλαιο | COMMON | `[STD]` `[GR-AKN]` | |
| `section` | section | τμήμα / ενότητα | OPTIONAL | `[STD]` | |
| `subsection` | subsection | υποενότητα | RARE | `[STD]` | |
| `article` | **article** | **άρθρο** | CORE | `[STD]` `[GR-LP]` `[GR-AKN]` | Fundamental unit; in LegalParser sample. |
| `paragraph` | **paragraph** | **παράγραφος** | CORE | `[STD]` `[GR-LP]` `[GR-AKN]` | Numbered παρ. |
| `subparagraph` | sub-paragraph | εδάφιο | COMMON | `[STD-CM]` `[CONV]` | "εδάφιο"; verify content model. |
| `list` | enumeration container | — | COMMON | `[STD]` | Wraps περιπτώσεις. |
| `point` | list item | περίπτωση | COMMON | `[STD]` `[CONV]` | α), β), γ). |
| `indent` | sub-item | υποπερίπτωση | COMMON | `[STD]` `[CONV]` | αα), ββ). |
| `alinea` | unnumbered block | — | OPTIONAL | `[STD]` | |
| `level` | generic level | — | OPTIONAL | `[STD]` | When the division is unnamed. |
| `hcontainer` | generic hierarchy container | (οποιαδήποτε διαίρεση) | OPTIONAL | `[STD]` | **Escape hatch** via `@name` (see §7). |

### 5.5 Structural sub-elements

| AKN | Purpose | Need | Source | Notes |
|---|---|---|---|---|
| `num` | number/label | CORE | `[STD]` | "Άρθρο 5", "1.", "α)". |
| `heading` | unit title | COMMON | `[STD]` | |
| `subheading` | secondary heading | RARE | `[STD]` | |
| `intro` | lead-in before a list | COMMON | `[STD]` | "…ως εξής:". |
| `wrapUp` | text after a list | OPTIONAL | `[STD]` | |
| `content` | leaf text container | CORE | `[STD]` | Wraps `<p>`. |

### 5.6 Block-level content

| AKN | Purpose | Need | Source | Notes |
|---|---|---|---|---|
| `p` | text paragraph | CORE | `[STD]` | Inside `content`. |
| `block` | labelled block | OPTIONAL | `[STD]` | |
| `tblock` | text-block grouping | RARE | `[STD]` | |
| `blockList` / `item` | block-level list | OPTIONAL | `[STD]` | Alternative list modeling. |
| `foreign` | non-AKN embedded content | OPTIONAL | `[STD]` | For content AKN cannot model (see §7) [I7]. |
| `table` / `tr` / `th` / `td` / `caption` | tables | COMMON | `[STD]` | HTML-derived elements in AKN namespace [N1]. Extraction from PDF is the hard part, not the markup. |
| `eol` / `eop` | end-of-line / end-of-page markers | OPTIONAL | `[STD]` | For preserving official manifestation layout [N1]. |

### 5.7 Inline / semantic elements

| AKN | Purpose | Greek term | Need | Source | Notes |
|---|---|---|---|---|---|
| `ref` | resolved reference | παραπομπή / αναφορά | CORE | `[STD]` `[GR-LP]` | **Mentions.** `@href` → target IRI. |
| `mref` | multiple reference | — | COMMON | `[STD]` | |
| `rref` | range reference | — | OPTIONAL | `[STD]` | "άρθρα 5 έως 8". |
| `date` | inline date | ημερομηνία | COMMON | `[STD]` | |
| `def` | a definition | ορισμός | COMMON | `[STD]` | Marks defined term. |
| `term` | defined term in use | όρος | OPTIONAL | `[STD]` | Links to its `def`. |
| `entity` | named entity | — | OPTIONAL | `[STD]` | |
| `organization` | organization | φορέας | OPTIONAL | `[STD]` | |
| `person` | person | πρόσωπο | OPTIONAL | `[STD]` | |
| `role` | role | ιδιότητα | OPTIONAL | `[STD]` | "Υπουργός Οικονομικών". |
| `location` | place | τόπος | OPTIONAL | `[STD]` | |
| `quantity` | quantity/sum | ποσό | OPTIONAL | `[STD]` | |

### 5.8 Reference register (Top-Level Classifications)

Declared inside `<references>`; pointed to by inline elements via `@refersTo`.

| AKN | Purpose | Need | Source |
|---|---|---|---|
| `TLCReference` | generic | COMMON | `[STD]` |
| `TLCPerson` | person (πρόσωπο) | OPTIONAL | `[STD]` |
| `TLCOrganization` | organization (φορέας) | OPTIONAL | `[STD]` |
| `TLCRole` | role (ιδιότητα) | OPTIONAL | `[STD]` |
| `TLCConcept` | concept/keyword | OPTIONAL | `[STD]` |
| `TLCTerm` | defined term | OPTIONAL | `[STD]` |
| `TLCLocation` | place | RARE | `[STD]` |
| `TLCEvent` | event | RARE | `[STD]` |

### 5.9 Amendments and modifications (consolidation layer)

| AKN | Purpose | Need | Source | Notes |
|---|---|---|---|---|
| `activeModifications` | changes this act makes to others | COMMON | `[STD]` | In `meta`. |
| `passiveModifications` | changes others made to this act | COMMON | `[STD]` | Basis of point-in-time text [N1]. |
| `textualMod` | a textual change | COMMON | `[STD]` | `@type`: `substitution` / `insertion` / `repeal` / `renumbering`. |
| `meaningMod` | change of meaning | RARE | `[STD]` | |
| `scopeMod` | change of scope | RARE | `[STD]` | |
| `efficacyMod` | change of force/effect | OPTIONAL | `[STD]` | |
| `source` | trigger of the change | COMMON | `[STD]` | Contains **one** `ref`. |
| `destination` | target of the change | COMMON | `[STD]` | |
| `old` / `new` | before / after text | COMMON | `[STD]` | |
| `quotedText` | quoted inline text | COMMON | `[STD]` | "…αντικαθίσταται από «X»". |
| `quotedStructure` | quoted structural block | OPTIONAL | `[STD]` | Inserting a whole article. |
| `mod` | inline modification marker | OPTIONAL | `[STD]` | |
| `ins` / `del` | inserted / deleted text | OPTIONAL | `[STD]` | Track-changes style. |

### 5.10 Conclusions and back matter

| AKN | Greek construct | Greek term | Need | Source | Notes |
|---|---|---|---|---|---|
| `conclusions` | closing block | — | COMMON | `[STD-CM]` | Place/date + signatures. |
| `signature` | signature | υπογραφή | COMMON | `[STD]` `[GR-LP]` | Present in LegalParser sample. |
| `attachments` / `attachment` | attached documents | παράρτημα | OPTIONAL | `[STD]` | |
| `annex` | annex | παράρτημα | COMMON | `[STD]` | "ΠΑΡΑΡΤΗΜΑ". |
| `components` / `interstitial` | collection assembly | — | OPTIONAL | `[STD]` | For ΦΕΚ issues bundling multiple acts [I-overview]. |

---

## 6. Canonical Greek structural depth

The conventional nesting for a Greek statute, with the AKN elements used at each
level. Provenance: structural levels `μέρος/κεφάλαιο/άρθρο/παράγραφος` are
supported by the Greek modelling literature `[GR-AKN]` [I1] and present in
LegalParser output `[GR-LP]` [I3]; the deeper `εδάφιο/περίπτωση/υποπερίπτωση`
choices are `[CONV]`.

```
νόμος            → act
  μέρος          → part
    κεφάλαιο     → chapter
      άρθρο      → article
        παράγραφος → paragraph
          εδάφιο   → subparagraph        [CONV]
          περίπτωση → list > point        [CONV]
            υποπερίπτωση → indent         [CONV]
```

Where a Greek division has no exact AKN counterpart, use
`hcontainer @name="…"` rather than inventing an element (see §7).

---

## 7. Handling Greek-specific constructs

AKN is explicitly designed to absorb national particularities without schema
extension. The standard's own authors document three mechanisms [I7]:

1. **`hcontainer @name="meros"`** — a generic, schema-valid hierarchical
   container for any named division AKN does not name natively. **Preferred** for
   Greek structural divisions outside the standard set.
2. **`foreign`** — wraps embedded non-AKN content (e.g. MathML, raw markup) that
   must be preserved verbatim.
3. **`proprietary`** — a legal location in `meta` for jurisdiction-specific
   metadata that has no AKN field (e.g. internal ΦΕΚ catalog identifiers).

Using these three instead of inventing elements keeps documents schema-valid and
interoperable. This is the standard-sanctioned path for a national profile and is
how AKN is expected to be localized [N2][I7].

---

## 8. Provenance of Greek implementations

What each Greek effort actually targeted — so you can judge how directly its
choices transfer.

| Project / work | Output format | AKN element map? | Code public? | Ref |
|---|---|---|---|---|
| LegalParser / Koniaris et al. | **Akoma Ntoso** (LegalDocML) | Described in paper; one sample document | No (README + 1 sample only) | [I3] |
| Angelidis et al., "Modelling Legal Documents…" | AKN model (proposal) | Conceptual modelling, prose | N/A (proposal) | [I1] |
| Nomothesia | **RDF / OWL** (ELI ontology) | No — different format | Yes (unmaintained) | [I2] |
| ManyLaws (ELI↔AKN mapping) | ELI + AKN + DCAT interoperability | Ontology-level mapping | EU infrastructure | [I5] |
| Garofalakis et al. | Legal open data | Structural | — | [I8] |
| Beris & Koubarakis | Govt decisions (semantic web) | — | — | [I9] |

**Key takeaway:** the works that reached **AKN** ([I1], [I3]) published
descriptions and samples, not a transcribable element map; the work that
published **runnable code** ([I2]) targeted **RDF, not AKN tags**. There is no
single authoritative, published, machine-readable Greek AKN element dictionary.

---

## 9. Validation and conformance procedure

1. Fix a schema revision (§3) — e.g. `akn/3.0/CSD13` — and obtain the official
   XSD from the OASIS LegalDocML repository [N1].
2. Validate every produced document against that XSD. A flat element list (this
   document) cannot express AKN **content models** (which elements may legally
   nest in which) — only the schema can. Validation is mandatory, not optional.
3. Treat validation errors as the authority. Where this reference and the schema
   conflict, **the schema governs** and this document should be corrected.
4. For ELI-URI conformance, additionally check IRIs against the ELI technical
   guidance [I4].

---

## 10. Relationship to AKN4EU

AKN4EU [I6] is the European Commission's AKN profile. It constrains and extends
AKN 3.0 for EU institutional drafting (it is the basis of tools such as LEOS).
For a **domestic Greek** system, plain AKN 3.0 is the cleaner target; align with
AKN4EU only if EU-interchange is a requirement. AKN4EU is **not** "AKN version 4"
(see §3).

---

## 11. Open issues / non-normative notes

- **No official Greek AKN profile exists.** Until a Greek authority publishes
  one, the Greek-term column is conventional. If/when an official profile or a
  Greek LegalDocML application schema (cf. Germany's LegalDocML.de) appears,
  defer to it.
- **`subparagraph` vs `list/point`** for εδάφιο/περίπτωση is a modelling choice;
  pick one mapping and apply it consistently across the corpus.
- **Tables and embedded images** are markup-able (§5.6) but their *extraction*
  from gazette PDFs is an unsolved-at-scale problem in the cited literature
  [I-survey]; do not assume inherited parsers handle them.
- **Schema revision drift:** `CSD13` vs `WD17` differ; mixing them causes
  validation failures.

---

## Appendix A — References

### Normative (the standard)

- **[N1]** Palmirani, M., Sperberg, R., Vergottini, G., Vitali, F. (eds.).
  *Akoma Ntoso Version 1.0, Part 1: XML Vocabulary.* OASIS Standard,
  29 August 2018. Namespace: `http://docs.oasis-open.org/legaldocml/ns/akn/3.0`.
- **[N2]** Vitali, F., Palmirani, M., Sperberg, R., Parisse, V. (eds.).
  *Akoma Ntoso Version 1.0, Part 2: Specifications.* OASIS Standard,
  29 August 2018.
- **[N3]** Vitali, F., Palmirani, M., Parisse, V. *Akoma Ntoso Naming Convention
  Version 1.0.* OASIS Standard, 21 February 2019.

### Informative (Greek and EU application work)

- **[I1]** Angelidis, I., Chalkidis, I., Nikolaou, C., Soursos, P.,
  Koubarakis, M. *Modelling Legal Documents for Their Exploitation as Open Data.*
  Springer, 2019. DOI: 10.1007/978-3-030-20485-3_3.
- **[I2]** Angelidis, I., Chalkidis, I., Nikolaou, C., Soursos, P.,
  Koubarakis, M. *Nomothesia: A Linked Data Platform for Greek Legislation.*
  MIREL Workshop, 2018. (Linked Open Data / RDF; ELI ontology.)
- **[I3]** Koniaris, M., et al. *Towards Automatic Structuring and Semantic
  Indexing of Legal Documents* (LegalParser). Pan-Hellenic Conference on
  Informatics (PCI), 2016. (DSL/ANTLR parser → LegalDocML/AKN; OCR-capable;
  emits Akoma Ntoso.)
- **[I4]** ELI Task Force. *ELI — A Technical Implementation Guide.* 2015.
- **[I5]** *Semantic Interoperability for Legal Information: Mapping the European
  Legislation Identifier (ELI) and Akoma Ntoso (AKN) Ontologies.* ManyLaws
  (INEA-CEF). ACM. DOI: 10.1145/3614321.3614327. (EU/Austrian/Greek
  interoperable infrastructure; ELI↔AKN↔DCAT.)
- **[I6]** European Commission. *AKN4EU* — Akoma Ntoso profile for EU
  legislation (basis of LEOS). (Profile of AKN 3.0; not "AKN v4".)
- **[I7]** Palmirani, M., Vitali, F. *Akoma-Ntoso for Legal Documents.* In
  *Legislative XML for the Semantic Web*, Law, Governance and Technology Series,
  vol. 4, pp. 75–100. Springer, 2011. (Customization via `foreign`,
  `proprietary`, generic elements.)
- **[I8]** Garofalakis, J., Plessas, K., Plessas, A., Spiliopoulou, P.
  *A Project for the Transformation of Greek Legal Documents into Legal Open
  Data.* 22nd Pan-Hellenic Conference on Informatics, ACM, 2018.
  DOI: 10.1145/3291533.3291548.
- **[I9]** Beris, T., Koubarakis, M. *Modeling and Preserving Greek Government
  Decisions Using Semantic Web Technologies and Permissionless Blockchains.*
  ESWC 2018, LNCS vol. 10843, pp. 81–96. DOI: 10.1007/978-3-319-93417-4_6.
- **[I-overview]** *Akoma Ntoso: An Overview* (LegalDocML documentation):
  document types, collections, `components`/`interstitial`/`portion`.
- **[I-survey]** Survey discussion (MDPI *Information* 2020, 11(1):10) noting the
  lack of large-scale automatic structural markup of legal documents and the
  RDF-vs-AKN split among Greek efforts.

---

## Appendix B — Changelog

| Version | Date | Notes |
|---|---|---|
| 0.1.0 | initial | First documentation-grade draft. Element catalog §5, provenance model §2/§8, validation §9. Greek-term column conventional pending an official profile. |

---

*Corrections welcome: any row that a validator or an official Greek/EU profile
contradicts should be updated, with the schema/profile treated as authoritative
over this reference.*
