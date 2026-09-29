class AppError(Exception):
    """Base application error."""

class OrderNotFoundError(AppError): pass
class UnauthorizedOrderError(AppError): pass
class InvalidOrderIdError(AppError): pass
class ToolExecutionError(AppError): pass
class LLMServiceError(AppError): pass
class RAGError(AppError): pass
class UnsafeRequestError(AppError): pass
