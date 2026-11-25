"""Money request management."""

import sqlite3
from typing import Any

from agent_ledger.clock import Clock
from agent_ledger.db import transaction
from agent_ledger.errors import TransferError
from agent_ledger.transfers import TransferManager


class RequestManager:
    """Manages money requests between wallets."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock, transfer_manager: TransferManager):
        self.conn = conn
        self.clock = clock
        self.transfer_manager = transfer_manager

    def create_request(
        self, from_wallet: str, to_wallet: str, amount_cents: int, memo: str
    ) -> dict[str, Any]:
        """Create a money request."""
        with transaction(self.conn) as cursor:
            cursor.execute(
                """
                INSERT INTO money_requests (
                    from_wallet, to_wallet, amount_cents, memo, status, created_at
                ) VALUES (?, ?, ?, ?, 'pending', ?)
                """,
                (from_wallet, to_wallet, amount_cents, memo, self.clock.now().isoformat()),
            )
            request_id = cursor.lastrowid

        return self._get_request(request_id)

    def pay_request(self, request_id: int, idempotency_key: str | None = None) -> dict[str, Any]:
        """Pay a money request (creates a transfer)."""
        request = self._get_request(request_id)
        
        if request["status"] != "pending":
            raise TransferError("invalid_status", f"Request status is {request['status']}")

        # Create transfer from to_wallet to from_wallet
        try:
            transfer = self.transfer_manager.create_transfer(
                request["to_wallet"],
                request["from_wallet"],
                request["amount_cents"],
                f"Payment for request #{request_id}: {request['memo']}",
            )
            
            # If transfer completed, update request
            if transfer["status"] == "completed":
                with transaction(self.conn) as cursor:
                    cursor.execute(
                        """
                        UPDATE money_requests
                        SET status = 'paid', transfer_id = ?, resolved_at = ?
                        WHERE id = ?
                        """,
                        (transfer["id"], self.clock.now().isoformat(), request_id),
                    )
                
                return self._get_request(request_id)
            else:
                # Return the transfer response (pending or rejected)
                return transfer
                
        except Exception as e:
            raise

    def decline_request(self, request_id: int) -> dict[str, Any]:
        """Decline a money request."""
        request = self._get_request(request_id)
        
        if request["status"] != "pending":
            raise TransferError("invalid_status", f"Request status is {request['status']}")

        with transaction(self.conn) as cursor:
            cursor.execute(
                """
                UPDATE money_requests
                SET status = 'declined', resolved_at = ?
                WHERE id = ?
                """,
                (self.clock.now().isoformat(), request_id),
            )

        return self._get_request(request_id)

    def cancel_request(self, request_id: int) -> dict[str, Any]:
        """Cancel a money request."""
        request = self._get_request(request_id)
        
        if request["status"] != "pending":
            raise TransferError("invalid_status", f"Request status is {request['status']}")

        with transaction(self.conn) as cursor:
            cursor.execute(
                """
                UPDATE money_requests
                SET status = 'cancelled', resolved_at = ?
                WHERE id = ?
                """,
                (self.clock.now().isoformat(), request_id),
            )

        return self._get_request(request_id)

    def _get_request(self, request_id: int) -> dict[str, Any]:
        """Get request details."""
        cursor = self.conn.cursor()
        row = cursor.execute(
            """
            SELECT id, from_wallet, to_wallet, amount_cents, memo, status, created_at, resolved_at
            FROM money_requests
            WHERE id = ?
            """,
            (request_id,),
        ).fetchone()

        if not row:
            raise TransferError("request_not_found", "Request not found")

        return {
            "id": row[0],
            "from_wallet": row[1],
            "to_wallet": row[2],
            "to": row[2],  # Include both for compatibility
            "amount_cents": row[3],
            "memo": row[4],
            "status": row[5],
            "created_at": row[6],
            "resolved_at": row[7],
        }

    def get_request(self, request_id: int) -> dict[str, Any]:
        """Get request details."""
        return self._get_request(request_id)
