"""FastAPI application."""

import json
import secrets
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

from agent_ledger.approvals import ApprovalManager
from agent_ledger.audit import AuditLogger
from agent_ledger.clock import Clock, SystemClock
from agent_ledger.db import get_connection, init_db
from agent_ledger.errors import LedgerError, error_response, ledger_error_handler
from agent_ledger.idempotency import IdempotencyManager
from agent_ledger.invariants import InvariantChecker
from agent_ledger.ledger import Ledger
from agent_ledger.models import *
from agent_ledger.policy import PolicyEngine
from agent_ledger.refunds import RefundManager
from agent_ledger.requests import RequestManager
from agent_ledger.split import BillSplitter
from agent_ledger.tools import generate_tool_manifest
from agent_ledger.transfers import TransferManager


def create_app(
    db_path: str = "ledger.db",
    clock: Clock | None = None,
    secret: bytes | None = None,
) -> FastAPI:
    """Create FastAPI application."""
    
    _clock = clock or SystemClock()
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Initialize database
        conn = get_connection(db_path)
        init_db(conn)
        
        # Store dependencies
        app.state.conn = conn
        app.state.clock = _clock
        app.state.secret = secret
        
        # Initialize managers
        app.state.ledger = Ledger(conn)
        app.state.policy = PolicyEngine(conn, _clock)
        app.state.approvals = ApprovalManager(conn, _clock, secret)
        app.state.idempotency = IdempotencyManager(conn, _clock)
        app.state.audit = AuditLogger(conn, _clock)
        app.state.invariants = InvariantChecker(conn)
        app.state.refunds = RefundManager(conn, app.state.ledger, _clock)
        
        # Circular dependency: transfers needs requests, requests needs transfers
        app.state.transfers = TransferManager(
            conn, app.state.ledger, app.state.policy, app.state.approvals, _clock
        )
        app.state.requests = RequestManager(conn, _clock, app.state.transfers)
        app.state.splitter = BillSplitter()
        
        yield
        
        conn.close()
    
    app = FastAPI(title="Agent Ledger", version="0.1.0", lifespan=lifespan)
    app.add_exception_handler(LedgerError, ledger_error_handler)
    
    # Health check
    @app.get("/healthz")
    async def health_check():
        return {"status": "ok"}
    
    # Wallets
    @app.post("/v1/wallets", status_code=status.HTTP_201_CREATED)
    async def create_wallet(request: Request, wallet: WalletCreate):
        ledger: Ledger = request.app.state.ledger
        policy: PolicyEngine = request.app.state.policy
        clock: Clock = request.app.state.clock
        
        ledger.create_wallet(wallet.id, wallet.currency, clock.now())
        policy.create_default_policy(wallet.id, clock.now())
        
        return await get_wallet(request, wallet.id)
    
    @app.get("/v1/wallets/{wallet_id}")
    async def get_wallet(request: Request, wallet_id: str):
        ledger: Ledger = request.app.state.ledger
        policy: PolicyEngine = request.app.state.policy
        
        wallet = ledger.get_wallet(wallet_id)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        pol = policy.get_policy(wallet_id)
        daily_spent = policy.get_daily_spent(wallet_id, pol["timezone"] if pol else "UTC")
        
        return WalletResponse(
            id=wallet["id"],
            balance=wallet["balance"],
            currency=wallet["currency"],
            daily_spent=daily_spent,
            policy=Policy(**pol) if pol else None,
        )
    
    @app.put("/v1/wallets/{wallet_id}/policy")
    async def update_wallet_policy(request: Request, wallet_id: str, policy_update: PolicyUpdate):
        policy: PolicyEngine = request.app.state.policy
        clock: Clock = request.app.state.clock
        
        updates = policy_update.model_dump(exclude_none=True)
        policy.update_policy(wallet_id, updates, clock.now())
        
        return await get_wallet(request, wallet_id)
    
    @app.post("/v1/wallets/{wallet_id}/deposits", status_code=status.HTTP_201_CREATED)
    async def deposit(
        request: Request,
        wallet_id: str,
        deposit_req: DepositRequest,
        idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    ):
        if not idempotency_key:
            raise HTTPException(status_code=400, detail=error_response(
                "idempotency_error", "idempotency_key_required", "Idempotency-Key header required"
            ))
        
        ledger: Ledger = request.app.state.ledger
        clock: Clock = request.app.state.clock
        idempotency: IdempotencyManager = request.app.state.idempotency
        
        # Check idempotency
        body = deposit_req.model_dump()
        is_replay, replay_status, replay_body = idempotency.check_and_store(
            idempotency_key, wallet_id, "POST", f"/v1/wallets/{wallet_id}/deposits", body
        )
        
        if is_replay:
            return JSONResponse(
                content=json.loads(replay_body),
                status_code=replay_status,
                headers={"Idempotent-Replayed": "true"},
            )
        
        # Create deposit
        entry_id = ledger.create_journal_entry(
            "deposit",
            [("external:funding", -deposit_req.amount_cents), (wallet_id, deposit_req.amount_cents)],
            clock.now(),
        )
        
        response = {"entry_id": entry_id, "wallet_id": wallet_id, "amount_cents": deposit_req.amount_cents}
        idempotency.store_response(
            idempotency_key, wallet_id, "POST", f"/v1/wallets/{wallet_id}/deposits",
            201, json.dumps(response)
        )
        
        return response
    
    # Transfers
    @app.post("/v1/transfers", status_code=status.HTTP_201_CREATED)
    async def create_transfer(
        request: Request,
        transfer: TransferCreate,
        idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    ):
        if not idempotency_key:
            raise HTTPException(status_code=400, detail=error_response(
                "idempotency_error", "idempotency_key_required", "Idempotency-Key header required"
            ))
        
        transfers: TransferManager = request.app.state.transfers
        idempotency: IdempotencyManager = request.app.state.idempotency
        audit: AuditLogger = request.app.state.audit
        
        # Check idempotency
        body = transfer.model_dump(by_alias=True)
        try:
            is_replay, replay_status, replay_body = idempotency.check_and_store(
                idempotency_key, transfer.from_wallet, "POST", "/v1/transfers", body
            )
            
            if is_replay:
                return JSONResponse(
                    content=json.loads(replay_body),
                    status_code=replay_status,
                    headers={"Idempotent-Replayed": "true"},
                )
        except LedgerError as e:
            raise
        
        # Create transfer
        try:
            result = transfers.create_transfer(
                transfer.from_wallet, transfer.to, transfer.amount_cents, transfer.memo
            )
            
            # Log audit
            audit.log(
                idempotency_key,
                "/v1/transfers",
                result["status"],
                wallet=transfer.from_wallet,
                reason=result.get("reason"),
                policy_version=result.get("policy_version"),
            )
            
            # Store idempotency
            response_body = json.dumps(result)
            idempotency.store_response(
                idempotency_key, transfer.from_wallet, "POST", "/v1/transfers", 201, response_body
            )
            
            return result
            
        except LedgerError as e:
            # Store policy rejections for idempotency replay
            if e.code == "policy_rejection":
                error_response_body = json.dumps(error_response(e.code, e.reason, e.detail))
                idempotency.store_response(
                    idempotency_key, transfer.from_wallet, "POST", "/v1/transfers",
                    409, error_response_body
                )
                
                # Log audit for rejection
                audit.log(
                    idempotency_key,
                    "/v1/transfers",
                    "rejected",
                    wallet=transfer.from_wallet,
                    reason=e.reason,
                )
            
            raise
    
    @app.get("/v1/transfers/{transfer_id}")
    async def get_transfer(request: Request, transfer_id: int):
        transfers: TransferManager = request.app.state.transfers
        return transfers.get_transfer(transfer_id)
    
    @app.post("/v1/transfers/{transfer_id}/approve")
    async def approve_transfer(request: Request, transfer_id: int, token_req: ApprovalToken):
        transfers: TransferManager = request.app.state.transfers
        audit: AuditLogger = request.app.state.audit
        
        try:
            result = transfers.approve_transfer(transfer_id, token_req.token)
            audit.log(
                f"approve-{transfer_id}",
                f"/v1/transfers/{transfer_id}/approve",
                "approved",
                wallet=result["from_wallet"],
            )
            return result
        except LedgerError as e:
            audit.log(
                f"approve-{transfer_id}",
                f"/v1/transfers/{transfer_id}/approve",
                "rejected",
                reason=e.reason,
            )
            raise
    
    @app.post("/v1/transfers/{transfer_id}/deny")
    async def deny_transfer(request: Request, transfer_id: int):
        transfers: TransferManager = request.app.state.transfers
        audit: AuditLogger = request.app.state.audit
        
        result = transfers.deny_transfer(transfer_id)
        audit.log(
            f"deny-{transfer_id}",
            f"/v1/transfers/{transfer_id}/deny",
            "denied",
            wallet=result["from_wallet"],
        )
        return result
    
    @app.post("/v1/transfers/{transfer_id}/reverse")
    async def reverse_transfer(request: Request, transfer_id: int):
        transfers: TransferManager = request.app.state.transfers
        audit: AuditLogger = request.app.state.audit
        
        result = transfers.reverse_transfer(transfer_id)
        audit.log(
            f"reverse-{transfer_id}",
            f"/v1/transfers/{transfer_id}/reverse",
            "reversed",
        )
        return result
    
    @app.post("/v1/transfers/{transfer_id}/refunds")
    async def create_refund(request: Request, transfer_id: int, refund_req: RefundRequest):
        refunds: RefundManager = request.app.state.refunds
        audit: AuditLogger = request.app.state.audit
        
        result = refunds.create_refund(transfer_id, refund_req.amount_cents)
        audit.log(
            f"refund-{transfer_id}",
            f"/v1/transfers/{transfer_id}/refunds",
            "refunded",
        )
        return result
    
    # Money requests
    @app.post("/v1/requests", status_code=status.HTTP_201_CREATED)
    async def create_request(request: Request, money_req: MoneyRequestCreate):
        requests: RequestManager = request.app.state.requests
        return requests.create_request(
            money_req.from_wallet, money_req.to, money_req.amount_cents, money_req.memo
        )
    
    @app.post("/v1/requests/{request_id}/pay")
    async def pay_request(
        request: Request,
        request_id: int,
        idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    ):
        if not idempotency_key:
            raise HTTPException(status_code=400, detail=error_response(
                "idempotency_error", "idempotency_key_required", "Idempotency-Key header required"
            ))
        
        requests: RequestManager = request.app.state.requests
        return requests.pay_request(request_id, idempotency_key)
    
    @app.post("/v1/requests/{request_id}/decline")
    async def decline_request(request: Request, request_id: int):
        requests: RequestManager = request.app.state.requests
        return requests.decline_request(request_id)
    
    @app.post("/v1/requests/{request_id}/cancel")
    async def cancel_request(request: Request, request_id: int):
        requests: RequestManager = request.app.state.requests
        return requests.cancel_request(request_id)
    
    # Bill splits
    @app.post("/v1/splits", status_code=status.HTTP_201_CREATED)
    async def split_bill(request: Request, split_req: BillSplitCreate):
        splitter: BillSplitter = request.app.state.splitter
        requests_mgr: RequestManager = request.app.state.requests
        
        # Calculate split
        result = splitter.split_bill(
            split_req.payer,
            split_req.participants,
            [item.model_dump() for item in split_req.items],
            split_req.tax_rate,
            split_req.tip_rate,
            split_req.tip_base,
        )
        
        # Create money requests for non-payer participants
        request_ids = []
        for share in result["shares"]:
            if share["participant"] != split_req.payer:
                req = requests_mgr.create_request(
                    split_req.payer,
                    share["participant"],
                    share["total_cents"],
                    f"Bill split: {share['total_cents']} cents",
                )
                request_ids.append(req["id"])
        
        result["requests_created"] = request_ids
        return result
    
    # Transactions
    @app.get("/v1/wallets/{wallet_id}/transactions")
    async def list_transactions(request: Request, wallet_id: str, limit: int = 50):
        ledger: Ledger = request.app.state.ledger
        return ledger.list_transactions(wallet_id, limit)
    
    # Audit
    @app.get("/v1/audit")
    async def get_audit_log(request: Request, wallet: str | None = None, limit: int = 100):
        audit: AuditLogger = request.app.state.audit
        return audit.get_audit_log(wallet, limit)
    
    # Tools
    @app.get("/v1/tools")
    async def get_tools():
        return generate_tool_manifest()
    
    # Admin
    @app.get("/v1/admin/invariants")
    async def check_invariants(request: Request):
        checker: InvariantChecker = request.app.state.invariants
        return checker.check_all()
    
    return app
