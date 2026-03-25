from __future__ import annotations

from fastapi import status
from typing import Any


class ReconixException(Exception):

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ReconixException):

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class AuthenticationError(ReconixException):

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message,
            code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationError(ReconixException):

    def __init__(
        self, message: str = "Insufficient permissions", required_role: str | None = None
    ):
        details = {}
        if required_role:
            details["required_role"] = required_role
        super().__init__(
            message,
            code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class ResourceNotFoundError(ReconixException):

    def __init__(self, resource_type: str, resource_id: Any):
        message = f"{resource_type} with ID {resource_id} not found"
        super().__init__(
            message,
            code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource_type": resource_type, "resource_id": str(resource_id)},
        )


class ConflictError(ReconixException):

    def __init__(self, message: str, resource_type: str | None = None):
        super().__init__(
            message,
            code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details={"resource_type": resource_type} if resource_type else {},
        )


class RateLimitError(ReconixException):

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


class AccountLockedError(ReconixException):

    def __init__(
        self,
        message: str = "Account is temporarily locked",
        unlock_time: str | None = None,
    ):
        details = {}
        if unlock_time:
            details["unlock_time"] = unlock_time
        super().__init__(
            message,
            code="ACCOUNT_LOCKED",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class ExternalAPIError(ReconixException):

    def __init__(
        self,
        api_name: str,
        message: str = "External API call failed",
        status_code: int = status.HTTP_502_BAD_GATEWAY,
    ):
        super().__init__(
            message,
            code="EXTERNAL_API_ERROR",
            status_code=status_code,
            details={"api_name": api_name},
        )


class IDORError(ReconixException):

    def __init__(self, message: str = "Access denied to this resource"):
        super().__init__(
            message,
            code="IDOR_VIOLATION",
            status_code=status.HTTP_403_FORBIDDEN,
        )
