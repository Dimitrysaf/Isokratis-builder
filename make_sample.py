#!/usr/bin/env python3
"""Build a minimal but complete sample Greek νόμος and write it to sample.xml.

Run:
    python make_sample.py
    python validate.py sample.xml
"""

import sys
from pathlib import Path

# ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent))

from src.models.document import Document
from src.renderers.xml_renderer import AkomaNtosoRenderer


def build_sample() -> Document:
    doc = Document(
        title="Νόμος για τη Δοκιμαστική Νομοθεσία",
        instrument_type="nomos",
    )

    doc.meta = {
        "frbr_number":  "4999",
        "frbr_year":    "2025",
        "frbr_subtype": "",
        "enacted_date": "2025-06-01",
        "language":     "ell",
        "author_href":  "#parliament",
        "fek_series":   "Α",
        "fek_number":   "137",
        "fek_date":     "2025-06-05",
        "keywords":     "δοκιμαστική, νομοθεσία",
    }

    doc.preface = {
        "doc_type":   "ΝΟΜΟΣ",
        "doc_number": "4999",
        "doc_title":  "Νόμος για τη Δοκιμαστική Νομοθεσία",
        "doc_date":   "2025-06-01",
    }

    doc.preamble = {
        "formula": "Εκδίδομε τον ακόλουθο νόμο που ψηφίσθηκε από τη Βουλή:",
        "citations": (
            "Έχοντας υπόψη το άρθρο 43 παρ. 2 του Συντάγματος.\n"
            "Τον νόμο 3852/2010 (ΦΕΚ Α΄ 87)."
        ),
    }

    import uuid

    doc.body = [
        {
            "node_id":   str(uuid.uuid4()),
            "akn_type":  "article",
            "num":       "Άρθρο 1",
            "heading":   "Σκοπός",
            "content":   "",
            "intro":     "",
            "wrap_up":   "",
            "name_attr": "article",
            "children": [
                {
                    "node_id":   str(uuid.uuid4()),
                    "akn_type":  "paragraph",
                    "num":       "1.",
                    "heading":   "",
                    "content":   "Σκοπός του παρόντος νόμου είναι η δοκιμαστική νομοθεσία.",
                    "intro":     "",
                    "wrap_up":   "",
                    "name_attr": "paragraph",
                    "children":  [],
                },
                {
                    "node_id":   str(uuid.uuid4()),
                    "akn_type":  "paragraph",
                    "num":       "2.",
                    "heading":   "",
                    "content":   "Οι διατάξεις ισχύουν από τη δημοσίευσή τους στην Εφημερίδα της Κυβερνήσεως.",
                    "intro":     "",
                    "wrap_up":   "",
                    "name_attr": "paragraph",
                    "children":  [],
                },
            ],
        },
        {
            "node_id":   str(uuid.uuid4()),
            "akn_type":  "article",
            "num":       "Άρθρο 2",
            "heading":   "Έναρξη ισχύος",
            "content":   "",
            "intro":     "",
            "wrap_up":   "",
            "name_attr": "article",
            "children": [
                {
                    "node_id":   str(uuid.uuid4()),
                    "akn_type":  "paragraph",
                    "num":       "1.",
                    "heading":   "",
                    "content":   "Ο παρών νόμος ισχύει από την ημερομηνία δημοσίευσής του στην Εφημερίδα της Κυβερνήσεως.",
                    "intro":     "",
                    "wrap_up":   "",
                    "name_attr": "paragraph",
                    "children":  [],
                },
            ],
        },
    ]

    doc.conclusions = {
        "place":      "Αθήνα",
        "date":       "2025-06-01",
        "signatures": "Ο Πρόεδρος της Δημοκρατίας\nΚΩΝΣΤΑΝΤΙΝΟΣ ΠΑΠΑΔΟΠΟΥΛΟΣ",
    }

    return doc


if __name__ == "__main__":
    doc      = build_sample()
    renderer = AkomaNtosoRenderer()
    xml      = renderer.render(doc)
    out      = Path("sample.xml")
    out.write_text(xml, encoding="utf-8")
    print(f"Written: {out}  ({len(xml)} bytes)")
    print("Run: python validate.py sample.xml")
