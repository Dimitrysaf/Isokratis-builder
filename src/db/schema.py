"""Database schema and initialization."""

import sqlite3


def _apply_pragmas(conn: sqlite3.Connection) -> None:
    """WAL mode + sensible defaults — applied to every connection.

    WAL lets readers and writers coexist so Flask's threaded server never
    gets 'database is locked' from concurrent requests.
    """
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")


def create_schema(db_path: str) -> None:
    """Create or migrate the SQLite schema to the current version."""
    conn = sqlite3.connect(db_path, timeout=30)
    _apply_pragmas(conn)
    c = conn.cursor()

    # ── documents table ────────────────────────────────────────────────────
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

    # Migration: old schema had root_node_id TEXT NOT NULL and metadata TEXT.
    # SQLite cannot ALTER COLUMN, so we rebuild the table if that legacy
    # column is still present with a NOT NULL constraint.
    existing = {row[1]: row for row in c.execute("PRAGMA table_info(documents)")}

    needs_rebuild = (
        "root_node_id" in existing and existing["root_node_id"][3] == 1  # notnull
    )

    if needs_rebuild:
        c.executescript("""
            ALTER TABLE documents RENAME TO _documents_old;

            CREATE TABLE documents (
                doc_id          TEXT PRIMARY KEY,
                title           TEXT NOT NULL,
                instrument_type TEXT NOT NULL DEFAULT 'nomos',
                created_at      TEXT,
                updated_at      TEXT,
                content         TEXT
            );

            INSERT INTO documents (doc_id, title, instrument_type, created_at, updated_at, content)
            SELECT doc_id, title,
                   COALESCE(instrument_type, 'nomos'),
                   created_at, updated_at, content
            FROM   _documents_old;

            DROP TABLE _documents_old;
        """)
    else:
        # Additive migrations only — add columns that may be missing
        for col, defn in [
            ("instrument_type", "TEXT NOT NULL DEFAULT 'nomos'"),
            ("content",         "TEXT"),
        ]:
            if col not in existing:
                c.execute(f"ALTER TABLE documents ADD COLUMN {col} {defn}")

    # ── document_versions table ────────────────────────────────────────────
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
