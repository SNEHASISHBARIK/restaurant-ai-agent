import re

ORDER_ID_RE = re.compile(r"\bORD-\d{4}\b")

DETAILS_HINTS = [
    "order details", "details of", "details for", "details about", "detail of",
    "what did i order", "what i ordered", "what was in", "what's in", "what is in",
    "items in", "items of", "contents of", "order summary", "receipt",
]
STATUS_HINTS = [
    "where is", "where's", "status", "track", "delivered", "delivery status",
    "when will", "eta", "how long",
]
POLICY_HINTS = [
    "policy", "policies", "faq", "operating hours", "opening hours", "working hours",
    "can i cancel", "how do i cancel", "how can i cancel", "cancel",
]
COMPLAINT_HINTS = [
    "payment", "charged", "deducted", "double charge", "twice", "duplicate", "overcharg",
    "failed", "complaint", "problem", "issue", "wrong", "missing", "cold",
    "late", "delay", "never arrived", "not delivered", "refund",
]


def extract_order_id(text: str) -> str | None:
    m = ORDER_ID_RE.search(text.upper())
    return m.group(0) if m else None


def route_message(text: str) -> str:
    """Return one of: order_details, order_status, rag, complaint, general.

    Order matters: specific lookups first, then policy questions, then complaints.
    Policy comes before complaints so "policy on late deliveries" is a policy
    question, while "I was charged twice, refund me" is a complaint.
    """
    t = text.lower()
    if any(x in t for x in DETAILS_HINTS):
        return "order_details"
    if any(x in t for x in STATUS_HINTS):
        return "order_status"
    if any(x in t for x in POLICY_HINTS):
        return "rag"
    if any(x in t for x in COMPLAINT_HINTS):
        return "complaint"
    return "general"
