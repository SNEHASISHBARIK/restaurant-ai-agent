from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import SupportTicket
from app.agent.schemas import TicketCreateRequest, TicketOut
from app.tools.ticket_tools import create_support_ticket

router=APIRouter(prefix="/api/support", tags=["support"])

@router.post("/tickets", response_model=TicketOut, summary="Create a support ticket")
def create_ticket(request: TicketCreateRequest, db: Session=Depends(get_db)):
    ticket=create_support_ticket(db, request)
    return TicketOut(ticket_id=ticket.ticket_id, customer_id=ticket.customer_id, order_id=ticket.order_id, category=ticket.category, priority=ticket.priority, sentiment=ticket.sentiment, summary=ticket.summary, status=ticket.status, created_at=ticket.created_at.isoformat())

@router.get("/tickets/{ticket_id}", response_model=TicketOut, summary="Get a support ticket")
def get_ticket(ticket_id: str, db: Session=Depends(get_db)):
    ticket=db.get(SupportTicket, ticket_id)
    if not ticket: raise HTTPException(404, "Ticket not found.")
    return TicketOut(ticket_id=ticket.ticket_id, customer_id=ticket.customer_id, order_id=ticket.order_id, category=ticket.category, priority=ticket.priority, sentiment=ticket.sentiment, summary=ticket.summary, status=ticket.status, created_at=ticket.created_at.isoformat())
