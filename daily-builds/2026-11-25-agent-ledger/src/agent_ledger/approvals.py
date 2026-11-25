"""Approval token generation and validation."""

import hashlib
import hmac
import os
import secrets
import sqlite3
from datetime import datetime, timedelta

from agent_ledger.clock import Clock
from agent_ledger.db import transaction
from agent_ledger.errors import ApprovalError


class ApprovalManager:
    """Manages approval tokens for pending transfers."""

    TOKEN_LIFETIME_MINUTES = 15

    def __init__(self, conn: sqlite3.Connection, clock: Clock, secret: bytes | None = None):
        self.conn = conn
        self.clock = clock
        self.secret = secret or self._get_secret()

    def _get_secret(self) -> bytes:
        """Get secret from env or generate random."""
        env_secret = os.environ.get("AGENT_LEDGER_SECRET")
        if env_secret:
            return env_secret.encode("utf-8")
        # Generate random per-process secret
        return secrets.token_bytes(32)

    def generate_token(
        self, transfer_id: int, from_wallet: str, to_wallet: str, amount_cents: int
    ) -> str:
        """Generate approval token for transfer."""
        expires_at = self.clock.now() + timedelta(minutes=self.TOKEN_LIFETIME_MINUTES)
        
        # Create token: HMAC(transfer_id|from|to|amount|expires_at)
        message = f"{transfer_id}|{from_wallet}|{to_wallet}|{amount_cents}|{expires_at.isoformat()}"
        token = hmac.new(self.secret, message.encode("utf-8"), hashlib.sha256).hexdigest()

        # Store token hash
        with transaction(self.conn, immediate=False) as cursor:
            token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
            cursor.execute(
                "INSERT INTO approval_tokens (transfer_id, token_hash, expires_at) VALUES (?, ?, ?)",
                (transfer_id, token_hash, expires_at.isoformat()),
            )

        return token

    def validate_token(self, transfer_id: int, token: str) -> None:
        """Validate approval token. Raises ApprovalError if invalid."""
        # Get stored token
        cursor = self.conn.cursor()
        row = cursor.execute(
            "SELECT token_hash, expires_at, used_at FROM approval_tokens WHERE transfer_id = ?",
            (transfer_id,),
        ).fetchone()

        if not row:
            raise ApprovalError("token_invalid", "No token found for transfer")

        stored_hash, expires_at_str, used_at = row
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

        # Use constant-time comparison
        if not hmac.compare_digest(token_hash, stored_hash):
            raise ApprovalError("token_invalid", "Token does not match")

        # Check expiration
        expires_at = datetime.fromisoformat(expires_at_str)
        if self.clock.now() > expires_at:
            raise ApprovalError("token_expired", "Token has expired")

        # Check if already used
        if used_at:
            raise ApprovalError("token_used", "Token already used")

    def mark_used(self, transfer_id: int) -> None:
        """Mark token as used."""
        with transaction(self.conn, immediate=False) as cursor:
            cursor.execute(
                "UPDATE approval_tokens SET used_at = ? WHERE transfer_id = ?",
                (self.clock.now().isoformat(), transfer_id),
            )

    def get_transfer(self, transfer_id: int) -> dict | None:
        """Get transfer details."""
        cursor = self.conn.cursor()
        row = cursor.execute(
            """
            SELECT id, from_wallet, to_wallet, amount_cents, status
            FROM transfers
            WHERE id = ?
            """,
            (transfer_id,),
        ).fetchone()
        
        if row:
            return {
                "id": row[0],
                "from_wallet": row[1],
                "to_wallet": row[2],
                "amount_cents": row[3],
                "status": row[4],
            }
        return None

    def verify_token_for_transfer(self, transfer_id: int, token: str) -> None:
        """Verify token belongs to the specified transfer."""
        transfer = self.get_transfer(transfer_id)
        if not transfer:
            raise ApprovalError("token_invalid", "Transfer not found")

        # Reconstruct what the token should be for this transfer
        cursor = self.conn.cursor()
        token_row = cursor.execute(
            "SELECT expires_at FROM approval_tokens WHERE transfer_id = ?",
            (transfer_id,),
        ).fetchone()

        if not token_row:
            raise ApprovalError("token_invalid", "No token for transfer")

        expires_at = token_row[0]
        message = f"{transfer['id']}|{transfer['from_wallet']}|{transfer['to_wallet']}|{transfer['amount_cents']}|{expires_at}"
        expected_token = hmac.new(self.secret, message.encode("utf-8"), hashlib.sha256).hexdigest()

        # Use constant-time comparison
        if not hmac.compare_digest(token, expected_token):
            raise ApprovalError("token_mismatch", "Token is for a different transfer")
