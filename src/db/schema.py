"""Database schema and initialization."""

import sqlite3


def create_schema(db_path: str) -> None:
    """Create / migrate the SQLite schema."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Documents table — stores AKN JSON blob in `content`
    c.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            doc_id      TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            instrument_type TEXT NOT NULL DEFAULT 'nomos',
            created_at  TEXT,
            updated_at  TEXT,
            content     TEXT
        )
    """)

    # Migration: add columns that may not exist in older DB versions
    existing_cols = {row[1] for row in c.execute("PRAGMA table_info(documents)")}
    for col, defn in [
        ("instrument_type", "TEXT NOT NULL DEFAULT 'nomos'"),
        ("content", "TEXT"),
    ]:
        if col not in existing_cols:
            c.execute(f"ALTER TABLE documents ADD COLUMN {col} {defn}")

    # Document version snapshots
    c.execute("""
        CREATE TABLE IF NOT EXISTS document_versions (
            version_id     TEXT PRIMARY KEY,
            doc_id         TEXT NOT NULL,
            version_number INTEGER NOT NULL,
            snapshot       TEXT NOT NULL,
            created_at     TEXT,
            note           TEXT,
            FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
        )
    """)

    conn.commit()
    conn.close()


def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
