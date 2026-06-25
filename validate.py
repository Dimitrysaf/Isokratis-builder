#!/usr/bin/env python3
"""Validate an Akoma Ntoso 3.0 XML file against the local XSD schema.

Usage:
    python validate.py <file.xml>

Exits 0 if valid, 1 if invalid.
"""

import sys
from pathlib import Path
from lxml import etree


SCHEMA_PATH = Path(__file__).parent / "schema" / "akomantoso30.xsd"


def load_schema() -> etree.XMLSchema:
    try:
        schema_doc = etree.parse(str(SCHEMA_PATH))
        return etree.XMLSchema(schema_doc)
    except Exception as e:
        print(f"ERROR loading schema {SCHEMA_PATH}: {e}", file=sys.stderr)
        sys.exit(2)


def validate(xml_path: str) -> bool:
    schema = load_schema()
    try:
        doc = etree.parse(xml_path)
    except etree.XMLSyntaxError as e:
        print(f"XML parse error: {e}")
        return False

    if schema.validate(doc):
        print("VALID")
        return True
    else:
        print(f"INVALID — {len(schema.error_log)} error(s):\n")
        for err in schema.error_log:
            print(f"  line {err.line:4d}: {err.message}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <file.xml>", file=sys.stderr)
        sys.exit(2)
    ok = validate(sys.argv[1])
    sys.exit(0 if ok else 1)
