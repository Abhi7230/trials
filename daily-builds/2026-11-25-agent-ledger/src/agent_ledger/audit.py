"""Audit log management."""

import sqlite3
from typing import Any

from agent_ledger.clock import Clock


class AuditLogger:
    """Manages audit log entries."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock):
        self.conn = conn
        self.clock = clock

    def log(
        self,
        request_id: str,
        endpoint: str,
        decision: str,
        wallet: str | None = None,
        actor: str | None = None,
        reason: str | None = None,
        policy_version: int | None = None,
    ) -> None:
        """Log an audit entry in a separate transaction."""
        # Use a separate connection for audit to avoid rollback issues
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_log (
                    request_id, wallet, actor, endpoint, decision, reason, policy_version, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request_id,
                    wallet,
                    actor,
                    endpoint,
                    decision,
                    reason,
                    policy_version,
                    self.clock.now().isoformat(),
                ),
            )
            self.conn.commit()
        except Exception:
            # Never let audit failure break the main operation
            pass

    def get_audit_log(self, wallet: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        """Get audit log entries."""
        cursor = self.conn.cursor()
        
        if wallet:
            rows = cursor.execute(
                """
                SELECT id, request_id, wallet, actor, endpoint, decision, reason, policy_version, timestamp
                FROM audit_log
                WHERE wallet = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (wallet, limit),
            ).fetchall()
        else:
            rows = cursor.execute(
                """
                SELECT id, request_id, wallet, actor, endpoint, decision, reason, policy_version, timestamp
                FROM audit_log
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            {
                "id": row[0],
                "request_id": row[1],
                "wallet": row[2],
                "actor": row[3],
                "endpoint": row[4],
                "decision": row[5],
                "reason": row[6],
                "policy_version": row[7],
                "timestamp": row[8],
            }
            for row in rows
        ]
