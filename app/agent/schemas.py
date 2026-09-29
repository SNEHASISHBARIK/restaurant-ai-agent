from typing import Literal, Any
from pydantic import BaseModel, Field

Category = Literal["Payment", "Order", "Delivery", "Refund", "Technical"]
Priority = Literal["Low", "Medium", "High"]
Sentiment = Literal["Positive", "Neutral", "Negative"]

class ComplaintClassification(BaseModel):
    category: Category
    priority: Priority
    sentiment: Sentiment
    summary: str = Field(min_length=3, max_length=500)

class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=80)
    customer_id: str = Field(pattern=r"^CUS-\d{3}$")
    message: str = Field(min_length=1, max_length=2000)

class ToolCallInfo(BaseModel):
    tool: str
    success: bool
    duration_ms: float | None = None

class ChatResponse(BaseModel):
    request_id: str
    answer: str
    intent: str
    source: str
    tool_calls: list[ToolCallInfo] = []
    documents: list[str] = []
    ticket_id: str | None = None
    category: str | None = None
    priority: str | None = None

class TicketCreateRequest(BaseModel):
    customer_id: str = Field(pattern=r"^CUS-\d{3}$")
    order_id: str | None = Field(default=None, pattern=r"^ORD-\d{4}$")
    category: Category
    priority: Priority
    sentiment: Sentiment
    summary: str = Field(min_length=3, max_length=500)
    description: str = Field(min_length=3, max_length=5000)
    idempotency_key: str = Field(min_length=8, max_length=128)

class OrderOut(BaseModel):
    order_id: str
    customer_id: str
    restaurant_name: str
    items: list[str]
    total_amount: float
    status: str
    estimated_delivery: str
    created_at: str

class TicketOut(BaseModel):
    ticket_id: str
    customer_id: str
    order_id: str | None
    category: str
    priority: str
    sentiment: str
    summary: str
    status: str
    created_at: str
