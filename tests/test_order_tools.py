import pytest
from app.database.database import SessionLocal
from app.tools.order_tools import get_order_status
from app.utils.errors import UnauthorizedOrderError

def test_order_tool_authorization():
    db=SessionLocal()
    with pytest.raises(UnauthorizedOrderError): get_order_status(db,'ORD-1005','CUS-001')
    db.close()
