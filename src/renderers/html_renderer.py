"""HTML renderer for documents."""

from typing import Dict
from ..models import Document, Template
from .base import BaseRenderer


class HTMLRenderer(BaseRenderer):
    """Render documents to HTML."""

    def render(self, doc: Document) -> str:
        """Render document to HTML."""
        html_content = self.render_node(doc.root)

        # Wrap in basic HTML document
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{self._escape_html(doc.title)}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #333;
        }}
        p {{
            margin: 10px 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 10px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
    </style>
</head>
<body>
    <h1>{self._escape_html(doc.title)}</h1>
    {html_content}
</body>
</html>"""
        return html
