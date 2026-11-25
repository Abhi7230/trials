"""Error definitions and handlers."""

from typing import Any
from fastapi import Request, status
from fastapi.responses import JSONResponse


class LedgerError(Exception):
    """Base exception for ledger errors."""

    def __init__(self, code: str, reason: str, detail: str = ""):
        self.code = code
        self.reason = reason
        self.detail = detail
        super().__init__(f"{code}: {reason}")


class InsufficientFundsError(LedgerError):
    """Raised when account has insufficient funds."""

    def __init__(self, detail: str = ""):
        super().__init__("insufficient_funds", "insufficient_funds", detail)


class PolicyRejectionError(LedgerError):
    """Raised when policy rejects a transfer."""

    def __init__(self, reason: str, detail: str = ""):
        super().__init__("policy_rejection", reason, detail)


class IdempotencyError(LedgerError):
    """Raised for idempotency violations."""

    def __init__(self, reason: str, detail: str = ""):
        super().__init__("idempotency_error", reason, detail)


class ApprovalError(LedgerError):
    """Raised for approval token errors."""

    def __init__(self, reason: str, detail: str = ""):
        super().__init__("approval_error", reason, detail)


class TransferError(LedgerError):
    """Raised for transfer-specific errors."""

    def __init__(self, reason: str, detail: str = ""):
        super().__init__("transfer_error", reason, detail)


def error_response(code: str, reason: str, detail: str = "") -> dict[str, Any]:
    """Create standardized error response."""
    return {
        "error": {
            "code": code,
            "reason": reason,
            "detail": detail,
        }
    }


async def ledger_error_handler(request: Request, exc: LedgerError) -> JSONResponse:
    """Handle LedgerError exceptions."""
    status_code = status.HTTP_409_CONFLICT
    
    if exc.reason in ["idempotency_key_required", "idempotency_key_missing"]:
        status_code = status.HTTP_400_BAD_REQUEST
    elif exc.reason in ["token_invalid", "token_expired", "token_used", "token_mismatch"]:
        status_code = status.HTTP_403_FORBIDDEN
    elif exc.reason == "currency_mismatch":
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    
    return JSONResponse(
        status_code=status_code,
        content=error_response(exc.code, exc.reason, exc.detail),
    )
