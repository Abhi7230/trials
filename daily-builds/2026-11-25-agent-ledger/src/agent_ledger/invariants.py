"""Ledger invariant checker."""

import sqlite3
from typing import Any


class InvariantChecker:
    """Checks ledger invariants."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def check_all(self) -> dict[str, Any]:
        """Check all invariants."""
        violations = []

        # Check 1: Every journal entry sums to 0
        cursor = self.conn.cursor()
        unbalanced = cursor.execute(
            """
            SELECT entry_id, SUM(amount_cents) as total
            FROM postings
            GROUP BY entry_id
            HAVING total != 0
            """
        ).fetchall()

        for entry_id, total in unbalanced:
            violations.append({
                "type": "unbalanced_entry",
                "description": f"Journal entry {entry_id} does not sum to zero",
                "details": {"entry_id": entry_id, "sum": total},
            })

        # Check 2: Sum of all postings is 0
        total_sum = cursor.execute(
            "SELECT COALESCE(SUM(amount_cents), 0) FROM postings"
        ).fetchone()[0]

        if total_sum != 0:
            violations.append({
                "type": "total_imbalance",
                "description": "Sum of all postings is not zero",
                "details": {"sum": total_sum},
            })

        # Check 3: Cached balance equals sum of postings for each wallet
        wallets = cursor.execute("SELECT id, balance FROM wallets").fetchall()
        
        for wallet_id, cached_balance in wallets:
            posting_sum = cursor.execute(
                "SELECT COALESCE(SUM(amount_cents), 0) FROM postings WHERE account = ?",
                (wallet_id,),
            ).fetchone()[0]

            if cached_balance != posting_sum:
                violations.append({
                    "type": "balance_mismatch",
                    "description": f"Cached balance does not match postings sum for {wallet_id}",
                    "details": {
                        "wallet": wallet_id,
                        "cached": cached_balance,
                        "actual": posting_sum,
                    },
                })

        # Check 4: No wallet has negative balance
        negative_wallets = cursor.execute(
            "SELECT id, balance FROM wallets WHERE balance < 0"
        ).fetchall()

        for wallet_id, balance in negative_wallets:
            violations.append({
                "type": "negative_balance",
                "description": f"Wallet {wallet_id} has negative balance",
                "details": {"wallet": wallet_id, "balance": balance},
            })

        # Check 5: Refunds never exceed transfer amount
        excessive_refunds = cursor.execute(
            """
            SELECT t.id, t.amount_cents, SUM(r.amount_cents) as total_refunded
            FROM transfers t
            JOIN refunds r ON r.transfer_id = t.id
            GROUP BY t.id, t.amount_cents
            HAVING total_refunded > t.amount_cents
            """
        ).fetchall()

        for transfer_id, original, total_refunded in excessive_refunds:
            violations.append({
                "type": "excessive_refund",
                "description": f"Transfer {transfer_id} has excessive refunds",
                "details": {
                    "transfer_id": transfer_id,
                    "original_amount": original,
                    "total_refunded": total_refunded,
                },
            })

        return {
            "ok": len(violations) == 0,
            "violations": violations,
        }
