import json
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import Order
from app.agent.schemas import OrderOut
from app.tools.order_tools import get_order_status, get_order_details
from app.utils.errors import OrderNotFoundError, UnauthorizedOrderError, InvalidOrderIdError

router=APIRouter(prefix="/api/orders", tags=["orders"])

def customer_from_header(x_customer_id: str | None):
    if not x_customer_id or not x_customer_id.startswith("CUS-"):
        raise HTTPException(401, "Customer identity is required.")
    return x_customer_id

@router.get("/{order_id}", response_model=OrderOut, summary="Get authorized order details")
def order_details(order_id: str, db: Session=Depends(get_db), x_customer_id: str | None=Header(default=None)):
    customer_id=customer_from_header(x_customer_id)
    try:
        data=get_order_details(db, order_id, customer_id)
        order=db.get(Order, order_id)
        return OrderOut(**data, customer_id=order.customer_id, created_at=order.created_at.isoformat())
    except InvalidOrderIdError as e: raise HTTPException(400, str(e))
    except OrderNotFoundError as e: raise HTTPException(404, str(e))
    except UnauthorizedOrderError as e: raise HTTPException(404, str(e))

@router.get("/{order_id}/status", summary="Get authorized current order status")
def order_status(order_id: str, db: Session=Depends(get_db), x_customer_id: str | None=Header(default=None)):
    customer_id=customer_from_header(x_customer_id)
    try: return get_order_status(db, order_id, customer_id)
    except InvalidOrderIdError as e: raise HTTPException(400, str(e))
    except OrderNotFoundError as e: raise HTTPException(404, str(e))
    except UnauthorizedOrderError as e: raise HTTPException(404, str(e))
