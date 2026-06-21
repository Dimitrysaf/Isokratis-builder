"""Persistence layer for documents, nodes, templates."""

import json
import sqlite3
from typing import Optional, List, Dict, Any
from pathlib import Path

from ..models import Document, Node, Template, Reference
from .schema import get_connection


class DocumentRepository:
    """Save and load documents from SQLite."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def save_document(self, doc: Document) -> None:
        """Save a document and its AST to the database."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        # Save document metadata
        cursor.execute("""
            INSERT OR REPLACE INTO documents
            (doc_id, title, root_node_id, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            doc.doc_id,
            doc.title,
            doc.root.node_id,
            doc.metadata.get("created_at"),
            doc.metadata.get("updated_at"),
            json.dumps(doc.metadata),
        ))

        # Save all nodes recursively
        self._save_nodes_recursive(cursor, doc.root, None)

        conn.commit()
        conn.close()

    def _save_nodes_recursive(self, cursor: sqlite3.Cursor, node: Node, parent_id: Optional[str], position: int = 0) -> None:
        """Recursively save nodes."""
        cursor.execute("""
            INSERT OR REPLACE INTO nodes
            (node_id, parent_node_id, node_type, template_id, data, metadata, position)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            node.node_id,
            parent_id,
            node.node_type,
            node.template_id,
            json.dumps(node.data),
            json.dumps(node.metadata),
            position,
        ))

        for idx, child in enumerate(node.children):
            self._save_nodes_recursive(cursor, child, node.node_id, idx)

    def load_document(self, doc_id: str) -> Optional[Document]:
        """Load a document and its AST from the database."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        root_node_id = row["root_node_id"]
        root = self._load_node_recursive(cursor, root_node_id)

        doc = Document(
            doc_id=row["doc_id"],
            title=row["title"],
            root=root,
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )
        conn.close()
        return doc

    def _load_node_recursive(self, cursor: sqlite3.Cursor, node_id: str) -> Node:
        """Recursively load nodes."""
        cursor.execute("SELECT * FROM nodes WHERE node_id = ?", (node_id,))
        row = cursor.fetchone()

        if not row:
            return Node(node_id=node_id)

        # Load children
        cursor.execute("SELECT * FROM nodes WHERE parent_node_id = ? ORDER BY position", (node_id,))
        children_rows = cursor.fetchall()
        children = [self._load_node_recursive(cursor, child_row["node_id"]) for child_row in children_rows]

        node = Node(
            node_id=row["node_id"],
            node_type=row["node_type"],
            template_id=row["template_id"],
            data=json.loads(row["data"]) if row["data"] else {},
            children=children,
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )
        return node

    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents (metadata only)."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT doc_id, title, created_at, updated_at FROM documents ORDER BY updated_at DESC")
        docs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return docs

    def delete_document(self, doc_id: str) -> None:
        """Delete a document and all its nodes."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        # Get root node ID
        cursor.execute("SELECT root_node_id FROM documents WHERE doc_id = ?", (doc_id,))
        row = cursor.fetchone()
        if row:
            root_id = row["root_node_id"]
            self._delete_nodes_recursive(cursor, root_id)

        cursor.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        conn.commit()
        conn.close()

    def _delete_nodes_recursive(self, cursor: sqlite3.Cursor, node_id: str) -> None:
        """Recursively delete nodes."""
        cursor.execute("SELECT node_id FROM nodes WHERE parent_node_id = ?", (node_id,))
        children = cursor.fetchall()
        for child in children:
            self._delete_nodes_recursive(cursor, child["node_id"])
        cursor.execute("DELETE FROM nodes WHERE node_id = ?", (node_id,))


class TemplateRepository:
    """Save and load templates from SQLite."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def save_template(self, template: Template) -> None:
        """Save a template definition."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO templates
            (template_id, name, description, fields, child_slots, render_template, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            template.template_id,
            template.name,
            template.description,
            json.dumps([f.to_dict() for f in template.fields]),
            json.dumps([s.to_dict() for s in template.child_slots]),
            template.render_template,
            json.dumps(template.metadata),
            template.metadata.get("created_at"),
            template.metadata.get("updated_at"),
        ))

        conn.commit()
        conn.close()

    def load_template(self, template_id: str) -> Optional[Template]:
        """Load a template by ID."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM templates WHERE template_id = ?", (template_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        row_dict = dict(row)
        # Parse JSON fields
        if isinstance(row_dict.get("fields"), str):
            row_dict["fields"] = json.loads(row_dict["fields"]) if row_dict["fields"] else []
        if isinstance(row_dict.get("child_slots"), str):
            row_dict["child_slots"] = json.loads(row_dict["child_slots"]) if row_dict["child_slots"] else []
        if isinstance(row_dict.get("metadata"), str):
            row_dict["metadata"] = json.loads(row_dict["metadata"]) if row_dict["metadata"] else {}

        return Template.from_dict(row_dict)

    def load_all_templates(self) -> List[Template]:
        """Load all templates."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM templates ORDER BY name")
        templates = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            # Parse JSON fields
            if isinstance(row_dict.get("fields"), str):
                row_dict["fields"] = json.loads(row_dict["fields"]) if row_dict["fields"] else []
            if isinstance(row_dict.get("child_slots"), str):
                row_dict["child_slots"] = json.loads(row_dict["child_slots"]) if row_dict["child_slots"] else []
            if isinstance(row_dict.get("metadata"), str):
                row_dict["metadata"] = json.loads(row_dict["metadata"]) if row_dict["metadata"] else {}
            templates.append(Template.from_dict(row_dict))
        
        conn.close()
        return templates

    def delete_template(self, template_id: str) -> None:
        """Delete a template."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM templates WHERE template_id = ?", (template_id,))
        conn.commit()
        conn.close()


class ReferenceRepository:
    """Save and load references."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def save_reference(self, ref: Reference) -> None:
        """Save a reference."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO document_references
            (reference_id, source_node_id, target_node_id, reference_type, display_text)
            VALUES (?, ?, ?, ?, ?)
        """, (
            ref.reference_id,
            ref.source_node_id,
            ref.target_node_id,
            ref.reference_type,
            ref.display_text,
        ))

        conn.commit()
        conn.close()

    def get_references_by_source(self, source_node_id: str) -> List[Reference]:
        """Get all references from a source node."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM document_references WHERE source_node_id = ?", (source_node_id,))
        refs = [Reference.from_dict(dict(row)) for row in cursor.fetchall()]
        conn.close()
        return refs

    def get_references_to_target(self, target_node_id: str) -> List[Reference]:
        """Get all references pointing to a target node (backlinks)."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM document_references WHERE target_node_id = ?", (target_node_id,))
        refs = [Reference.from_dict(dict(row)) for row in cursor.fetchall()]
        conn.close()
        return refs
