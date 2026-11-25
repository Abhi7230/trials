"""Refund management."""

import sqlite3
from typing import Any

from agent_ledger.clock import Clock
from agent_ledger.db import transaction
from agent_ledger.errors import TransferError
from agent_ledger.ledger import Ledger


class RefundManager:
    """Manages partial refunds for transfers."""

    def __init__(self, conn: sqlite3.Connection, ledger: Ledger, clock: Clock):
        self.conn = conn
        self.ledger = ledger
        self.clock = clock

    def create_refund(self, transfer_id: int, amount_cents: int) -> dict[str, Any]:
        """Create a partial refund for a transfer."""
        cursor = self.conn.cursor()
        
        # Get transfer details
        row = cursor.execute(
            """
            SELECT from_wallet, to_wallet, amount_cents, status, reversed
            FROM transfers
            WHERE id = ?
            """,
            (transfer_id,),
        ).fetchone()

        if not row:
            raise TransferError("transfer_not_found", "Transfer not found")

        from_wallet, to_wallet, original_amount, status, reversed_flag = row

        if status != "completed":
            raise TransferError("invalid_status", "Transfer not completed")

        if reversed_flag:
            raise TransferError("already_reversed", "Cannot refund reversed transfer")

        # Calculate total refunded so far
        total_refunded = cursor.execute(
            "SELECT COALESCE(SUM(amount_cents), 0) FROM refunds WHERE transfer_id = ?",
            (transfer_id,),
        ).fetchone()[0]

        # Check if already fully refunded
        if total_refunded == original_amount:
            raise TransferError("fully_refunded", "Transfer fully refunded")

        # Check if refund would exceed original amount
        if total_refunded + amount_cents > original_amount:
            remaining = original_amount - total_refunded
            raise TransferError("exceeds_refundable", f"Only {remaining} cents refundable")

        # Create refund journal entry
        now = self.clock.now()
        entry_id = self.ledger.create_journal_entry(
            "refund",
            [(to_wallet, -amount_cents), (from_wallet, amount_cents)],
            now,
        )

        # Store refund
        with transaction(self.conn, immediate=False) as cursor:
            cursor.execute(
                """
                INSERT INTO refunds (transfer_id, amount_cents, entry_id, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (transfer_id, amount_cents, entry_id, now.isoformat()),
            )
            refund_id = cursor.lastrowid

        return {
            "refund_id": refund_id,
            "transfer_id": transfer_id,
            "amount_cents": amount_cents,
            "entry_id": entry_id,
        }

    def get_refunds(self, transfer_id: int) -> list[dict[str, Any]]:
        """Get all refunds for a transfer."""
        cursor = self.conn.cursor()
        rows = cursor.execute(
            """
            SELECT id, transfer_id, amount_cents, entry_id, created_at
            FROM refunds
            WHERE transfer_id = ?
            ORDER BY created_at
            """,
            (transfer_id,),
        ).fetchall()

        return [
            {
                "refund_id": row[0],
                "transfer_id": row[1],
                "amount_cents": row[2],
                "entry_id": row[3],
                "created_at": row[4],
            }
            for row in rows
        ]
