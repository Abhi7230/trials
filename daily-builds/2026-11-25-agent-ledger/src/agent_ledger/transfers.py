"""Transfer management."""

import sqlite3
from datetime import datetime, timedelta
from typing import Any

from agent_ledger.approvals import ApprovalManager
from agent_ledger.clock import Clock
from agent_ledger.db import transaction
from agent_ledger.errors import InsufficientFundsError, PolicyRejectionError, TransferError
from agent_ledger.ledger import Ledger
from agent_ledger.policy import PolicyEngine


class TransferManager:
    """Manages money transfers between wallets."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        ledger: Ledger,
        policy: PolicyEngine,
        approvals: ApprovalManager,
        clock: Clock,
    ):
        self.conn = conn
        self.ledger = ledger
        self.policy = policy
        self.approvals = approvals
        self.clock = clock

    def create_transfer(
        self, from_wallet: str, to_wallet: str, amount_cents: int, memo: str
    ) -> dict[str, Any]:
        """Create a transfer (may be pending or completed)."""
        # Get wallet currencies
        from_w = self.ledger.get_wallet(from_wallet)
        to_w = self.ledger.get_wallet(to_wallet)

        if not from_w:
            raise TransferError("wallet_not_found", f"From wallet {from_wallet} not found")
        if not to_w:
            raise TransferError("wallet_not_found", f"To wallet {to_wallet} not found")

        # Check currency match
        if from_w["currency"] != to_w["currency"]:
            raise PolicyRejectionError("currency_mismatch", "Currency mismatch")

        # Evaluate policy
        decision = self.policy.evaluate_transfer(
            from_wallet, to_wallet, amount_cents, from_w["currency"], to_w["currency"]
        )

        if decision.decision == "rejected":
            # Store rejected transfer
            with transaction(self.conn) as cursor:
                cursor.execute(
                    """
                    INSERT INTO transfers (
                        from_wallet, to_wallet, amount_cents, memo, status, reason,
                        policy_version, created_at
                    ) VALUES (?, ?, ?, ?, 'rejected', ?, ?, ?)
                    """,
                    (
                        from_wallet,
                        to_wallet,
                        amount_cents,
                        memo,
                        decision.reason,
                        decision.policy_version,
                        self.clock.now().isoformat(),
                    ),
                )
                transfer_id = cursor.lastrowid

            raise PolicyRejectionError(decision.reason, f"Transfer {transfer_id} rejected")

        elif decision.decision == "completed":
            # Check balance and daily cap before completing
            ok, reason = self.policy.check_balance_and_daily_cap(from_wallet, amount_cents)
            if not ok:
                # Store rejected transfer
                with transaction(self.conn) as cursor:
                    cursor.execute(
                        """
                        INSERT INTO transfers (
                            from_wallet, to_wallet, amount_cents, memo, status, reason,
                            policy_version, created_at
                        ) VALUES (?, ?, ?, ?, 'rejected', ?, ?, ?)
                        """,
                        (
                            from_wallet,
                            to_wallet,
                            amount_cents,
                            memo,
                            reason,
                            decision.policy_version,
                            self.clock.now().isoformat(),
                        ),
                    )
                    transfer_id = cursor.lastrowid

                raise PolicyRejectionError(reason, f"Transfer {transfer_id} rejected")

            # Complete transfer
            return self._complete_transfer(
                from_wallet, to_wallet, amount_cents, memo, decision.policy_version
            )

        else:  # pending_approval
            # Create pending transfer
            with transaction(self.conn) as cursor:
                cursor.execute(
                    """
                    INSERT INTO transfers (
                        from_wallet, to_wallet, amount_cents, memo, status,
                        policy_version, created_at
                    ) VALUES (?, ?, ?, ?, 'pending_approval', ?, ?)
                    """,
                    (
                        from_wallet,
                        to_wallet,
                        amount_cents,
                        memo,
                        decision.policy_version,
                        self.clock.now().isoformat(),
                    ),
                )
                transfer_id = cursor.lastrowid

            # Generate approval token
            token = self.approvals.generate_token(transfer_id, from_wallet, to_wallet, amount_cents)

            return self._get_transfer(transfer_id, approval_token=token)

    def _complete_transfer(
        self, from_wallet: str, to_wallet: str, amount_cents: int, memo: str, policy_version: int
    ) -> dict[str, Any]:
        """Complete a transfer immediately."""
        now = self.clock.now()

        # Create journal entry
        entry_id = self.ledger.create_journal_entry(
            "transfer",
            [(from_wallet, -amount_cents), (to_wallet, amount_cents)],
            now,
        )

        # Store transfer
        with transaction(self.conn, immediate=False) as cursor:
            cursor.execute(
                """
                INSERT INTO transfers (
                    from_wallet, to_wallet, amount_cents, memo, status,
                    policy_version, entry_id, created_at, completed_at
                ) VALUES (?, ?, ?, ?, 'completed', ?, ?, ?, ?)
                """,
                (
                    from_wallet,
                    to_wallet,
                    amount_cents,
                    memo,
                    policy_version,
                    entry_id,
                    now.isoformat(),
                    now.isoformat(),
                ),
            )
            transfer_id = cursor.lastrowid

        return self._get_transfer(transfer_id)

    def approve_transfer(self, transfer_id: int, token: str) -> dict[str, Any]:
        """Approve a pending transfer."""
        # Validate token
        self.approvals.validate_token(transfer_id, token)
        self.approvals.verify_token_for_transfer(transfer_id, token)

        # Get transfer
        transfer = self.approvals.get_transfer(transfer_id)
        if not transfer:
            raise TransferError("transfer_not_found", "Transfer not found")

        if transfer["status"] != "pending_approval":
            raise TransferError("invalid_status", f"Transfer status is {transfer['status']}")

        # Re-check balance and daily cap at approval time
        ok, reason = self.policy.check_balance_and_daily_cap(
            transfer["from_wallet"], transfer["amount_cents"]
        )
        if not ok:
            # Mark as rejected
            with transaction(self.conn) as cursor:
                cursor.execute(
                    "UPDATE transfers SET status = 'completed', reason = ? WHERE id = ?",
                    (reason, transfer_id),
                )
            
            self.approvals.mark_used(transfer_id)
            raise PolicyRejectionError(reason, f"Transfer {transfer_id} rejected at approval")

        # Complete the transfer
        now = self.clock.now()
        entry_id = self.ledger.create_journal_entry(
            "transfer",
            [(transfer["from_wallet"], -transfer["amount_cents"]), (transfer["to_wallet"], transfer["amount_cents"])],
            now,
        )

        with transaction(self.conn, immediate=False) as cursor:
            cursor.execute(
                """
                UPDATE transfers
                SET status = 'completed', entry_id = ?, completed_at = ?
                WHERE id = ?
                """,
                (entry_id, now.isoformat(), transfer_id),
            )

        self.approvals.mark_used(transfer_id)
        return self._get_transfer(transfer_id)

    def deny_transfer(self, transfer_id: int) -> dict[str, Any]:
        """Deny a pending transfer."""
        transfer = self.approvals.get_transfer(transfer_id)
        if not transfer:
            raise TransferError("transfer_not_found", "Transfer not found")

        if transfer["status"] != "pending_approval":
            raise TransferError("invalid_status", f"Transfer status is {transfer['status']}")

        with transaction(self.conn) as cursor:
            cursor.execute(
                "UPDATE transfers SET status = 'denied' WHERE id = ?",
                (transfer_id,),
            )

        return self._get_transfer(transfer_id)

    def reverse_transfer(self, transfer_id: int) -> dict[str, Any]:
        """Reverse a completed transfer."""
        cursor = self.conn.cursor()
        row = cursor.execute(
            """
            SELECT from_wallet, to_wallet, amount_cents, status, completed_at, reversed, entry_id
            FROM transfers
            WHERE id = ?
            """,
            (transfer_id,),
        ).fetchone()

        if not row:
            raise TransferError("transfer_not_found", "Transfer not found")

        from_wallet, to_wallet, amount, status, completed_at_str, reversed_flag, entry_id = row

        if status != "completed":
            raise TransferError("invalid_status", "Transfer not completed")

        if reversed_flag:
            raise TransferError("already_reversed", "Transfer already reversed")

        # Check if any partial refunds exist
        refund_count = cursor.execute(
            "SELECT COUNT(*) FROM refunds WHERE transfer_id = ?", (transfer_id,)
        ).fetchone()[0]

        if refund_count > 0:
            raise TransferError("partially_refunded", "Cannot reverse partially refunded transfer")

        # Check reversal window (72 hours)
        completed_at = datetime.fromisoformat(completed_at_str)
        if self.clock.now() - completed_at > timedelta(hours=72):
            raise TransferError("reversal_window_closed", "Reversal window closed")

        # Check if payee has funds
        balance = self.ledger.get_balance(to_wallet)
        if balance < amount:
            raise InsufficientFundsError(f"Payee {to_wallet} has insufficient funds for reversal")

        # Create reversal entry
        now = self.clock.now()
        reversal_entry_id = self.ledger.create_journal_entry(
            "reversal",
            [(to_wallet, -amount), (from_wallet, amount)],
            now,
        )

        with transaction(self.conn, immediate=False) as cursor:
            cursor.execute(
                "UPDATE transfers SET reversed = 1 WHERE id = ?",
                (transfer_id,),
            )

        return {"reversal_entry_id": reversal_entry_id, "original_transfer_id": transfer_id}

    def _get_transfer(self, transfer_id: int, approval_token: str | None = None) -> dict[str, Any]:
        """Get transfer details."""
        cursor = self.conn.cursor()
        row = cursor.execute(
            """
            SELECT id, from_wallet, to_wallet, amount_cents, memo, status, reason,
                   policy_version, created_at, completed_at
            FROM transfers
            WHERE id = ?
            """,
            (transfer_id,),
        ).fetchone()

        if not row:
            raise TransferError("transfer_not_found", "Transfer not found")

        result = {
            "id": row[0],
            "from_wallet": row[1],
            "to": row[2],
            "amount_cents": row[3],
            "memo": row[4],
            "status": row[5],
            "reason": row[6],
            "policy_version": row[7],
            "created_at": row[8],
            "completed_at": row[9],
        }

        if approval_token:
            result["approval_token"] = approval_token

        return result

    def get_transfer(self, transfer_id: int) -> dict[str, Any]:
        """Get transfer details."""
        return self._get_transfer(transfer_id)
