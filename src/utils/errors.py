from enum import Enum
from typing import Any


class EvaluationError(Enum):
    API_ERROR = "api_error"
    PARSE_ERROR = "parse_error"
    TIMEOUT_ERROR = "timeout_error"
    CONSENSUS_FAILED = "consensus_failed"


class EvaluationException(Exception):
    def __init__(self, error_type: EvaluationError, message: str, details: dict[str, Any] | None = None):
        self.error_type = error_type
        self.message = message
        self.details = details or {}
        super().__init__(f"[{error_type.value}] {message}")


class APIError(EvaluationException):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(EvaluationError.API_ERROR, message, details)


class ParseError(EvaluationException):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(EvaluationError.PARSE_ERROR, message, details)


class TimeoutError(EvaluationException):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(EvaluationError.TIMEOUT_ERROR, message, details)