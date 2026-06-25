"""Akoma Ntoso 3.0 renderer for Greek legislation (§5 mapping reference)."""

from datetime import date as date_cls
from typing import Any
from .base import BaseRenderer
from ..models import Document, INSTRUMENT_TYPES, AKN_TYPES


AKN_NS = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"

# AKN eId prefix per element type
_EID = {
    "part": "part", "chapter": "chp", "section": "sec",
    "article": "art", "paragraph": "para", "subparagraph": "subpara",
    "list": "list", "point": "pnt", "indent": "indent",
    "hcontainer": "hcontainer",
}


def _x(text: str) -> str:
    """XML-escape a string."""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _ind(depth: int) -> str:
    return "  " * depth


class AkomaNtosoRenderer(BaseRenderer):
    """Render a Document to Akoma Ntoso 3.0 XML following the Greek legislation mapping."""

    def __init__(self, templates=None):
        # templates param kept for API compat but unused
        pass

    def render(self, doc: Document) -> str:
        info = INSTRUMENT_TYPES.get(doc.instrument_type, INSTRUMENT_TYPES["nomos"])
        akn_el   = info["akn_el"]
        akn_name = info["akn_name"]

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<akomaNtoso xmlns="{AKN_NS}">',
            f'  <{akn_el} name="{akn_name}">',
        ]
        lines += self._meta(doc, info)
        lines += self._preface(doc)
        lines += self._preamble(doc)
        lines += self._body(doc)
        lines += self._conclusions(doc)
        lines.append(f'  </{akn_el}>')
        lines.append('</akomaNtoso>')
        return "\n".join(lines) + "\n"

    # ── §5.2 Meta block ───────────────────────────────────────────────────────

    def _meta(self, doc: Document, info: dict) -> list[str]:
        m = doc.meta or {}
        today = str(date_cls.today())
        year       = _x(m.get("frbr_year", str(date_cls.today().year)))
        number     = _x(m.get("frbr_number", ""))
        enacted    = _x(m.get("enacted_date", "") or today)
        author     = _x(m.get("author_href", info["author"]))
        language   = _x(m.get("language", "ell"))
        fek_series = _x(m.get("fek_series", ""))
        fek_num    = _x(m.get("fek_number", ""))
        fek_date   = _x(m.get("fek_date", "") or today)
        subtype    = _x(m.get("frbr_subtype", ""))
        keywords_raw = m.get("keywords", "")

        uri_num = number or "0"
        work_uri = f"/gr/act/{year}/{uri_num}"

        ls = ["    <meta>"]

        # identification / FRBR
        ls += [
            '      <identification source="#isokratis">',
            '        <FRBRWork>',
            f'          <FRBRthis value="{work_uri}/main"/>',
            f'          <FRBRuri value="{work_uri}"/>',
            f'          <FRBRdate date="{enacted}" name="enacted"/>',
            f'          <FRBRauthor href="{author}"/>',
            '          <FRBRcountry value="gr"/>',
        ]
        if number:
            ls.append(f'          <FRBRnumber value="{number}"/>')
        if subtype:
            ls.append(f'          <FRBRsubtype value="{subtype}"/>')
        ls += [
            '        </FRBRWork>',
            '        <FRBRExpression>',
            f'          <FRBRthis value="{work_uri}/{language}@/main"/>',
            f'          <FRBRuri value="{work_uri}/{language}@"/>',
            f'          <FRBRdate date="{enacted}" name="enacted"/>',
            '          <FRBRauthor href="#isokratis"/>',
            f'          <FRBRlanguage language="{language}"/>',
            '        </FRBRExpression>',
            '        <FRBRManifestation>',
            f'          <FRBRthis value="{work_uri}/{language}@/main.xml"/>',
            f'          <FRBRuri value="{work_uri}/{language}@.akn"/>',
            f'          <FRBRdate date="{today}" name="Generation"/>',
            '          <FRBRauthor href="#isokratis"/>',
            '        </FRBRManifestation>',
            '      </identification>',
        ]

        # publication (ΦΕΚ) — §5.2
        if fek_num:
            fek_show = f"ΦΕΚ {fek_series}΄ {fek_num}/{fek_date}" if fek_series else f"ΦΕΚ {fek_num}/{fek_date}"
            ls.append(f'      <publication date="{fek_date}" name="ΦΕΚ" showAs="{_x(fek_show)}" number="{fek_num}"/>')

        # lifecycle — §5.2
        ls += [
            '      <lifecycle source="#isokratis">',
            f'        <eventRef date="{enacted}" type="generation" source="{author}" eId="ev_enacted"/>',
            '      </lifecycle>',
        ]

        # classification / keywords — §5.2
        if keywords_raw:
            kws = [k.strip() for k in keywords_raw.split(",") if k.strip()]
            ls.append('      <classification source="#isokratis">')
            for i, kw in enumerate(kws, 1):
                ls.append(f'        <keyword eId="kw_{i}" value="{_x(kw)}" showAs="{_x(kw)}" dictionary="#isokratis"/>')
            ls.append('      </classification>')

        # references / TLC — §5.8
        ls += [
            '      <references source="#isokratis">',
            '        <TLCOrganization eId="parliament" href="/ontology/organization/gr/parliament" showAs="Ελληνικό Κοινοβούλιο"/>',
            '        <TLCOrganization eId="president" href="/ontology/organization/gr/president" showAs="Πρόεδρος της Δημοκρατίας"/>',
            '        <TLCOrganization eId="isokratis" href="/ontology/organization/gr/isokratis" showAs="Isokratis"/>',
            '      </references>',
        ]

        ls.append("    </meta>")
        return ls

    # ── §5.3 Preface ──────────────────────────────────────────────────────────

    def _preface(self, doc: Document) -> list[str]:
        p = doc.preface or {}
        doc_type   = _x(p.get("doc_type", ""))
        doc_number = _x(p.get("doc_number", ""))
        doc_title  = _x(p.get("doc_title", ""))
        doc_date   = _x(p.get("doc_date", ""))

        if not any([doc_type, doc_number, doc_title, doc_date]):
            return []

        ls = ["    <preface>"]
        if doc_type:
            ls.append(f'      <p><docType>{doc_type}</docType></p>')
        if doc_number:
            ls.append(f'      <p><docNumber>ΥΠ&apos; ΑΡΙΘΜ. {doc_number}</docNumber></p>')
        if doc_title:
            ls.append(f'      <p><docTitle>{doc_title}</docTitle></p>')
        if doc_date:
            ls.append(f'      <p><docDate date="{doc_date}">{doc_date}</docDate></p>')
        ls.append("    </preface>")
        return ls

    # ── §5.3 Preamble ─────────────────────────────────────────────────────────

    def _preamble(self, doc: Document) -> list[str]:
        p = doc.preamble or {}
        formula  = _x(p.get("formula", ""))
        cit_text = p.get("citations", "")
        citations = [c.strip() for c in (cit_text or "").splitlines() if c.strip()]

        if not formula and not citations:
            return []

        ls = ["    <preamble>"]
        if formula:
            ls.append(f'      <formula name="enactingFormula"><p>{formula}</p></formula>')
        if citations:
            ls.append("      <citations>")
            for i, cit in enumerate(citations, 1):
                ls.append(f'        <citation eId="cit_{i}"><p>{_x(cit)}</p></citation>')
            ls.append("      </citations>")
        ls.append("    </preamble>")
        return ls

    # ── §5.4 Body hierarchy ───────────────────────────────────────────────────

    def _body(self, doc: Document) -> list[str]:
        ls = ["    <body>"]
        if doc.body:
            counters: dict[str, int] = {}
            for node in doc.body:
                ls += self._node(node, depth=3, parent_eid="", counters=counters)
        else:
            ls.append("      <!-- κενό κείμενο -->")
        ls.append("    </body>")
        return ls

    def _node(self, node: dict, depth: int, parent_eid: str, counters: dict) -> list[str]:
        akn_type = node.get("akn_type", "hcontainer")
        type_info = AKN_TYPES.get(akn_type, AKN_TYPES["hcontainer"])
        prefix    = _EID.get(akn_type, "hcontainer")

        # eId counter scoped to parent
        eid_key = f"{parent_eid}__{prefix}" if parent_eid else prefix
        counters[eid_key] = counters.get(eid_key, 0) + 1
        pos   = counters[eid_key]
        local = f"{prefix}_{pos}"
        eid   = f"{parent_eid}__{local}" if parent_eid else local

        num_val     = _x(str(node.get("num", "") or ""))
        heading_val = _x(str(node.get("heading", "") or ""))
        content_val = _x(str(node.get("content", "") or ""))
        intro_val   = _x(str(node.get("intro", "") or ""))
        wrapup_val  = _x(str(node.get("wrap_up", "") or ""))
        name_attr   = _x(str(node.get("name_attr", "section") or "section"))
        ind         = _ind(depth)

        # Build opening tag
        if akn_type == "hcontainer":
            open_tag = f'{ind}<hcontainer eId="{eid}" name="{name_attr}">'
            close_tag = f'{ind}</hcontainer>'
        else:
            open_tag = f'{ind}<{akn_type} eId="{eid}">'
            close_tag = f'{ind}</{akn_type}>'

        ls = [open_tag]

        # §5.5 num / heading
        if num_val:
            ls.append(f'{ind}  <num>{num_val}</num>')
        if heading_val:
            ls.append(f'{ind}  <heading>{heading_val}</heading>')

        # §5.5 intro (before list children)
        if intro_val:
            ls.append(f'{ind}  <intro><p>{intro_val}</p></intro>')

        # Children
        children = node.get("children", [])
        child_counters: dict[str, int] = {}
        for child in children:
            ls += self._node(child, depth + 1, eid, child_counters)

        # §5.5 content (leaf text container — §5.6 p inside content)
        if content_val and not children:
            ls.append(f'{ind}  <content><p>{content_val}</p></content>')
        elif content_val and children:
            # content goes as alinea if there are also children (rare)
            ls.append(f'{ind}  <alinea><p>{content_val}</p></alinea>')

        # §5.5 wrapUp (after list children)
        if wrapup_val and children:
            ls.append(f'{ind}  <wrapUp><p>{wrapup_val}</p></wrapUp>')

        # Ensure schema-valid: leaves without content get empty content
        if not children and not content_val and akn_type not in ("part", "chapter", "section", "list", "hcontainer"):
            ls.append(f'{ind}  <content><p/></content>')

        ls.append(close_tag)
        return ls

    # ── §5.10 Conclusions ─────────────────────────────────────────────────────

    def _conclusions(self, doc: Document) -> list[str]:
        c = doc.conclusions or {}
        place = _x(c.get("place", ""))
        dt    = _x(c.get("date", ""))
        sigs  = c.get("signatures", "")
        sig_lines = [s.strip() for s in (sigs or "").splitlines() if s.strip()]

        if not place and not dt and not sig_lines:
            return []

        ls = ["    <conclusions>"]
        if place or dt:
            loc = ", ".join(filter(None, [place, dt]))
            ls.append(f'      <p>{_x(loc)}</p>')
        for sig in sig_lines:
            ls.append(f'      <signature><p>{_x(sig)}</p></signature>')
        ls.append("    </conclusions>")
        return ls
