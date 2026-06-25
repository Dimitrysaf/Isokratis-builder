"""Persistence layer — documents and versions."""

import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from ..models import Document
from .schema import get_connection


class DocumentRepository:

    def __init__(self, db_path: str):
        self.db_path = db_path

    def save_document(self, doc: Document) -> None:
        conn = get_connection(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO documents
            (doc_id, title, instrument_type, created_at, updated_at, content)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            doc.doc_id,
            doc.title,
            doc.instrument_type,
            doc.created_at,
            doc.updated_at,
            json.dumps(doc.to_dict()),
        ))
        conn.commit()
        conn.close()

    def load_document(self, doc_id: str) -> Optional[Document]:
        conn = get_connection(self.db_path)
        c = conn.cursor()
        c.execute(
            "SELECT doc_id, title, instrument_type, created_at, updated_at, content "
            "FROM documents WHERE doc_id = ?", (doc_id,)
        )
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        if row["content"]:
            doc = Document.from_dict(json.loads(row["content"]))
            doc.doc_id = doc_id
            return doc
        # Legacy row: content column is NULL — reconstruct a blank document
        doc = Document(
            title=row["title"] or "Χωρίς τίτλο",
            instrument_type=row["instrument_type"] or "nomos",
        )
        doc.doc_id = doc_id
        doc.created_at = row["created_at"] or doc.created_at
        doc.updated_at = row["updated_at"] or doc.updated_at
        return doc

    def list_documents(self) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        c = conn.cursor()
        c.execute("""
            SELECT doc_id, title, instrument_type, created_at, updated_at
            FROM documents ORDER BY updated_at DESC
        """)
        docs = [dict(r) for r in c.fetchall()]
        conn.close()
        return docs

    def delete_document(self, doc_id: str) -> None:
        conn = get_connection(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM document_versions WHERE doc_id = ?", (doc_id,))
        c.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        conn.commit()
        conn.close()


class VersionRepository:

    def __init__(self, db_path: str):
        self.db_path = db_path

    def save_version(self, doc: Document, note: str = "") -> str:
        version_id = str(uuid.uuid4())
        conn = get_connection(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM document_versions WHERE doc_id = ?", (doc.doc_id,))
        row = c.fetchone()
        count = row["cnt"] if row else 0
        c.execute("""
            INSERT INTO document_versions
            (version_id, doc_id, version_number, snapshot, created_at, note)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (version_id, doc.doc_id, count + 1,
              json.dumps(doc.to_dict()), datetime.now().isoformat(), note))
        conn.commit()
        conn.close()
        return version_id

    def list_versions(self, doc_id: str) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        c = conn.cursor()
        c.execute("""
            SELECT version_id, version_number, created_at, note
            FROM document_versions WHERE doc_id = ?
            ORDER BY version_number DESC
        """, (doc_id,))
        versions = [dict(r) for r in c.fetchall()]
        conn.close()
        return versions

    def load_version(self, version_id: str) -> Optional[Document]:
        conn = get_connection(self.db_path)
        c = conn.cursor()
        c.execute("SELECT snapshot FROM document_versions WHERE version_id = ?", (version_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return Document.from_dict(json.loads(row["snapshot"]))
        return None
