"""Akoma Ntoso 3.0 Document model for Greek legislation."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


# ── Instrument type catalogue ─────────────────────────────────────────────────

INSTRUMENT_TYPES = {
    "nomos":   {"label": "ΝΟΜΟΣ",                           "akn_el": "act",  "akn_name": "nomos",   "author": "#parliament"},
    "pd":      {"label": "ΠΡΟΕΔΡΙΚΟ ΔΙΑΤΑΓΜΑ",             "akn_el": "act",  "akn_name": "pd",      "author": "#president"},
    "pnp":     {"label": "ΠΡΑΞΗ ΝΟΜΟΘΕΤΙΚΟΥ ΠΕΡΙΕΧΟΜΕΝΟΥ", "akn_el": "act",  "akn_name": "pnp",     "author": "#cabinet"},
    "ya":      {"label": "ΥΠΟΥΡΓΙΚΗ ΑΠΟΦΑΣΗ",              "akn_el": "act",  "akn_name": "ya",      "author": "#minister"},
    "egkykl":  {"label": "ΕΓΚΥΚΛΙΟΣ",                      "akn_el": "doc",  "akn_name": "egkykl",  "author": "#minister"},
    "kodikop": {"label": "ΚΩΔΙΚΟΠΟΙΗΣΗ",                   "akn_el": "act",  "akn_name": "kodikop", "author": "#parliament"},
}

# ── AKN node type catalogue ───────────────────────────────────────────────────

AKN_TYPES = {
    "part":         {"label": "Μέρος",             "eid_prefix": "part",    "fields": ["num", "heading"],           "can_add": ["chapter", "section", "article", "hcontainer"]},
    "chapter":      {"label": "Κεφάλαιο",          "eid_prefix": "chp",     "fields": ["num", "heading"],           "can_add": ["section", "article", "hcontainer"]},
    "section":      {"label": "Τμήμα",             "eid_prefix": "sec",     "fields": ["num", "heading"],           "can_add": ["article", "hcontainer"]},
    "article":      {"label": "Άρθρο",             "eid_prefix": "art",     "fields": ["num", "heading"],           "can_add": ["paragraph", "subparagraph", "list"]},
    "paragraph":    {"label": "Παράγραφος",        "eid_prefix": "para",    "fields": ["num", "content"],           "can_add": ["subparagraph", "list"]},
    "subparagraph": {"label": "Εδάφιο",            "eid_prefix": "subpara", "fields": ["content"],                  "can_add": []},
    "list":         {"label": "Απαρίθμηση",        "eid_prefix": "list",    "fields": ["intro", "wrap_up"],         "can_add": ["point"]},
    "point":        {"label": "Περίπτωση",         "eid_prefix": "pnt",     "fields": ["num", "content"],           "can_add": ["indent"]},
    "indent":       {"label": "Υποπερίπτωση",      "eid_prefix": "indent",  "fields": ["num", "content"],           "can_add": []},
    "hcontainer":   {"label": "Τμήμα (ελεύθερο)",  "eid_prefix": "hcontainer", "fields": ["name_attr", "num", "heading"], "can_add": ["part", "chapter", "section", "article", "paragraph", "hcontainer"]},
}

BODY_ROOT_CAN_ADD = ["part", "chapter", "article", "hcontainer"]


def _default_meta(instrument_type: str) -> dict:
    info = INSTRUMENT_TYPES.get(instrument_type, INSTRUMENT_TYPES["nomos"])
    return {
        "frbr_number": "",
        "frbr_year": str(datetime.now().year),
        "frbr_subtype": "",
        "fek_series": "Α",
        "fek_number": "",
        "fek_date": "",
        "enacted_date": "",
        "author_href": info["author"],
        "language": "ell",
        "keywords": "",
    }


def _default_preface(instrument_type: str) -> dict:
    info = INSTRUMENT_TYPES.get(instrument_type, INSTRUMENT_TYPES["nomos"])
    return {
        "doc_type": info["label"],
        "doc_number": "",
        "doc_title": "",
        "doc_date": "",
    }


def _default_preamble(instrument_type: str) -> dict:
    labels = {
        "nomos":   "Εκδίδομε τον ακόλουθο νόμο που ψηφίσθηκε από τη Βουλή:",
        "pd":      "Έχοντας υπόψη:",
        "pnp":     "Έχοντας υπόψη:",
        "ya":      "Έχοντας υπόψη:",
        "egkykl":  "",
        "kodikop": "Εκδίδομε τον ακόλουθο κώδικα:",
    }
    return {
        "formula": labels.get(instrument_type, ""),
        "citations": "",
    }


# ── Document dataclass ────────────────────────────────────────────────────────

@dataclass
class Document:
    """An AKN 3.0 legislative document."""
    doc_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    instrument_type: str = "nomos"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    meta: dict = field(default_factory=dict)
    preface: dict = field(default_factory=dict)
    preamble: dict = field(default_factory=dict)
    body: list = field(default_factory=list)
    conclusions: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.meta:
            self.meta = _default_meta(self.instrument_type)
        if not self.preface:
            self.preface = _default_preface(self.instrument_type)
        if not self.preamble:
            self.preamble = _default_preamble(self.instrument_type)
        if not self.conclusions:
            self.conclusions = {"place": "", "date": "", "signatures": ""}

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "instrument_type": self.instrument_type,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "meta": self.meta,
            "preface": self.preface,
            "preamble": self.preamble,
            "body": self.body,
            "conclusions": self.conclusions,
        }

    @staticmethod
    def from_dict(data: dict) -> "Document":
        itype = data.get("instrument_type", "nomos")
        d = Document.__new__(Document)
        d.doc_id = data.get("doc_id", str(uuid.uuid4()))
        d.title = data.get("title", "")
        d.instrument_type = itype
        d.created_at = data.get("created_at", datetime.now().isoformat())
        d.updated_at = data.get("updated_at", datetime.now().isoformat())
        d.meta = data.get("meta") or _default_meta(itype)
        d.preface = data.get("preface") or _default_preface(itype)
        d.preamble = data.get("preamble") or _default_preamble(itype)
        d.body = data.get("body") or []
        d.conclusions = data.get("conclusions") or {"place": "", "date": "", "signatures": ""}
        return d

    def update_modified_time(self):
        self.updated_at = datetime.now().isoformat()
