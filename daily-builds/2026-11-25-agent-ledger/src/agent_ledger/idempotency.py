"""Idempotency key management."""

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Any

from agent_ledger.clock import Clock
from agent_ledger.db import transaction
from agent_ledger.errors import IdempotencyError


class IdempotencyManager:
    """Manages idempotency keys for API requests."""

    RETENTION_HOURS = 24

    def __init__(self, conn: sqlite3.Connection, clock: Clock):
        self.conn = conn
        self.clock = clock

    def _hash_key(self, key: str) -> str:
        """Hash an idempotency key."""
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def _hash_body(self, body: dict[str, Any]) -> str:
        """Hash request body canonically."""
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def check_and_store(
        self,
        key: str,
        wallet_id: str,
        method: str,
        path: str,
        body: dict[str, Any],
    ) -> tuple[bool, int | None, bytes | None]:
        """
        Check idempotency key and store if new.
        
        Returns:
            (is_replay, status_code, response_body)
            - is_replay=True: return stored response
            - is_replay=False: proceed with request
        
        Raises:
            IdempotencyError: if key is reused with different body or in progress
        """
        key_hash = self._hash_key(key)
        body_hash = self._hash_body(body)

        with transaction(self.conn) as cursor:
            # Check if key exists
            row = cursor.execute(
                """
                SELECT body_hash, response_status, response_body, in_progress
                FROM idempotency_keys
                WHERE key_hash = ? AND wallet_id = ? AND method = ? AND path = ?
                """,
                (key_hash, wallet_id, method, path),
            ).fetchone()

            if row:
                stored_body_hash, status, response, in_progress = row

                # Check if request is in progress
                if in_progress:
                    raise IdempotencyError("idempotency_key_in_progress", "Request in progress")

                # Check if body matches
                if stored_body_hash != body_hash:
                    raise IdempotencyError("idempotency_key_reused", "Key reused with different body")

                # Return stored response
                return True, status, response.encode("utf-8") if isinstance(response, str) else response

            # Store new key (in progress)
            cursor.execute(
                """
                INSERT INTO idempotency_keys (
                    key_hash, wallet_id, method, path, body_hash,
                    response_status, response_body, in_progress, created_at
                ) VALUES (?, ?, ?, ?, ?, 0, '', 1, ?)
                """,
                (key_hash, wallet_id, method, path, body_hash, self.clock.now().isoformat()),
            )

        return False, None, None

    def store_response(
        self,
        key: str,
        wallet_id: str,
        method: str,
        path: str,
        status: int,
        response: str,
    ) -> None:
        """Store response for idempotency key."""
        key_hash = self._hash_key(key)

        with transaction(self.conn, immediate=False) as cursor:
            cursor.execute(
                """
                UPDATE idempotency_keys
                SET response_status = ?, response_body = ?, in_progress = 0
                WHERE key_hash = ? AND wallet_id = ? AND method = ? AND path = ?
                """,
                (status, response, key_hash, wallet_id, method, path),
            )

    def purge_old_keys(self) -> int:
        """Remove keys older than retention period. Returns count deleted."""
        cutoff = self.clock.now() - timedelta(hours=self.RETENTION_HOURS)
        
        with transaction(self.conn, immediate=False) as cursor:
            cursor.execute(
                "DELETE FROM idempotency_keys WHERE created_at < ?",
                (cutoff.isoformat(),),
            )
            return cursor.rowcount
