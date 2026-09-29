import hashlib, re
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy.orm import Session
from app.database.models import SupportTicket
from app.agent.schemas import TicketCreateRequest

def normalize_issue(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower().strip())

def make_idempotency_key(customer_id: str, order_id: str | None, issue: str) -> str:
    raw = f"{customer_id}|{order_id or ''}|{normalize_issue(issue)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def new_ticket_id(db: Session) -> str:
    """TICKET-YYYYMMDD-XXXXXX: date plus random suffix, re-rolled if it already exists."""
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    while True:
        candidate = f"TICKET-{day}-{uuid4().hex[:6].upper()}"
        if not db.get(SupportTicket, candidate):
            return candidate

def create_support_ticket(db: Session, request: TicketCreateRequest) -> SupportTicket:
    existing = db.query(SupportTicket).filter_by(idempotency_key=request.idempotency_key).first()
    if existing:
        return existing
    ticket_id = new_ticket_id(db)
    ticket = SupportTicket(
        ticket_id=ticket_id, customer_id=request.customer_id, order_id=request.order_id,
        category=request.category, priority=request.priority, sentiment=request.sentiment,
        summary=request.summary, description=request.description, status="Open",
        idempotency_key=request.idempotency_key,
    )
    db.add(ticket); db.commit(); db.refresh(ticket)
    return ticket
