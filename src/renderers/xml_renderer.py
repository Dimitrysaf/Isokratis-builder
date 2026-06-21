"""Legal XML renderer for structured legal documents."""

from typing import Dict
from ..models import Document, Template, Node
from .base import BaseRenderer


class LegalXMLRenderer(BaseRenderer):
    """Render documents to custom legal XML structure."""

    def render(self, doc: Document) -> str:
        """Render document to legal XML."""
        content = self.render_node(doc.root)

        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<νόμος>
    <μεταδεδομένα>
        <τίτλος>{self._escape_xml(doc.title)}</τίτλος>
        <ημερομηνία_δημιουργίας>{doc.metadata.get('created_at', '')}</ημερομηνία_δημιουργίας>
    </μεταδεδομένα>
    <περιεχόμενο>
{content}
    </περιεχόμενο>
</νόμος>"""
        return xml

    def _render_node_by_type(self, node: Node, context: Dict) -> str:
        """Render LaTeX-specific nodes."""
        node_type = node.node_type

        if node_type == "paragraph":
            content = self._escape_xml(node.data.get('content', ''))
            num = node.data.get('number', '')
            return f"        <παράγραφος αριθμός=\"{num}\">{content}</παράγραφος>\n"
        elif node_type == "header":
            content = self._escape_xml(node.data.get('content', ''))
            return f"        <κεφάλαιο>{content}</κεφάλαιο>\n"
        else:
            return ""

    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))
