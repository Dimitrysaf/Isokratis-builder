# Isokratis — Legislature Builder

Web application for authoring Greek legislative documents in **Akoma Ntoso 3.0** XML (OASIS LegalDocML standard).

## Features

| Area | Details |
|------|---------|
| **Instrument types** | Νόμος, Προεδρικό Διάταγμα, ΠΝΠ, Υπουργική Απόφαση, Εγκύκλιος, Κωδικοποίηση |
| **AKN structure** | `act`/`doc` · full meta block · preface · preamble · body/mainBody · conclusions |
| **Hierarchy** | part · chapter · section · article · paragraph · subparagraph · list · point · indent · hcontainer |
| **Inline refs** | `{{href\|label}}` in content → `<ref href="…">label</ref>` |
| **Amendments** | Structured `textualMod` records → `<analysis><passiveModifications>` |
| **Schema** | Validated against local AKN 3.0 XSD (`schema/akomantoso30.xsd`) |
| **Storage** | SQLite at `~/.isokratis/documents.db` with version history |
| **Editor** | LEOS-style: outline panel / document canvas / properties panel |

## Quick Start

```bash
pip install -r requirements.txt
python web_app.py          # dev server on port 5000
```

Then open http://localhost:5000

## Validation & Testing

```bash
# Generate a conformant sample document
python make_sample.py

# Validate any AKN file against the local XSD
python validate.py sample.xml

# Full renderer test suite (5 tests)
python tests/test_renderer.py
```

## Project Structure

```
├── web_app.py                     Flask application entry point
├── make_sample.py                 Build sample.xml for validation smoke-test
├── validate.py                    CLI XSD validator (lxml)
├── schema/
│   └── akomantoso30.xsd           AKN 3.0 profile schema (written from spec)
├── src/
│   ├── models/
│   │   ├── document.py            Document dataclass + INSTRUMENT_TYPES + AKN_TYPES
│   │   └── __init__.py
│   ├── renderers/
│   │   ├── xml_renderer.py        lxml-based AKN 3.0 renderer (Phase C1)
│   │   ├── base.py                BaseRenderer ABC
│   │   └── __init__.py
│   └── db/
│       ├── schema.py              SQLite schema creation
│       ├── persistence.py         DocumentRepository / VersionRepository
│       └── __init__.py
├── templates_web/
│   ├── base.html
│   ├── index.html
│   ├── new_document.html
│   └── edit_document.html         LEOS-style 3-panel editor
├── tests/
│   ├── test_renderer.py           Integration tests (nomos, egkykl, amendments, edge cases, golden)
│   └── golden/
│       └── nomos_min.akn.xml      Regression golden file
└── requirements.txt               flask, gunicorn, Jinja2, lxml>=5.0
```

## Inline References (D1)

In any content / intro / wrapUp field use the markup:

```
Βλ. {{/gr/act/2020/4782/ell@/art_5|Ν. 4782/2020 άρθρο 5}} για λεπτομέρειες.
```

The renderer converts this to:

```xml
<p>Βλ. <ref href="/gr/act/2020/4782/ell@/art_5">Ν. 4782/2020 άρθρο 5</ref> για λεπτομέρειες.</p>
```

## Amendments (D2)

In the editor, click **Τροποποιήσεις** in the outline to add `textualMod` records.  
Each record becomes:

```xml
<analysis source="#isokratis">
  <passiveModifications>
    <textualMod eId="mod_1" type="substitution">
      <source><ref href="…">Ν. 3000/2020 άρ. 1</ref></source>
      <destination><ref href="…">Ν. 1234/2025 άρ. 1 παρ. 1</ref></destination>
      <old>Παλαιό κείμενο.</old>
      <new>Νέο κείμενο.</new>
    </textualMod>
  </passiveModifications>
</analysis>
```

## Meta Element Ordering (AKN 3.0 §5.2)

The renderer follows the normative sequence:

```
identification → publication* → classification* → lifecycle* → analysis* → references*
```

## AKN Type Mapping (C3 Decision)

| Greek term | AKN element | eId prefix |
|-----------|-------------|------------|
| εδάφιο | `<subparagraph>` | `subpara` |
| περίπτωση | `<list>/<point>` | `list`/`pnt` |
| υποπερίπτωση | `<indent>` | `indent` |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Document list |
| GET/POST | `/documents/new` | Create document |
| GET | `/documents/<id>` | Editor |
| POST | `/api/documents/<id>/save` | Auto-save (JSON) |
| POST | `/api/documents/<id>/version` | Save named version |
| POST | `/api/documents/<id>/restore/<vid>` | Restore version |
| GET | `/documents/<id>/export/akn` | Download `.akn.xml` |
| POST | `/api/preview/akn` | Live XML preview |
| POST | `/documents/<id>/delete` | Delete |

## License

TBD
