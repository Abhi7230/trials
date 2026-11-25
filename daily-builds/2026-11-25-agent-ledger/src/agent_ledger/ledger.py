"""Double-entry ledger implementation."""

import sqlite3
from datetime import datetime
from typing import Any

from agent_ledger.db import transaction
from agent_ledger.errors import InsufficientFundsError


class Ledger:
    """Double-entry ledger manager."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create_wallet(self, wallet_id: str, currency: str, created_at: datetime) -> None:
        """Create a new wallet."""
        with transaction(self.conn) as cursor:
            cursor.execute(
                "INSERT INTO wallets (id, balance, currency, created_at) VALUES (?, 0, ?, ?)",
                (wallet_id, currency, created_at.isoformat()),
            )

    def get_wallet(self, wallet_id: str) -> dict[str, Any] | None:
        """Get wallet details."""
        cursor = self.conn.cursor()
        row = cursor.execute(
            "SELECT id, balance, currency, created_at FROM wallets WHERE id = ?",
            (wallet_id,),
        ).fetchone()
        if row:
            return dict(row)
        return None

    def create_journal_entry(
        self, entry_type: str, postings: list[tuple[str, int]], created_at: datetime
    ) -> int:
        """Create a journal entry with postings. Returns entry_id."""
        total = sum(amount for _, amount in postings)
        if total != 0:
            raise ValueError(f"Journal entry must sum to zero, got {total}")

        with transaction(self.conn) as cursor:
            cursor.execute(
                "INSERT INTO journal_entries (type, created_at) VALUES (?, ?)",
                (entry_type, created_at.isoformat()),
            )
            entry_id = cursor.lastrowid

            for account, amount in postings:
                cursor.execute(
                    "INSERT INTO postings (entry_id, account, amount_cents) VALUES (?, ?, ?)",
                    (entry_id, account, amount),
                )

                # Update wallet balance if it's a wallet (not a system account)
                if not account.startswith("external:"):
                    cursor.execute(
                        "UPDATE wallets SET balance = balance + ? WHERE id = ?",
                        (amount, account),
                    )

                    # Check for negative balance on wallets
                    new_balance = cursor.execute(
                        "SELECT balance FROM wallets WHERE id = ?", (account,)
                    ).fetchone()
                    if new_balance and new_balance[0] < 0:
                        raise InsufficientFundsError(f"Wallet {account} would have negative balance")

        return entry_id

    def get_balance(self, account: str) -> int:
        """Get account balance."""
        cursor = self.conn.cursor()
        
        # For wallets, use the cached balance
        if not account.startswith("external:"):
            row = cursor.execute("SELECT balance FROM wallets WHERE id = ?", (account,)).fetchone()
            if row:
                return row[0]
            return 0
        
        # For system accounts, sum postings
        row = cursor.execute(
            "SELECT COALESCE(SUM(amount_cents), 0) FROM postings WHERE account = ?",
            (account,),
        ).fetchone()
        return row[0] if row else 0

    def get_postings_sum(self, account: str) -> int:
        """Get the sum of all postings for an account (for invariant checking)."""
        cursor = self.conn.cursor()
        row = cursor.execute(
            "SELECT COALESCE(SUM(amount_cents), 0) FROM postings WHERE account = ?",
            (account,),
        ).fetchone()
        return row[0] if row else 0

    def list_transactions(self, wallet_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """List recent transactions for a wallet."""
        cursor = self.conn.cursor()
        rows = cursor.execute(
            """
            SELECT 
                t.id, t.from_wallet, t.to_wallet, t.amount_cents, t.memo, 
                t.status, t.created_at, t.completed_at
            FROM transfers t
            WHERE t.from_wallet = ? OR t.to_wallet = ?
            ORDER BY t.created_at DESC
            LIMIT ?
            """,
            (wallet_id, wallet_id, limit),
        ).fetchall()
        
        return [dict(row) for row in rows]
