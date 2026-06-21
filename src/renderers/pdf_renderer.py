"""PDF renderer for documents."""

from typing import Dict, Optional
from ..models import Document, Template
from .html_renderer import HTMLRenderer


class PDFRenderer(HTMLRenderer):
    """
    Render documents to PDF.
    Uses wkhtmltopdf or weasyprint (pure Python).
    """

    def __init__(self, templates: Dict[str, Template], use_weasyprint: bool = True):
        super().__init__(templates)
        self.use_weasyprint = use_weasyprint

    def render(self, doc: Document) -> bytes:
        """
        Render document to PDF (returns bytes).
        Requires wkhtmltopdf or weasyprint to be installed.
        """
        html_content = super().render(doc)

        if self.use_weasyprint:
            return self._render_with_weasyprint(html_content)
        else:
            return self._render_with_wkhtmltopdf(html_content)

    def _render_with_weasyprint(self, html: str) -> bytes:
        """Render using WeasyPrint (pure Python)."""
        try:
            import weasyprint
            doc = weasyprint.HTML(string=html)
            return doc.write_pdf()
        except ImportError:
            raise ImportError("WeasyPrint is required. Install with: pip install weasyprint")

    def _render_with_wkhtmltopdf(self, html: str) -> bytes:
        """Render using wkhtmltopdf."""
        try:
            import pdfkit
            options = {
                'quiet': '',
                'enable-local-file-access': '',
            }
            return pdfkit.from_string(html, False, options=options)
        except ImportError:
            raise ImportError("pdfkit is required. Install with: pip install pdfkit")
        except OSError:
            raise OSError("wkhtmltopdf is not installed. Install it system-wide.")
