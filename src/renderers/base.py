"""Base renderer class and utilities."""

from abc import ABC, abstractmethod
from typing import Dict, Any
import jinja2

from ..models import Document, Node, Template


class BaseRenderer(ABC):
    """Abstract base class for document renderers."""

    def __init__(self, templates: Dict[str, Template]):
        """
        Initialize renderer with loaded templates.
        templates: dict of template_id -> Template
        """
        self.templates = templates
        self.jinja_env = jinja2.Environment()

    @abstractmethod
    def render(self, doc: Document) -> str:
        """Render document to output format. Return a string."""
        pass

    def render_node(self, node: Node, context: Dict[str, Any] = None) -> str:
        """Render a single node."""
        if context is None:
            context = {}

        # If node is a template instance, use template renderer
        if node.template_id and node.template_id in self.templates:
            template_def = self.templates[node.template_id]
            return self._render_template_instance(node, template_def, context)

        # Otherwise, render based on node type
        return self._render_node_by_type(node, context)

    def _render_template_instance(self, node: Node, template_def: Template, context: Dict[str, Any]) -> str:
        """Render a template instance node using the template definition."""
        # Merge node data (form values) into context
        render_context = {**context, **node.data}

        # Add children as a list for the render template
        render_context["children"] = [self.render_node(child, render_context) for child in node.children]

        # Render the template's Jinja2 template string
        try:
            template = self.jinja_env.from_string(template_def.render_template)
            return template.render(**render_context)
        except Exception as e:
            return f"<!-- Error rendering template {template_def.name}: {e} -->"

    def _render_node_by_type(self, node: Node, context: Dict[str, Any]) -> str:
        """Default node rendering by type."""
        node_type = node.node_type

        if node_type == "paragraph":
            return f"<p>{node.data.get('content', '')}</p>"
        elif node_type == "header":
            level = node.data.get('level', 1)
            return f"<h{level}>{node.data.get('content', '')}</h{level}>"
        elif node_type == "text":
            return node.data.get('content', '')
        else:
            return f"<!-- Unhandled node type: {node_type} -->"

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#x27;"))
