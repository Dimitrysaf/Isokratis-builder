"""Database schema and initialization."""

import sqlite3


def _apply_pragmas(conn: sqlite3.Connection) -> None:
    """Apply performance/concurrency pragmas.

    WAL mode lets readers and writers coexist without locking each other out,
    which prevents 'database is locked' under Flask's debug reloader (two
    processes) and under concurrent AJAX saves.
    """
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")   # safe with WAL, faster
    conn.execute("PRAGMA foreign_keys=ON")


def create_schema(db_path: str) -> None:
    """Create / migrate the SQLite schema."""
    conn = sqlite3.connect(db_path, timeout=30)
    _apply_pragmas(conn)
    c = conn.cursor()

    # Documents table — stores AKN JSON blob in `content`
    c.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            doc_id          TEXT PRIMARY KEY,
            title           TEXT NOT NULL,
            instrument_type TEXT NOT NULL DEFAULT 'nomos',
            created_at      TEXT,
            updated_at      TEXT,
            content         TEXT
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
    """Open a connection with WAL mode and a 30-second busy timeout."""
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    _apply_pragmas(conn)
    return conn
