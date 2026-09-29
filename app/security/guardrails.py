import re
from app.utils.errors import UnsafeRequestError

PATTERNS = [
    r"ignore (all|any|the) previous instructions",
    r"reveal (your|the) system prompt",
    r"(tell me|show me|give me|what is) (the )?(api key|secret|password|environment variables)",
    r"run\s+(select|insert|update|delete|drop|alter)\b",
    r"execute\s+(this )?(python|shell|command|code)",
    r"show me (every|all) customer",
    r"another customer",
]

def check_message(message: str, max_length: int = 2000) -> None:
    if len(message) > max_length:
        raise UnsafeRequestError("Message is too long.")
    lowered = message.lower().strip()
    if any(re.search(pattern, lowered) for pattern in PATTERNS):
        raise UnsafeRequestError("I can't help with that request.")

def safe_error_message(exc: Exception) -> str:
    return str(exc) if isinstance(exc, UnsafeRequestError) else "I couldn't complete that request right now."
