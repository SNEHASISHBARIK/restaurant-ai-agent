from app.database.database import SessionLocal
from app.agent.schemas import TicketCreateRequest
from app.tools.ticket_tools import create_support_ticket

def test_duplicate_ticket():
    db=SessionLocal()
    req=TicketCreateRequest(customer_id='CUS-005',order_id='ORD-1005',category='Payment',priority='High',sentiment='Negative',summary='Payment deducted but order failed',description='Payment was deducted but order failed.',idempotency_key='same-key-12345')
    a=create_support_ticket(db,req); b=create_support_ticket(db,req)
    assert a.ticket_id == b.ticket_id
    db.close()
