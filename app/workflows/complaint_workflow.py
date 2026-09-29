"""Complaint workflow helpers kept separate from the HTTP layer."""
from app.agent.schemas import ComplaintClassification

PAYMENT_HIGH = ["deducted", "twice", "double", "duplicate", "unauthorized", "unauthorised", "fraud", "failed", "overcharg"]
SAFETY = ["allergic", "allergy", "sick", "food poisoning", "contaminat", "insect", "hair in"]
LONG_WAIT = ["hours", "still waiting", "over an hour"]

# Placeholder targets: set these to what the support team can actually meet.
RESPONSE_TARGETS = {"High": "1 hour", "Medium": "4 hours", "Low": "24 hours"}


def apply_priority_rules(classification: ComplaintClassification, message: str) -> ComplaintClassification:
    text = message.lower()
    if classification.category == "Payment":
        classification.priority = "High" if any(x in text for x in PAYMENT_HIGH) else max_priority(classification.priority, "Medium")
    elif classification.category in {"Delivery", "Refund", "Order"}:
        classification.priority = max_priority(classification.priority, "Medium")
    if any(x in text for x in SAFETY) or (classification.category == "Delivery" and any(x in text for x in LONG_WAIT)):
        classification.priority = "High"
    return classification


def max_priority(a: str, b: str) -> str:
    order = {"Low": 0, "Medium": 1, "High": 2}
    return a if order[a] >= order[b] else b
