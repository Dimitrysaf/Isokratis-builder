"""Akoma Ntoso 3.0 importer — reverse of AkomaNtosoRenderer (Phase D3).

Parses an AKN XML document (as produced by AkomaNtosoRenderer) back into a
:class:`Document`, so that ``render(import_akn(x))`` reproduces ``x`` for the
**source** content.

Note on round-tripping: the renderer stamps ``FRBRManifestation`` with a
``Generation`` date of *today* — a manifestation timestamp, not source data.
That single field is therefore not recoverable to its original value; every
other field round-trips. The D3 test normalises that one date before comparing.
"""

from __future__ import annotations

import re
from lxml import etree

from ..models import Document, INSTRUMENT_TYPES

AKN_NS = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
AKN = f"{{{AKN_NS}}}"
XHTML_NS = "http://www.w3.org/1999/xhtml"

# Hierarchical body element local-names the importer recognises as nodes.
_HIER_TAGS = {
    "part", "chapter", "section", "subsection", "title",
    "article", "paragraph", "subparagraph", "list", "point", "indent",
    "hcontainer",
}


def _local(el: etree._Element) -> str:
    """Local tag name without the namespace."""
    return etree.QName(el).localname


def _find(parent, *tags):
    """First descendant-or-child with the given AKN local tag (direct children)."""
    for child in parent:
        if _local(child) == tags[0]:
            return child
    return None


def _mixed_to_text(el: etree._Element | None) -> str:
    """Inverse of renderer ``_mixed`` — turn text + <ref> back into {{href|label}}.

    A lone non-breaking space (the renderer's empty-leaf placeholder) maps to "".
    """
    if el is None:
        return ""
    parts: list[str] = []
    if el.text:
        parts.append(el.text)
    for child in el:
        if _local(child) == "ref":
            href = child.get("href", "")
            label = child.text or ""
            parts.append(f"{{{{{href}|{label}}}}}")
        if child.tail:
            parts.append(child.tail)
    text = "".join(parts)
    if text == " ":
        return ""
    return text


def _p_text(parent: etree._Element | None) -> str:
    """Text of the first <p> under *parent*, with refs reversed."""
    if parent is None:
        return ""
    p = _find(parent, "p")
    return _mixed_to_text(p)


class AkomaNtosoImporter:
    """Parse AKN 3.0 XML into a :class:`Document` (reverse renderer)."""

    def import_document(self, xml: str | bytes) -> Document:
        if isinstance(xml, str):
            xml = xml.encode("utf-8")
        root = etree.fromstring(xml)
        doc_el = root[0]  # <act> or <doc>
        akn_name = doc_el.get("name", "nomos")
        instrument_type = akn_name if akn_name in INSTRUMENT_TYPES else "nomos"

        d = Document(title="", instrument_type=instrument_type)
        d.meta = {}
        d.preface = {}
        d.preamble = {}
        d.conclusions = {"place": "", "date": "", "signatures": ""}
        d.body = []
        d.amendments = []

        for section in doc_el:
            tag = _local(section)
            if tag == "meta":
                self._read_meta(section, d)
            elif tag == "preface":
                self._read_preface(section, d)
            elif tag == "preamble":
                self._read_preamble(section, d)
            elif tag in ("body", "mainBody"):
                d.body = [self._read_node(c) for c in section
                          if _local(c) in _HIER_TAGS
                          and not (_local(c) == "hcontainer" and c.get("name") == "placeholder")]
            elif tag == "conclusions":
                self._read_conclusions(section, d)

        # title is not stored separately in AKN; mirror the doc title from preface
        d.title = d.preface.get("doc_title", "") or d.title
        return d

    # ── meta ──────────────────────────────────────────────────────────────────
    def _read_meta(self, meta_el, d: Document) -> None:
        m: dict = {}
        ident = _find(meta_el, "identification")
        if ident is not None:
            work = _find(ident, "FRBRWork")
            if work is not None:
                for c in work:
                    lt = _local(c)
                    if lt == "FRBRdate" and c.get("name") == "enacted":
                        m["enacted_date"] = c.get("date", "")
                    elif lt == "FRBRnumber":
                        m["frbr_number"] = c.get("value", "")
                    elif lt == "FRBRsubtype":
                        m["frbr_subtype"] = c.get("value", "")
                    elif lt == "FRBRauthor":
                        m["author_href"] = c.get("href", "")
                    elif lt == "FRBRuri":
                        # /gr/act/{year}/{number}
                        parts = c.get("value", "").strip("/").split("/")
                        if len(parts) >= 3:
                            m["frbr_year"] = parts[2]
            expr = _find(ident, "FRBRExpression")
            if expr is not None:
                lang = _find(expr, "FRBRlanguage")
                if lang is not None:
                    m["language"] = lang.get("language", "ell")

        pub = _find(meta_el, "publication")
        if pub is not None:
            m["fek_number"] = pub.get("number", "")
            m["fek_date"] = pub.get("date", "")
            # showAs: "ΦΕΚ Α΄ 137/..." → series is the token before the ΄ mark
            show = pub.get("showAs", "")
            mt = re.search(r"ΦΕΚ\s+(\S+?)΄", show)
            m["fek_series"] = mt.group(1) if mt else ""

        cls = _find(meta_el, "classification")
        if cls is not None:
            kws = [k.get("value", "") for k in cls if _local(k) == "keyword"]
            m["keywords"] = ", ".join(kws)

        analysis = _find(meta_el, "analysis")
        if analysis is not None:
            self._read_amendments(analysis, d)

        d.meta = m

    # ── preface ───────────────────────────────────────────────────────────────
    def _read_preface(self, pref_el, d: Document) -> None:
        p: dict = {}
        for wrapper in pref_el:           # each is a <p>
            for el in wrapper:
                lt = _local(el)
                if lt == "docType":
                    p["doc_type"] = el.text or ""
                elif lt == "docNumber":
                    txt = el.text or ""
                    p["doc_number"] = txt.replace("ΥΠ' ΑΡΙΘΜ. ", "").strip()
                elif lt == "docTitle":
                    p["doc_title"] = el.text or ""
                elif lt == "docDate":
                    p["doc_date"] = el.get("date", el.text or "")
        d.preface = p

    # ── preamble ──────────────────────────────────────────────────────────────
    def _read_preamble(self, prea_el, d: Document) -> None:
        p: dict = {"formula": "", "citations": ""}
        formula = _find(prea_el, "formula")
        if formula is not None:
            p["formula"] = _p_text(formula)
        cits = _find(prea_el, "citations")
        if cits is not None:
            lines = [_p_text(c) for c in cits if _local(c) == "citation"]
            p["citations"] = "\n".join(lines)
        d.preamble = p

    # ── body nodes ────────────────────────────────────────────────────────────
    def _read_node(self, el) -> dict:
        akn_type = _local(el)
        node: dict = {"akn_type": akn_type, "children": []}
        if akn_type == "hcontainer":
            node["name_attr"] = el.get("name", "")

        for c in el:
            lt = _local(c)
            if lt == "num":
                node["num"] = c.text or ""
            elif lt == "heading":
                node["heading"] = c.text or ""
            elif lt == "intro":
                node["intro"] = _p_text(c)
            elif lt == "wrapUp":
                node["wrap_up"] = _p_text(c)
            elif lt == "content":
                node["content"] = _p_text(c)
            elif lt == "alinea":
                # renderer turns a container's free text into <alinea><content>…
                node["content"] = _p_text(_find(c, "content"))
            elif lt in _HIER_TAGS:
                node["children"].append(self._read_node(c))
        return node

    # ── conclusions ───────────────────────────────────────────────────────────
    def _read_conclusions(self, concl_el, d: Document) -> None:
        c: dict = {"place": "", "date": "", "signatures": ""}
        sigs: list[str] = []
        for el in concl_el:
            lt = _local(el)
            if lt == "p":
                loc = _mixed_to_text(el)
                # renderer: ", ".join([place, date]) → split last ", "
                if ", " in loc:
                    place, dt = loc.rsplit(", ", 1)
                    c["place"], c["date"] = place, dt
                else:
                    c["place"] = loc
            elif lt == "block" and el.get("name") == "signature":
                sig = _find(el, "signature")
                if sig is not None:
                    sigs.append(_mixed_to_text(sig))
        c["signatures"] = "\n".join(sigs)
        d.conclusions = c

    # ── amendments ────────────────────────────────────────────────────────────
    def _read_amendments(self, analysis_el, d: Document) -> None:
        pm = _find(analysis_el, "passiveModifications")
        if pm is None:
            return
        out: list[dict] = []
        for mod in pm:
            if _local(mod) != "textualMod":
                continue
            amd: dict = {"type": mod.get("type", "substitution")}
            src = _find(mod, "source")
            if src is not None and src.get("href"):
                amd["source_href"] = src.get("href")
            dst = _find(mod, "destination")
            if dst is not None and dst.get("href"):
                amd["dest_href"] = dst.get("href")
            old = _find(mod, "old")
            if old is not None:
                amd["old_text"] = "".join(old.itertext()).strip()
            new = _find(mod, "new")
            if new is not None:
                amd["new_text"] = "".join(new.itertext()).strip()
            out.append(amd)
        d.amendments = out
