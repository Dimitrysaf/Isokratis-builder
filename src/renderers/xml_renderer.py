"""Akoma Ntoso 3.0 renderer for Greek legal documents."""

import re
from typing import Dict, Any
from datetime import date
from ..models import Document, Node, Template
from .base import BaseRenderer


# Map template_id prefixes → AKN element names
_TPL_TO_AKN = {
    "tpl_nomos":    "act",
    "tpl_pd":       "act",
    "tpl_pnp":      "act",
    "tpl_apofasi":  "act",
    "tpl_egkykl":   "doc",
    "tpl_kodikop":  "act",
    "tpl_fek":      "act",
    "tpl_meros":    "part",
    "tpl_kefalaio": "chapter",
    "tpl_arthro":   "article",
    "tpl_paragrafos": "paragraph",
    "tpl_periptosi":  "point",
    "tpl_ypopeript":  "indent",
    "tpl_foreis":   "FRBRauthor",
    "tpl_prosopo":  "person",
    "tpl_parapomp": "ref",
}

_DOC_LEVEL_TPLS = {"tpl_nomos", "tpl_pd", "tpl_pnp", "tpl_apofasi", "tpl_egkykl", "tpl_kodikop", "tpl_fek"}
_BODY_LEVEL_TPLS = {"tpl_meros", "tpl_kefalaio", "tpl_arthro", "tpl_paragrafos", "tpl_periptosi", "tpl_ypopeript"}


def _slug(tpl_id: str) -> str:
    """Return the prefix part of a template id (e.g. tpl_arthro)."""
    return tpl_id if "_" not in tpl_id else "_".join(tpl_id.split("_")[:2])


def _eid(node: Node, position: int = 1) -> str:
    """Build a simple eId for a node."""
    tpl = node.template_id or node.node_type
    prefix = tpl.replace("tpl_", "")
    num = node.data.get("number", node.data.get("arthro", node.data.get("id", position)))
    return f"{prefix}_{num}" if num else f"{prefix}_{position}"


class AkomaNtosoRenderer(BaseRenderer):
    """Render documents to Akoma Ntoso 3.0 XML."""

    AKN_NS = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
    AKN_EL = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0/AKN"

    def render(self, doc: Document) -> str:
        """Render a Document to a full Akoma Ntoso 3.0 XML string."""
        doc_type, doc_name = self._detect_doc_type(doc)
        meta_block = self._build_meta(doc)
        body_xml = self._render_body(doc)

        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<akomaNtoso xmlns="{self.AKN_NS}">\n'
            f'  <{doc_type} name="{doc_name}">\n'
            f'{meta_block}'
            f'{body_xml}'
            f'  </{doc_type}>\n'
            '</akomaNtoso>\n'
        )

    # ── Document-type detection ────────────────────────────────────────────

    def _detect_doc_type(self, doc: Document):
        """Return (akn_element, name_attr) for the top-level AKN element."""
        for child in doc.root.children:
            tpl_id = child.template_id or ""
            prefix = _slug(tpl_id)
            if prefix in _DOC_LEVEL_TPLS:
                if prefix == "tpl_egkykl":
                    return "doc", "circular"
                return "act", prefix.replace("tpl_", "")
        return "act", "act"

    # ── Meta block ─────────────────────────────────────────────────────────

    def _build_meta(self, doc: Document) -> str:
        today = doc.metadata.get("created_at", str(date.today()))[:10]
        title_esc = self._x(doc.title)
        uri = f"/gr/act/{today}/1"
        lines = [
            '    <meta>',
            '      <identification source="#isokratis">',
            '        <FRBRWork>',
            f'          <FRBRthis value="{uri}/main"/>',
            f'          <FRBRuri value="{uri}"/>',
            f'          <FRBRdate date="{today}" name="Generation"/>',
            '          <FRBRauthor href="#parliament"/>',
            '          <FRBRcountry value="GR"/>',
            '        </FRBRWork>',
            '        <FRBRExpression>',
            f'          <FRBRthis value="{uri}/gre@/main"/>',
            f'          <FRBRuri value="{uri}/gre@"/>',
            f'          <FRBRdate date="{today}" name="Generation"/>',
            '          <FRBRauthor href="#isokratis"/>',
            '          <FRBRlanguage language="gre"/>',
            '        </FRBRExpression>',
            '        <FRBRManifestation>',
            f'          <FRBRthis value="{uri}/gre@/main.xml"/>',
            f'          <FRBRuri value="{uri}/gre@.akn"/>',
            f'          <FRBRdate date="{today}" name="Generation"/>',
            '          <FRBRauthor href="#isokratis"/>',
            '        </FRBRManifestation>',
            '      </identification>',
            '      <references source="#isokratis">',
            '        <TLCOrganization eId="parliament" href="/ontology/organization/gr/parliament" showAs="Ελληνικό Κοινοβούλιο"/>',
            '        <TLCOrganization eId="isokratis" href="/ontology/organization/gr/isokratis" showAs="Isokratis"/>',
            '      </references>',
            f'      <proprietary source="#isokratis">',
            f'        <gr:title xmlns:gr="http://isokratis.gr/akn">{title_esc}</gr:title>',
            f'      </proprietary>',
            '    </meta>',
        ]
        return "\n".join(lines) + "\n"

    # ── Body ───────────────────────────────────────────────────────────────

    def _render_body(self, doc: Document) -> str:
        inner = ""
        for i, child in enumerate(doc.root.children, 1):
            inner += self._render_akn_node(child, depth=3, position=i)
        if not inner.strip():
            inner = "      <!-- empty document -->\n"
        return f"    <body>\n{inner}    </body>\n"

    # ── Node dispatch ──────────────────────────────────────────────────────

    def _render_akn_node(self, node: Node, depth: int = 3, position: int = 1) -> str:
        indent = "  " * depth
        tpl_id = node.template_id or ""
        prefix = _slug(tpl_id)

        # Use template Jinja render if available and non-trivial
        if tpl_id and tpl_id in self.templates:
            tpl_def = self.templates[tpl_id]
            if tpl_def.render_template and tpl_def.render_template.strip():
                rendered = self._render_template_instance_xml(node, tpl_def, depth, position)
                if rendered:
                    return rendered

        # Fallback: structural mapping
        akn_el = _TPL_TO_AKN.get(prefix, "hcontainer")
        return self._render_structural(node, akn_el, depth, position)

    def _render_structural(self, node: Node, akn_el: str, depth: int, position: int) -> str:
        indent = "  " * depth
        eid = _eid(node, position)
        data = node.data

        # Collect heading / number / content from data fields
        num_val = data.get("number", data.get("arthro", data.get("id", "")))
        heading_val = (
            data.get("title") or data.get("titlos") or
            data.get("name") or data.get("heading") or
            data.get("perigrafi") or ""
        )
        content_val = (
            data.get("content") or data.get("keimeno") or
            data.get("text") or ""
        )

        lines = [f'{indent}<{akn_el} eId="{self._x(eid)}">']

        if num_val:
            lines.append(f'{indent}  <num>{self._x(str(num_val))}</num>')
        if heading_val:
            lines.append(f'{indent}  <heading>{self._x(str(heading_val))}</heading>')

        # Render children recursively first
        child_xml = ""
        for i, child in enumerate(node.children, 1):
            child_xml += self._render_akn_node(child, depth + 1, i)

        if content_val:
            lines.append(f'{indent}  <intro><p>{self._x(str(content_val))}</p></intro>')

        # Extra data fields as akn:FRBRprop or gr:prop
        skip_keys = {"number", "arthro", "id", "title", "titlos", "name", "heading",
                     "perigrafi", "content", "keimeno", "text"}
        extra = {k: v for k, v in data.items() if k not in skip_keys and v}
        if extra:
            lines.append(f'{indent}  <proprietary source="#isokratis">')
            for k, v in extra.items():
                lines.append(f'{indent}    <gr:{self._safe_tag(k)} xmlns:gr="http://isokratis.gr/akn">{self._x(str(v))}</gr:{self._safe_tag(k)}>')
            lines.append(f'{indent}  </proprietary>')

        if child_xml:
            lines.append(child_xml.rstrip("\n"))
        elif not content_val:
            lines.append(f'{indent}  <content><p/></content>')

        lines.append(f'{indent}</{akn_el}>')
        return "\n".join(lines) + "\n"

    def _render_template_instance_xml(self, node: Node, tpl_def: Template, depth: int, position: int) -> str:
        """Use the template's Jinja render_template but strip HTML tags to get text, then wrap in AKN."""
        try:
            ctx = {**node.data}
            ctx["children"] = [self._render_akn_node(c, depth + 1, i) for i, c in enumerate(node.children, 1)]
            import jinja2
            env = jinja2.Environment()
            rendered = env.from_string(tpl_def.render_template).render(**ctx)
            # Strip HTML tags — keep text only
            text = re.sub(r'<[^>]+>', ' ', rendered).strip()
            text = re.sub(r'\s+', ' ', text)
            if not text and not node.children:
                return ""
            prefix = _slug(node.template_id or "")
            akn_el = _TPL_TO_AKN.get(prefix, "hcontainer")
            return self._render_structural(node, akn_el, depth, position)
        except Exception:
            return self._render_structural(node, "hcontainer", depth, position)

    # ── Utilities ──────────────────────────────────────────────────────────

    def _x(self, text: str) -> str:
        """Escape XML special characters."""
        return (str(text)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))

    def _safe_tag(self, name: str) -> str:
        """Make a string safe for use as an XML element name."""
        tag = re.sub(r"[^a-zA-Z0-9_\-.]", "_", name)
        if tag and tag[0].isdigit():
            tag = "f_" + tag
        return tag or "field"
