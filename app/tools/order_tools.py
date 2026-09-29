import json, re
from sqlalchemy.orm import Session
from app.database.models import Order
from app.utils.errors import InvalidOrderIdError, OrderNotFoundError, UnauthorizedOrderError

ORDER_ID_RE = re.compile(r"^ORD-\d{4}$")
NOT_FOUND_MESSAGE = "Order not found on your account. Please check the order ID."

def validate_order_id(order_id: str) -> str:
    if not ORDER_ID_RE.fullmatch(order_id):
        raise InvalidOrderIdError("Invalid order ID format. Expected ORD-XXXX.")
    return order_id

def _get_authorized(db: Session, order_id: str, customer_id: str) -> Order:
    validate_order_id(order_id)
    order = db.get(Order, order_id)
    if not order:
        raise OrderNotFoundError(NOT_FOUND_MESSAGE)
    if order.customer_id != customer_id:
        # Same message as a missing order so order IDs can't be probed.
        raise UnauthorizedOrderError(NOT_FOUND_MESSAGE)
    return order

def get_order_status(db: Session, order_id: str, customer_id: str) -> dict:
    order = _get_authorized(db, order_id, customer_id)
    return {"order_id": order.order_id, "status": order.status, "estimated_delivery": order.estimated_delivery}

def get_order_details(db: Session, order_id: str, customer_id: str) -> dict:
    order = _get_authorized(db, order_id, customer_id)
    return {
        "order_id": order.order_id, "restaurant_name": order.restaurant_name,
        "items": json.loads(order.items), "total_amount": order.total_amount,
        "status": order.status, "estimated_delivery": order.estimated_delivery,
    }

def owned_order_id(db: Session, order_id: str | None, customer_id: str) -> str | None:
    """Return order_id only if it exists and belongs to this customer, else None."""
    if not order_id or not ORDER_ID_RE.fullmatch(order_id):
        return None
    order = db.get(Order, order_id)
    return order.order_id if order and order.customer_id == customer_id else None

def latest_order_id(db: Session, customer_id: str, active_only: bool = False) -> str | None:
    """Customer's most recent order (optionally only ones not yet delivered/cancelled)."""
    q = db.query(Order).filter(Order.customer_id == customer_id)
    if active_only:
        q = q.filter(~Order.status.in_(["Delivered", "Cancelled"]))
    order = q.order_by(Order.created_at.desc()).first()
    return order.order_id if order else None
