"""LaTeX renderer for documents."""

from typing import Dict
from ..models import Document, Template
from .base import BaseRenderer


class LaTeXRenderer(BaseRenderer):
    """Render documents to LaTeX."""

    def render(self, doc: Document) -> str:
        """Render document to LaTeX."""
        content = self.render_node(doc.root)

        latex = f"""\\documentclass{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[margin=1in]{{geometry}}

\\title{{{self._escape_latex(doc.title)}}}
\\author{{}}
\\date{{}}

\\begin{{document}}

\\maketitle

{content}

\\end{{document}}
"""
        return latex

    def _render_node_by_type(self, node, context) -> str:
        """Override to render LaTeX-specific nodes."""
        node_type = node.node_type

        if node_type == "paragraph":
            content = self._escape_latex(node.data.get('content', ''))
            return f"{content}\n\n"
        elif node_type == "header":
            level = node.data.get('level', 1)
            # LaTeX levels: 1=section, 2=subsection, 3=subsubsection
            commands = {1: "section", 2: "subsection", 3: "subsubsection"}
            cmd = commands.get(level, "section")
            title = self._escape_latex(node.data.get('content', ''))
            return f"\\{cmd}{{{title}}}\n\n"
        else:
            return ""

    def _escape_latex(self, text: str) -> str:
        """Escape LaTeX special characters."""
        replacements = {
            '\\': '\\textbackslash{}',
            '{': '\\{',
            '}': '\\}',
            '$': '\\$',
            '&': '\\&',
            '%': '\\%',
            '#': '\\#',
            '_': '\\_',
            '~': '\\textasciitilde{}',
            '^': '\\textasciicircum{}',
        }
        for char, escaped in replacements.items():
            text = text.replace(char, escaped)
        return text
