"""Policy engine for transfer decisions."""

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Literal
from zoneinfo import ZoneInfo

from agent_ledger.db import transaction
from agent_ledger.clock import Clock


DecisionType = Literal["completed", "pending_approval", "rejected"]


class PolicyDecision:
    """Result of policy evaluation."""

    def __init__(
        self,
        decision: DecisionType,
        reason: str | None = None,
        policy_version: int = 1,
    ):
        self.decision = decision
        self.reason = reason
        self.policy_version = policy_version


class PolicyEngine:
    """Policy engine for evaluating transfers."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock):
        self.conn = conn
        self.clock = clock

    def get_policy(self, wallet_id: str) -> dict[str, Any] | None:
        """Get current policy for wallet."""
        cursor = self.conn.cursor()
        row = cursor.execute(
            """
            SELECT version, per_tx_cap_cents, daily_cap_cents, auto_approve_limit_cents,
                   trusted_contacts, blocked_contacts, timezone
            FROM policies
            WHERE wallet_id = ?
            ORDER BY version DESC
            LIMIT 1
            """,
            (wallet_id,),
        ).fetchone()
        
        if row:
            return {
                "version": row[0],
                "per_tx_cap_cents": row[1],
                "daily_cap_cents": row[2],
                "auto_approve_limit_cents": row[3],
                "trusted_contacts": json.loads(row[4]),
                "blocked_contacts": json.loads(row[5]),
                "timezone": row[6],
            }
        return None

    def create_default_policy(self, wallet_id: str, created_at: datetime) -> None:
        """Create default policy for a wallet."""
        with transaction(self.conn) as cursor:
            cursor.execute(
                """
                INSERT INTO policies (
                    wallet_id, version, per_tx_cap_cents, daily_cap_cents,
                    auto_approve_limit_cents, trusted_contacts, blocked_contacts,
                    timezone, created_at
                ) VALUES (?, 1, ?, ?, ?, ?, ?, 'UTC', ?)
                """,
                (
                    wallet_id,
                    10**12,  # 10 billion cents = 100 million dollars
                    10**12,
                    0,
                    "[]",
                    "[]",
                    created_at.isoformat(),
                ),
            )

    def update_policy(
        self, wallet_id: str, updates: dict[str, Any], created_at: datetime
    ) -> int:
        """Update wallet policy, creating a new version."""
        current = self.get_policy(wallet_id)
        if not current:
            raise ValueError("Policy not found")

        new_version = current["version"] + 1

        # Merge updates
        per_tx_cap = updates.get("per_tx_cap_cents", current["per_tx_cap_cents"])
        daily_cap = updates.get("daily_cap_cents", current["daily_cap_cents"])
        auto_approve = updates.get("auto_approve_limit_cents", current["auto_approve_limit_cents"])
        trusted = updates.get("trusted_contacts", current["trusted_contacts"])
        blocked = updates.get("blocked_contacts", current["blocked_contacts"])
        tz = updates.get("timezone", current["timezone"])

        with transaction(self.conn) as cursor:
            cursor.execute(
                """
                INSERT INTO policies (
                    wallet_id, version, per_tx_cap_cents, daily_cap_cents,
                    auto_approve_limit_cents, trusted_contacts, blocked_contacts,
                    timezone, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    wallet_id,
                    new_version,
                    per_tx_cap,
                    daily_cap,
                    auto_approve,
                    json.dumps(trusted),
                    json.dumps(blocked),
                    tz,
                    created_at.isoformat(),
                ),
            )

        return new_version

    def evaluate_transfer(
        self, from_wallet: str, to_wallet: str, amount_cents: int, from_currency: str, to_currency: str
    ) -> PolicyDecision:
        """Evaluate a transfer against policy."""
        policy = self.get_policy(from_wallet)
        if not policy:
            return PolicyDecision("rejected", "no_policy")

        # Decision order: blocked → self → currency → per_tx_cap → trusted+auto_approve → pending

        # Check blocked
        if to_wallet in policy["blocked_contacts"]:
            return PolicyDecision("rejected", "blocked_contact", policy["version"])

        # Check self-transfer
        if from_wallet == to_wallet:
            return PolicyDecision("rejected", "self_transfer", policy["version"])

        # Check currency mismatch (should be caught earlier, but checked here too)
        if from_currency != to_currency:
            return PolicyDecision("rejected", "currency_mismatch", policy["version"])

        # Check per-transaction cap (inclusive)
        if amount_cents > policy["per_tx_cap_cents"]:
            return PolicyDecision("rejected", "per_tx_cap", policy["version"])

        # Check if trusted and within auto-approve limit
        is_trusted = to_wallet in policy["trusted_contacts"]
        if is_trusted and amount_cents <= policy["auto_approve_limit_cents"]:
            return PolicyDecision("completed", None, policy["version"])

        # Otherwise, pending approval
        return PolicyDecision("pending_approval", None, policy["version"])

    def check_balance_and_daily_cap(
        self, wallet_id: str, amount_cents: int
    ) -> tuple[bool, str | None]:
        """Check if transfer would exceed balance or daily cap."""
        policy = self.get_policy(wallet_id)
        if not policy:
            return False, "no_policy"

        # Check balance
        cursor = self.conn.cursor()
        balance_row = cursor.execute(
            "SELECT balance FROM wallets WHERE id = ?", (wallet_id,)
        ).fetchone()
        
        if not balance_row or balance_row[0] < amount_cents:
            return False, "insufficient_funds"

        # Check daily cap
        daily_spent = self.get_daily_spent(wallet_id, policy["timezone"])
        if daily_spent + amount_cents > policy["daily_cap_cents"]:
            return False, "daily_cap"

        return True, None

    def get_daily_spent(self, wallet_id: str, timezone_str: str) -> int:
        """Get total spent today in wallet's timezone."""
        now = self.clock.now()
        
        # Get start of day in wallet's timezone
        try:
            tz = ZoneInfo(timezone_str)
        except Exception:
            tz = timezone.utc
        
        local_now = now.astimezone(tz)
        start_of_day = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_day_utc = start_of_day.astimezone(timezone.utc)

        # Sum completed transfers from today
        cursor = self.conn.cursor()
        row = cursor.execute(
            """
            SELECT COALESCE(SUM(amount_cents), 0)
            FROM transfers
            WHERE from_wallet = ?
              AND status = 'completed'
              AND completed_at >= ?
            """,
            (wallet_id, start_of_day_utc.isoformat()),
        ).fetchone()

        return row[0] if row else 0
