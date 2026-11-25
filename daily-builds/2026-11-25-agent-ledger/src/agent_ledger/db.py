"""Database schema and operations."""

import sqlite3
from contextlib import contextmanager
from typing import Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS wallets (
    id TEXT PRIMARY KEY,
    balance INTEGER NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'USD',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS policies (
    wallet_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    per_tx_cap_cents INTEGER NOT NULL,
    daily_cap_cents INTEGER NOT NULL,
    auto_approve_limit_cents INTEGER NOT NULL,
    trusted_contacts TEXT NOT NULL,
    blocked_contacts TEXT NOT NULL,
    timezone TEXT NOT NULL DEFAULT 'UTC',
    created_at TEXT NOT NULL,
    PRIMARY KEY (wallet_id, version),
    FOREIGN KEY (wallet_id) REFERENCES wallets(id)
);

CREATE TABLE IF NOT EXISTS journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS postings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL,
    account TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    FOREIGN KEY (entry_id) REFERENCES journal_entries(id)
);

CREATE INDEX IF NOT EXISTS idx_postings_account ON postings(account);
CREATE INDEX IF NOT EXISTS idx_postings_entry ON postings(entry_id);

CREATE TABLE IF NOT EXISTS transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_wallet TEXT NOT NULL,
    to_wallet TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    memo TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL,
    reason TEXT,
    policy_version INTEGER NOT NULL,
    entry_id INTEGER,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    reversed BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (entry_id) REFERENCES journal_entries(id),
    FOREIGN KEY (from_wallet) REFERENCES wallets(id)
);

CREATE INDEX IF NOT EXISTS idx_transfers_from ON transfers(from_wallet);
CREATE INDEX IF NOT EXISTS idx_transfers_status ON transfers(status);

CREATE TABLE IF NOT EXISTS approval_tokens (
    transfer_id INTEGER PRIMARY KEY,
    token_hash TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used_at TEXT,
    FOREIGN KEY (transfer_id) REFERENCES transfers(id)
);

CREATE TABLE IF NOT EXISTS refunds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transfer_id INTEGER NOT NULL,
    amount_cents INTEGER NOT NULL,
    entry_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (transfer_id) REFERENCES transfers(id),
    FOREIGN KEY (entry_id) REFERENCES journal_entries(id)
);

CREATE TABLE IF NOT EXISTS money_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_wallet TEXT NOT NULL,
    to_wallet TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    memo TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL,
    transfer_id INTEGER,
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    FOREIGN KEY (from_wallet) REFERENCES wallets(id),
    FOREIGN KEY (transfer_id) REFERENCES transfers(id)
);

CREATE TABLE IF NOT EXISTS idempotency_keys (
    key_hash TEXT NOT NULL,
    wallet_id TEXT NOT NULL,
    method TEXT NOT NULL,
    path TEXT NOT NULL,
    body_hash TEXT NOT NULL,
    response_status INTEGER NOT NULL,
    response_body TEXT NOT NULL,
    in_progress BOOLEAN NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    PRIMARY KEY (key_hash, wallet_id, method, path)
);

CREATE INDEX IF NOT EXISTS idx_idempotency_created ON idempotency_keys(created_at);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    wallet TEXT,
    actor TEXT,
    endpoint TEXT NOT NULL,
    decision TEXT NOT NULL,
    reason TEXT,
    policy_version INTEGER,
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_wallet ON audit_log(wallet);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
"""


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize database schema."""
    conn.executescript(SCHEMA)
    conn.commit()


@contextmanager
def transaction(conn: sqlite3.Connection, immediate: bool = True) -> Iterator[sqlite3.Cursor]:
    """Context manager for database transactions with BEGIN IMMEDIATE."""
    cursor = conn.cursor()
    try:
        if immediate:
            cursor.execute("BEGIN IMMEDIATE")
        else:
            cursor.execute("BEGIN")
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def get_connection(db_path: str) -> sqlite3.Connection:
    """Create a database connection."""
    conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn
