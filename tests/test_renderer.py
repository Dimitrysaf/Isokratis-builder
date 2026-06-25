"""E1 — Renderer integration test.

Builds a sample document, renders it, validates against the AKN 3.0 XSD,
and asserts the output is schema-valid.  Also regression-tests the golden file.

Run:
    python tests/test_renderer.py
"""

import sys
import uuid
from pathlib import Path

# Project root on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lxml import etree

from src.models.document import Document
from src.renderers.xml_renderer import AkomaNtosoRenderer

SCHEMA_PATH  = Path(__file__).parent.parent / "schema" / "akomantoso30.xsd"
GOLDEN_PATH  = Path(__file__).parent / "golden" / "nomos_min.akn.xml"


def load_schema() -> etree.XMLSchema:
    return etree.XMLSchema(etree.parse(str(SCHEMA_PATH)))


def build_doc(instrument_type: str = "nomos") -> Document:
    doc = Document(title="Test Document", instrument_type=instrument_type)
    doc.meta = {
        "frbr_number": "1234", "frbr_year": "2025", "frbr_subtype": "",
        "enacted_date": "2025-01-15", "language": "ell",
        "author_href": "#parliament",
        "fek_series": "Α", "fek_number": "10", "fek_date": "2025-01-20",
        "keywords": "δοκιμή, ανάπτυξη",
    }
    doc.preface  = {"doc_type": "ΝΟΜΟΣ", "doc_number": "1234",
                    "doc_title": "Νόμος Δοκιμαστικός", "doc_date": "2025-01-15"}
    doc.preamble = {"formula": "Εκδίδομε τον ακόλουθο νόμο:", "citations": "Έχοντας υπόψη τον Ν. 1234/2000."}
    doc.body = [
        {
            "node_id": str(uuid.uuid4()), "akn_type": "article",
            "num": "Άρθρο 1", "heading": "Σκοπός",
            "content": "", "intro": "", "wrap_up": "", "name_attr": "article",
            "children": [
                {
                    "node_id": str(uuid.uuid4()), "akn_type": "paragraph",
                    "num": "1.", "heading": "", "intro": "", "wrap_up": "",
                    "content": "Ο σκοπός του νόμου είναι η δοκιμή.",
                    "name_attr": "paragraph", "children": [],
                },
            ],
        },
    ]
    doc.conclusions = {"place": "Αθήνα", "date": "2025-01-15",
                       "signatures": "Ο Πρωθυπουργός\nΚΩΝΣΤΑΝΤΙΝΟΣ ΔΟΚΙΜΑΣΤΗΣ"}
    return doc


def test_nomos_validates():
    schema   = load_schema()
    renderer = AkomaNtosoRenderer()
    doc      = build_doc("nomos")
    xml_str  = renderer.render(doc)
    tree     = etree.fromstring(xml_str.encode())
    result   = schema.validate(tree)
    if not result:
        for e in schema.error_log:
            print(f"  line {e.line}: {e.message}")
    assert result, "nomos output failed XSD validation"
    print("PASS  test_nomos_validates")


def test_egkykl_uses_mainBody():
    renderer = AkomaNtosoRenderer()
    doc      = build_doc("egkykl")
    xml_str  = renderer.render(doc)
    assert "<akn:mainBody" in xml_str or "mainBody" in xml_str, \
        "egkykl must use mainBody, not body"
    schema = load_schema()
    tree   = etree.fromstring(xml_str.encode())
    result = schema.validate(tree)
    if not result:
        for e in schema.error_log:
            print(f"  line {e.line}: {e.message}")
    assert result, "egkykl output failed XSD validation"
    print("PASS  test_egkykl_uses_mainBody")


def test_amendments_validate():
    schema   = load_schema()
    renderer = AkomaNtosoRenderer()
    doc      = build_doc("nomos")
    doc.amendments = [
        {
            "type":         "substitution",
            "source_href":  "/gr/act/2020/3000/ell@/art_1",
            "source_label": "Ν. 3000/2020 άρθρο 1",
            "dest_href":    "/gr/act/2025/1234/ell@/art_1__para_1",
            "dest_label":   "Ν. 1234/2025 άρθρο 1 παρ. 1",
            "old_text":     "Παλαιό κείμενο.",
            "new_text":     "Νέο κείμενο.",
        },
    ]
    xml_str = renderer.render(doc)
    assert "passiveModifications" in xml_str, "amendments must produce passiveModifications"
    assert "textualMod" in xml_str
    tree   = etree.fromstring(xml_str.encode())
    result = schema.validate(tree)
    if not result:
        for e in schema.error_log:
            print(f"  line {e.line}: {e.message}")
    assert result, "document with amendments failed XSD validation"
    print("PASS  test_amendments_validate")


def test_edge_cases_validate():
    """Nasty input: Greek characters, ampersands, empty body, special chars."""
    schema   = load_schema()
    renderer = AkomaNtosoRenderer()
    doc      = build_doc("nomos")
    # Nasty content: & < > " Greek polytonic
    doc.body = [
        {
            "node_id": str(uuid.uuid4()), "akn_type": "article",
            "num": "Άρθρο 1", "heading": "Δοκιμή & <Ειδικών> Χαρακτήρων",
            "content": "", "intro": "", "wrap_up": "", "name_attr": "article",
            "children": [
                {
                    "node_id": str(uuid.uuid4()), "akn_type": "paragraph",
                    "num": "1.", "heading": "", "intro": "", "wrap_up": "",
                    "content": 'Κείμενο με & < > " και ελληνικά: ᾽Αθῆναι.',
                    "name_attr": "paragraph", "children": [],
                },
            ],
        },
    ]
    xml_str = renderer.render(doc)
    tree    = etree.fromstring(xml_str.encode())  # will raise if malformed
    result  = schema.validate(tree)
    if not result:
        for e in schema.error_log:
            print(f"  line {e.line}: {e.message}")
    assert result, "edge-case output failed XSD validation"
    print("PASS  test_edge_cases_validate")


def test_golden_file():
    """A5/E1 regression: the saved golden file must still validate."""
    if not GOLDEN_PATH.exists():
        print(f"SKIP  test_golden_file (file not found: {GOLDEN_PATH})")
        return
    schema = load_schema()
    tree   = etree.parse(str(GOLDEN_PATH))
    result = schema.validate(tree)
    if not result:
        for e in schema.error_log:
            print(f"  line {e.line}: {e.message}")
    assert result, f"Golden file {GOLDEN_PATH} failed XSD validation"
    print("PASS  test_golden_file")


if __name__ == "__main__":
    tests = [
        test_nomos_validates,
        test_egkykl_uses_mainBody,
        test_amendments_validate,
        test_edge_cases_validate,
        test_golden_file,
    ]
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"FAIL  {t.__name__}: {e}")
            failures.append(t.__name__)
    print()
    if failures:
        print(f"FAILED: {', '.join(failures)}")
        sys.exit(1)
    else:
        print(f"All {len(tests)} tests passed.")
