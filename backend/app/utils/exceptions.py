"""Application-specific exceptions."""


class AppException(Exception):
    """Base exception carrying API response metadata."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        code: str = "application_error",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class NotFoundException(AppException):
    """Raised when a requested entity cannot be found."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message=message, status_code=404, code="not_found")


class RepositoryException(AppException):
    """Raised for repository validation, clone, or analysis failures."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            code="repository_error",
        )


class AIServiceException(AppException):
    """Raised when the AI provider cannot produce a valid response."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            code="ai_service_error",
        )

