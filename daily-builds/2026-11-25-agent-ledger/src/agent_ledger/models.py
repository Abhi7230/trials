"""Pydantic models for API requests and responses."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class WalletCreate(BaseModel):
    """Request to create a wallet."""
    id: str = Field(..., min_length=1, max_length=100)
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")


class PolicyUpdate(BaseModel):
    """Update wallet policy."""
    per_tx_cap_cents: int | None = Field(None, ge=1, le=10**12)
    daily_cap_cents: int | None = Field(None, ge=1, le=10**12)
    auto_approve_limit_cents: int | None = Field(None, ge=0, le=10**12)
    trusted_contacts: list[str] | None = None
    blocked_contacts: list[str] | None = None
    timezone: str | None = Field(None, pattern="^[A-Za-z/_]+$")


class Policy(BaseModel):
    """Wallet policy."""
    version: int
    per_tx_cap_cents: int
    daily_cap_cents: int
    auto_approve_limit_cents: int
    trusted_contacts: list[str]
    blocked_contacts: list[str]
    timezone: str


class WalletResponse(BaseModel):
    """Wallet details response."""
    id: str
    balance: int
    currency: str
    daily_spent: int
    policy: Policy


class DepositRequest(BaseModel):
    """Deposit money into wallet."""
    amount_cents: int = Field(..., ge=1, le=10**12)
    memo: str = ""


class TransferCreate(BaseModel):
    """Create a transfer."""
    from_wallet: str = Field(..., alias="from")
    to: str
    amount_cents: int = Field(..., ge=1, le=10**12)
    memo: str = ""

    @field_validator("amount_cents")
    @classmethod
    def validate_amount(cls, v):
        if not isinstance(v, int):
            raise ValueError("amount must be an integer")
        return v


class ApprovalToken(BaseModel):
    """Approval token."""
    token: str


class TransferResponse(BaseModel):
    """Transfer details response."""
    id: int
    from_wallet: str
    to: str
    amount_cents: int
    memo: str
    status: Literal["pending_approval", "completed", "rejected", "denied"]
    reason: str | None = None
    approval_token: str | None = None
    policy_version: int
    created_at: str
    completed_at: str | None = None


class RefundRequest(BaseModel):
    """Create a refund."""
    amount_cents: int = Field(..., ge=1, le=10**12)


class MoneyRequestCreate(BaseModel):
    """Create a money request."""
    from_wallet: str = Field(..., alias="from")
    to: str
    amount_cents: int = Field(..., ge=1, le=10**12)
    memo: str = ""


class MoneyRequestResponse(BaseModel):
    """Money request details."""
    id: int
    from_wallet: str
    to: str
    amount_cents: int
    memo: str
    status: Literal["pending", "paid", "declined", "cancelled"]
    created_at: str
    resolved_at: str | None = None


class SplitItem(BaseModel):
    """Item in a bill split."""
    owner: str | None = None
    amount_cents: int = Field(..., ge=1, le=10**12)


class BillSplitCreate(BaseModel):
    """Create a bill split."""
    payer: str
    participants: list[str] = Field(..., min_length=1, max_length=100)
    items: list[SplitItem]
    tax_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    tip_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    tip_base: Literal["pre_tax", "post_tax"] = "pre_tax"

    @field_validator("participants")
    @classmethod
    def validate_participants(cls, v):
        if len(v) > 100:
            raise ValueError("too many participants")
        if len(set(v)) != len(v):
            raise ValueError("duplicate participants")
        return v


class ParticipantShare(BaseModel):
    """Share for one participant."""
    participant: str
    items_cents: int
    shared_cents: int
    subtotal_cents: int
    tax_cents: int
    tip_cents: int
    total_cents: int


class BillSplitResponse(BaseModel):
    """Bill split result."""
    payer: str
    items_total_cents: int
    tax_cents: int
    tip_cents: int
    grand_total_cents: int
    shares: list[ParticipantShare]
    requests_created: list[int]


class TransactionItem(BaseModel):
    """Transaction list item."""
    id: int
    type: str
    amount_cents: int
    counterparty: str
    memo: str
    timestamp: str


class AuditEntry(BaseModel):
    """Audit log entry."""
    id: int
    request_id: str
    wallet: str | None
    actor: str | None
    endpoint: str
    decision: str
    reason: str | None
    policy_version: int | None
    timestamp: str


class InvariantViolation(BaseModel):
    """Invariant violation."""
    type: str
    description: str
    details: dict


class InvariantsResponse(BaseModel):
    """Invariants check response."""
    ok: bool
    violations: list[InvariantViolation]


class ToolDefinition(BaseModel):
    """MCP-style tool definition."""
    name: str
    description: str
    inputSchema: dict
