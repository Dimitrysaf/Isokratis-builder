"""Akoma Ntoso 3.0 renderer — lxml-based (Phase C1).

Uses lxml.etree so XML correctness (escaping, encoding, well-formedness)
is structurally guaranteed.  String concatenation was eliminated.

Meta element order follows the normative AKN 3.0 sequence (§5.2):
  identification → publication* → classification* → lifecycle* →
  analysis* → references*

Body vs mainBody: act → body, doc → mainBody (§5.4).
"""

from __future__ import annotations

import re
from datetime import date as date_cls
from typing import Any

from lxml import etree

from .base import BaseRenderer
from ..models import Document, INSTRUMENT_TYPES, AKN_TYPES

AKN_NS = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
AKN    = f"{{{AKN_NS}}}"       # shorthand for lxml Clark notation

# D1 — inline reference pattern: {{href|display text}}
_REF_RE = re.compile(r"\{\{([^|{}\n]+)\|([^|{}\n]+)\}\}")

# eId prefix per AKN element type
_EID_PREFIX: dict[str, str] = {
    "part":         "part",
    "chapter":      "chp",
    "section":      "sec",
    "article":      "art",
    "paragraph":    "para",
    "subparagraph": "subpara",
    "list":         "list",
    "point":        "pnt",
    "indent":       "indent",
    "hcontainer":   "hcontainer",
}


def _sub(parent: etree._Element, tag: str, text: str | None = None, **attrs) -> etree._Element:
    """Create a child element in the AKN namespace, optionally with text and attributes."""
    el = etree.SubElement(parent, AKN + tag, **{k: v for k, v in attrs.items() if v is not None})
    if text is not None:
        el.text = text
    return el


def _mixed(el: etree._Element, text: str) -> None:
    """D1 — set mixed text+<ref> content on an already-created element.

    Any ``{{href|label}}`` patterns in *text* are converted to
    ``<ref href="href">label</ref>`` child elements.  Surrounding plain text
    becomes the element's ``text`` and each ref's ``tail`` as appropriate.
    lxml handles XML-escaping of every value.
    """
    if not text:
        el.text = "\u00a0"
        return
    parts = _REF_RE.split(text)
    # split on 2 capture groups → [text0, href1, label1, text2, href2, label2, …]
    el.text = parts[0] or None
    prev: etree._Element | None = None
    for i in range(1, len(parts), 3):
        href  = parts[i]
        label = parts[i + 1] if i + 1 < len(parts) else ""
        tail  = parts[i + 2] if i + 2 < len(parts) else ""
        ref_el = etree.SubElement(el, AKN + "ref", href=href)
        ref_el.text = label
        ref_el.tail = tail or None
        prev = ref_el
    # If text was entirely whitespace and no refs, ensure non-empty p
    if el.text is None and not len(el):
        el.text = "\u00a0"


def _p(parent: etree._Element, text: str) -> etree._Element:
    """Append <p> to parent with mixed text+ref content."""
    el = etree.SubElement(parent, AKN + "p")
    _mixed(el, text)
    return el


class AkomaNtosoRenderer(BaseRenderer):
    """Render a Document to Akoma Ntoso 3.0 XML (lxml, schema-valid)."""

    def __init__(self, templates=None):
        pass  # templates param kept for API compat

    def render(self, doc: Document) -> str:
        info    = INSTRUMENT_TYPES.get(doc.instrument_type, INSTRUMENT_TYPES["nomos"])
        akn_el  = info["akn_el"]    # "act" or "doc"
        akn_name = info["akn_name"]

        root = etree.Element(AKN + "akomaNtoso", nsmap={None: AKN_NS})
        doc_el = etree.SubElement(root, AKN + akn_el, name=akn_name)

        self._meta(doc_el, doc, info)
        self._preface(doc_el, doc)
        self._preamble(doc_el, doc)

        # §5.4: act → <body>, doc → <mainBody>
        body_tag = "body" if akn_el == "act" else "mainBody"
        self._body(doc_el, doc, body_tag)

        self._conclusions(doc_el, doc)

        return etree.tostring(
            root,
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8",
        ).decode("utf-8")

    # ── §5.2 Meta (STRICT ordering) ───────────────────────────────────────────

    def _meta(self, parent: etree._Element, doc: Document, info: dict) -> None:
        m       = doc.meta or {}
        today   = str(date_cls.today())
        year    = m.get("frbr_year", str(date_cls.today().year)) or str(date_cls.today().year)
        number  = m.get("frbr_number", "") or ""
        enacted = m.get("enacted_date", "") or today
        author  = m.get("author_href", info["author"]) or info["author"]
        language = m.get("language", "ell") or "ell"
        fek_series = m.get("fek_series", "") or ""
        fek_num    = m.get("fek_number", "") or ""
        fek_date   = m.get("fek_date",   "") or today
        subtype    = m.get("frbr_subtype", "") or ""
        keywords_raw = m.get("keywords", "") or ""

        uri_num  = number or "0"
        work_uri = f"/gr/act/{year}/{uri_num}"

        meta_el = etree.SubElement(parent, AKN + "meta")

        # ── identification ─────────────────────────────────────────────────────
        ident = etree.SubElement(meta_el, AKN + "identification", source="#isokratis")

        # FRBRWork
        work = etree.SubElement(ident, AKN + "FRBRWork")
        _sub(work, "FRBRthis", value=f"{work_uri}/main")
        _sub(work, "FRBRuri",  value=work_uri)
        _sub(work, "FRBRdate", date=enacted, name="enacted")
        _sub(work, "FRBRauthor", href=author)
        _sub(work, "FRBRcountry", value="gr")
        if number:
            _sub(work, "FRBRnumber", value=number)
        if subtype:
            _sub(work, "FRBRsubtype", value=subtype)

        # FRBRExpression
        expr = etree.SubElement(ident, AKN + "FRBRExpression")
        _sub(expr, "FRBRthis",     value=f"{work_uri}/{language}@/main")
        _sub(expr, "FRBRuri",      value=f"{work_uri}/{language}@")
        _sub(expr, "FRBRdate",     date=enacted, name="enacted")
        _sub(expr, "FRBRauthor",   href="#isokratis")
        _sub(expr, "FRBRlanguage", language=language)

        # FRBRManifestation
        mani = etree.SubElement(ident, AKN + "FRBRManifestation")
        _sub(mani, "FRBRthis",   value=f"{work_uri}/{language}@/main.xml")
        _sub(mani, "FRBRuri",    value=f"{work_uri}/{language}@.akn")
        _sub(mani, "FRBRdate",   date=today, name="Generation")
        _sub(mani, "FRBRauthor", href="#isokratis")

        # ── publication (ΦΕΚ) ──────────────────────────────────────────────────
        if fek_num:
            fek_show = f"ΦΕΚ {fek_series}΄ {fek_num}/{fek_date}" if fek_series else f"ΦΕΚ {fek_num}/{fek_date}"
            etree.SubElement(
                meta_el, AKN + "publication",
                date=fek_date, name="ΦΕΚ", showAs=fek_show, number=fek_num,
            )

        # ── classification (BEFORE lifecycle per AKN 3.0 §5.2 ordering) ───────
        if keywords_raw:
            kws = [k.strip() for k in keywords_raw.split(",") if k.strip()]
            cls_el = etree.SubElement(meta_el, AKN + "classification", source="#isokratis")
            for i, kw in enumerate(kws, 1):
                etree.SubElement(
                    cls_el, AKN + "keyword",
                    eId=f"kw_{i}", value=kw, showAs=kw, dictionary="#isokratis",
                )

        # ── lifecycle ──────────────────────────────────────────────────────────
        lc = etree.SubElement(meta_el, AKN + "lifecycle", source="#isokratis")
        etree.SubElement(
            lc, AKN + "eventRef",
            date=enacted, type="generation", source=author, eId="ev_enacted",
        )

        # ── analysis (amendments) — rendered by _analysis if present ───────────
        if getattr(doc, "amendments", None):
            self._analysis(meta_el, doc.amendments)

        # ── references (TLC register) ──────────────────────────────────────────
        refs_el = etree.SubElement(meta_el, AKN + "references", source="#isokratis")
        _sub(refs_el, "TLCOrganization",
             eId="parliament", href="/ontology/organization/gr/parliament",
             showAs="Ελληνικό Κοινοβούλιο")
        _sub(refs_el, "TLCOrganization",
             eId="president",  href="/ontology/organization/gr/president",
             showAs="Πρόεδρος της Δημοκρατίας")
        _sub(refs_el, "TLCOrganization",
             eId="isokratis",  href="/ontology/organization/gr/isokratis",
             showAs="Isokratis")

    # ── §5.3 Preface ──────────────────────────────────────────────────────────

    def _preface(self, parent: etree._Element, doc: Document) -> None:
        p = doc.preface or {}
        doc_type   = (p.get("doc_type")   or "").strip()
        doc_number = (p.get("doc_number") or "").strip()
        doc_title  = (p.get("doc_title")  or "").strip()
        doc_date   = (p.get("doc_date")   or "").strip()

        if not any([doc_type, doc_number, doc_title, doc_date]):
            return

        pref_el = etree.SubElement(parent, AKN + "preface")
        if doc_type:
            p_el = etree.SubElement(pref_el, AKN + "p")
            dt = etree.SubElement(p_el, AKN + "docType")
            dt.text = doc_type
        if doc_number:
            p_el = etree.SubElement(pref_el, AKN + "p")
            dn = etree.SubElement(p_el, AKN + "docNumber")
            dn.text = f"ΥΠ' ΑΡΙΘΜ. {doc_number}"
        if doc_title:
            p_el = etree.SubElement(pref_el, AKN + "p")
            dtt = etree.SubElement(p_el, AKN + "docTitle")
            dtt.text = doc_title
        if doc_date:
            p_el = etree.SubElement(pref_el, AKN + "p")
            dd = etree.SubElement(p_el, AKN + "docDate", date=doc_date)
            dd.text = doc_date

    # ── §5.3 Preamble ─────────────────────────────────────────────────────────

    def _preamble(self, parent: etree._Element, doc: Document) -> None:
        p        = doc.preamble or {}
        formula  = (p.get("formula")  or "").strip()
        cit_text = (p.get("citations") or "").strip()
        citations = [c.strip() for c in cit_text.splitlines() if c.strip()]

        if not formula and not citations:
            return

        prea_el = etree.SubElement(parent, AKN + "preamble")
        if formula:
            form_el = etree.SubElement(prea_el, AKN + "formula", name="enactingFormula")
            _p(form_el, formula)
        if citations:
            cits_el = etree.SubElement(prea_el, AKN + "citations")
            for i, cit in enumerate(citations, 1):
                cit_el = etree.SubElement(cits_el, AKN + "citation", eId=f"cit_{i}")
                _p(cit_el, cit)

    # ── §5.4 Body ─────────────────────────────────────────────────────────────

    def _body(self, parent: etree._Element, doc: Document, body_tag: str) -> None:
        body_el = etree.SubElement(parent, AKN + body_tag)
        if doc.body:
            counters: dict[str, int] = {}
            for node in doc.body:
                self._node(body_el, node, parent_eid="", counters=counters)
        else:
            # Both <body> and <mainBody> require at least one hierarchical child.
            # An export with no articles yet still has to be schema-valid, so emit
            # a single empty placeholder container.
            ph = etree.SubElement(body_el, AKN + "hcontainer",
                                  eId="hcontainer_1", name="placeholder")
            cnt = etree.SubElement(ph, AKN + "content")
            etree.SubElement(cnt, AKN + "p").text = " "

    def _node(
        self,
        parent: etree._Element,
        node: dict[str, Any],
        parent_eid: str,
        counters: dict[str, int],
    ) -> etree._Element:
        akn_type  = node.get("akn_type", "hcontainer")
        prefix    = _EID_PREFIX.get(akn_type, "hcontainer")
        name_attr = (node.get("name_attr") or akn_type).strip()

        # Scoped eId counter
        eid_key = f"{parent_eid}__{prefix}" if parent_eid else prefix
        counters[eid_key] = counters.get(eid_key, 0) + 1
        pos   = counters[eid_key]
        local = f"{prefix}_{pos}"
        eid   = f"{parent_eid}__{local}" if parent_eid else local

        # Build element
        if akn_type == "hcontainer":
            el = etree.SubElement(parent, AKN + "hcontainer", eId=eid, name=name_attr)
        else:
            el = etree.SubElement(parent, AKN + akn_type, eId=eid)

        # §5.5 num / heading
        num_val     = (node.get("num")     or "").strip()
        heading_val = (node.get("heading") or "").strip()
        if num_val:
            _sub(el, "num", text=num_val)
        if heading_val:
            _sub(el, "heading", text=heading_val)

        # §5.5 intro
        intro_val = (node.get("intro") or "").strip()
        if intro_val:
            intro_el = etree.SubElement(el, AKN + "intro")
            _p(intro_el, intro_val)

        # Children
        children = node.get("children") or []
        child_counters: dict[str, int] = {}
        for child in children:
            self._node(el, child, eid, child_counters)

        # §5.5/5.6 — the AKN `hierarchy` content model is a strict either/or:
        #   container : intro?, (sub-elements)*, wrapUp?   (NO direct <content>)
        #   leaf      : exactly one <content>              (NO intro/children/wrapUp)
        # Mixing the two (e.g. <intro> beside <content>, or a bare <p>) is
        # rejected by the official schema, so pick exactly one branch.
        content_val = (node.get("content") or "").strip()
        wrapup_val  = (node.get("wrap_up") or "").strip()

        if children or intro_val or wrapup_val:
            # container branch — free text becomes an <alinea> leaf, since a
            # container may not hold a direct <content>.
            if content_val:
                alinea = etree.SubElement(el, AKN + "alinea", eId=f"{eid}__alinea_1")
                cnt = etree.SubElement(alinea, AKN + "content")
                _p(cnt, content_val)
            if wrapup_val:
                wu = etree.SubElement(el, AKN + "wrapUp")
                _p(wu, wrapup_val)
        elif content_val:
            # leaf branch
            cnt = etree.SubElement(el, AKN + "content")
            _p(cnt, content_val)
        else:
            # Empty: structural containers may be legally empty; leaf elements
            # get a placeholder <content> so they are not bare.
            is_structural = akn_type in (
                "part", "chapter", "section", "subsection",
                "list", "hcontainer", "title",
            )
            if not is_structural:
                cnt = etree.SubElement(el, AKN + "content")
                p_el = etree.SubElement(cnt, AKN + "p")
                p_el.text = "\u00a0"   # non-breaking space — not an empty element

        return el

    # ── §5.9 Analysis / amendments ────────────────────────────────────────────

    def _analysis(self, meta_el: etree._Element, amendments: list[dict]) -> None:
        """Render passiveModifications into <analysis> (§5.9).

        Per the authentic AKN 3.0 schema (modificationType / anyOtherType):

        * ``source`` and ``destination`` are **empty** elements that carry the
          reference in their ``@href`` attribute — they do NOT contain a nested
          ``<ref>`` (that earlier assumption was wrong; the official XSD rejects
          any child in the AKN namespace here).
        * ``old`` / ``new`` have an open ``##other`` content model: they hold the
          before/after text "in some non-managed form" and may contain only
          *foreign-namespace* elements (no AKN children, no bare text).  We wrap
          the text in an XHTML ``<p>`` so it is preserved losslessly and still
          validates (processContents="lax").
        """
        if not amendments:
            return
        XHTML = "http://www.w3.org/1999/xhtml"
        analysis_el = etree.SubElement(meta_el, AKN + "analysis", source="#isokratis")
        pm_el = etree.SubElement(analysis_el, AKN + "passiveModifications")
        for i, amd in enumerate(amendments, 1):
            mod_type = amd.get("type", "substitution")
            mod_el = etree.SubElement(pm_el, AKN + "textualMod",
                                      eId=f"mod_{i}", type=mod_type)
            # source — empty element, reference carried by @href (required 1..*)
            src_attrs = {}
            if amd.get("source_href"):
                src_attrs["href"] = amd["source_href"]
            etree.SubElement(mod_el, AKN + "source", **src_attrs)
            # destination — empty element, reference carried by @href (required 1..*)
            dst_attrs = {}
            if amd.get("dest_href"):
                dst_attrs["href"] = amd["dest_href"]
            etree.SubElement(mod_el, AKN + "destination", **dst_attrs)
            # old / new — foreign-namespace (##other) content only
            old_text = amd.get("old_text", "")
            new_text = amd.get("new_text", "")
            if old_text:
                old_el = etree.SubElement(mod_el, AKN + "old")
                etree.SubElement(old_el, f"{{{XHTML}}}p").text = old_text
            if new_text:
                new_el = etree.SubElement(mod_el, AKN + "new")
                etree.SubElement(new_el, f"{{{XHTML}}}p").text = new_text

    # ── §5.10 Conclusions ─────────────────────────────────────────────────────

    def _conclusions(self, parent: etree._Element, doc: Document) -> None:
        c = doc.conclusions or {}
        place    = (c.get("place")      or "").strip()
        dt       = (c.get("date")       or "").strip()
        sigs_raw = (c.get("signatures") or "").strip()
        sig_lines = [s.strip() for s in sigs_raw.splitlines() if s.strip()]

        if not place and not dt and not sig_lines:
            return

        concl_el = etree.SubElement(parent, AKN + "conclusions")
        if place or dt:
            loc = ", ".join(filter(None, [place, dt]))
            _p(concl_el, loc)
        # <signature> is an *inline* element (ANheaderInline); it cannot be a
        # direct child of conclusions, which only accepts block elements.
        # Wrap each in a generic <block name="signature"> per AKN 3.0.
        for sig in sig_lines:
            block_el = etree.SubElement(concl_el, AKN + "block", name="signature")
            sig_el = etree.SubElement(block_el, AKN + "signature")
            _mixed(sig_el, sig)
