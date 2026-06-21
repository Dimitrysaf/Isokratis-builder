"""Database schema and initialization."""

import sqlite3
from pathlib import Path


def create_schema(db_path: str) -> None:
    """Create the SQLite schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            doc_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            root_node_id TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT,
            metadata TEXT,
            FOREIGN KEY (root_node_id) REFERENCES nodes(node_id)
        )
    """)

    # Nodes table (AST storage)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            node_id TEXT PRIMARY KEY,
            parent_node_id TEXT,
            node_type TEXT NOT NULL,
            template_id TEXT,
            data TEXT,
            metadata TEXT,
            position INTEGER,
            FOREIGN KEY (parent_node_id) REFERENCES nodes(node_id),
            FOREIGN KEY (template_id) REFERENCES templates(template_id)
        )
    """)

    # Templates table (definitions)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS templates (
            template_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            fields TEXT,
            child_slots TEXT,
            render_template TEXT,
            metadata TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    # References table (cross-refs)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_references (
            reference_id TEXT PRIMARY KEY,
            source_node_id TEXT NOT NULL,
            target_node_id TEXT NOT NULL,
            reference_type TEXT,
            display_text TEXT,
            FOREIGN KEY (source_node_id) REFERENCES nodes(node_id),
            FOREIGN KEY (target_node_id) REFERENCES nodes(node_id)
        )
    """)

    # Full-text search on node content
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
            node_id,
            content,
            metadata
        )
    """)

    # Document version snapshots (for history / restore)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_versions (
            version_id TEXT PRIMARY KEY,
            doc_id TEXT NOT NULL,
            version_number INTEGER NOT NULL,
            snapshot TEXT NOT NULL,
            created_at TEXT,
            note TEXT,
            FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
        )
    """)

    conn.commit()
    conn.close()


def get_connection(db_path: str) -> sqlite3.Connection:
    """Get a database connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
