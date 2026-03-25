import pytest
from fastapi import status
from fast_api.exceptions import (
    ReconixException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    ConflictError,
    RateLimitError,
    AccountLockedError,
    ExternalAPIError,
    IDORError,
)
from fast_api.exceptions.handlers import to_http_exception


class TestValidationError:

    def test_validation_error_status_code(self):
        exc = ValidationError("Field is invalid")
        assert exc.status_code == 422

    def test_validation_error_code(self):
        exc = ValidationError("Field is invalid")
        assert exc.code == "VALIDATION_ERROR"

    def test_validation_error_message(self):
        exc = ValidationError("email is required")
        assert exc.message == "email is required"

    def test_validation_error_with_details(self):
        details = {"field": "email", "constraint": "required"}
        exc = ValidationError("Validation failed", details=details)
        assert exc.details == details

    def test_validation_error_without_details(self):
        exc = ValidationError("Validation failed")
        assert exc.details == {}


class TestAuthenticationError:

    def test_authentication_error_defaults(self):
        exc = AuthenticationError()
        assert exc.message == "Authentication failed"
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc.code == "AUTHENTICATION_ERROR"

    def test_authentication_error_custom_message(self):
        exc = AuthenticationError("Token expired")
        assert exc.message == "Token expired"
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthorizationError:

    def test_authorization_error_defaults(self):
        exc = AuthorizationError()
        assert exc.message == "Insufficient permissions"
        assert exc.status_code == status.HTTP_403_FORBIDDEN
        assert exc.code == "AUTHORIZATION_ERROR"

    def test_authorization_error_with_role(self):
        exc = AuthorizationError("Admin only", required_role="admin")
        assert exc.details["required_role"] == "admin"


class TestResourceNotFoundError:

    def test_resource_not_found_message_format(self):
        exc = ResourceNotFoundError("User", 42)
        assert exc.message == "User with ID 42 not found"
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.code == "RESOURCE_NOT_FOUND"

    def test_resource_not_found_details(self):
        exc = ResourceNotFoundError("RecycledSIM", "abc-123")
        assert exc.details["resource_type"] == "RecycledSIM"
        assert exc.details["resource_id"] == "abc-123"

    def test_resource_not_found_integer_id(self):
        exc = ResourceNotFoundError("DelinkRequest", 99)
        assert exc.details["resource_id"] == "99"


class TestConflictError:

    def test_conflict_error_basic(self):
        exc = ConflictError("Email already exists")
        assert exc.status_code == status.HTTP_409_CONFLICT
        assert exc.code == "CONFLICT"

    def test_conflict_error_with_resource_type(self):
        exc = ConflictError("Duplicate entry", resource_type="User")
        assert exc.details["resource_type"] == "User"


class TestRateLimitError:

    def test_rate_limit_error_defaults(self):
        exc = RateLimitError()
        assert exc.message == "Rate limit exceeded"
        assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_rate_limit_error_custom_message(self):
        exc = RateLimitError("Too many login attempts")
        assert exc.message == "Too many login attempts"


class TestAccountLockedError:

    def test_account_locked_defaults(self):
        exc = AccountLockedError()
        assert exc.message == "Account is temporarily locked"
        assert exc.status_code == status.HTTP_403_FORBIDDEN
        assert exc.code == "ACCOUNT_LOCKED"

    def test_account_locked_with_unlock_time(self):
        exc = AccountLockedError(unlock_time="2025-01-01T12:00:00Z")
        assert exc.details["unlock_time"] == "2025-01-01T12:00:00Z"


class TestExternalAPIError:

    def test_external_api_error(self):
        exc = ExternalAPIError("NIMC")
        assert exc.status_code == status.HTTP_502_BAD_GATEWAY
        assert exc.details["api_name"] == "NIMC"

    def test_external_api_error_custom_status(self):
        exc = ExternalAPIError("NIBSS", status_code=504)
        assert exc.status_code == 504


class TestIDORError:

    def test_idor_error_defaults(self):
        exc = IDORError()
        assert exc.message == "Access denied to this resource"
        assert exc.status_code == status.HTTP_403_FORBIDDEN
        assert exc.code == "IDOR_VIOLATION"


class TestToHTTPException:

    def test_to_http_exception_preserves_details(self):
        exc = ValidationError("Bad input", details={"field": "email"})
        http_exc = to_http_exception(exc)
        assert http_exc.status_code == 422
        assert http_exc.detail["code"] == "VALIDATION_ERROR"
        assert http_exc.detail["message"] == "Bad input"
        assert http_exc.detail["details"]["field"] == "email"

    def test_to_http_exception_auth_error(self):
        exc = AuthenticationError("Token invalid")
        http_exc = to_http_exception(exc)
        assert http_exc.status_code == 401
        assert http_exc.detail["code"] == "AUTHENTICATION_ERROR"

    def test_to_http_exception_not_found(self):
        exc = ResourceNotFoundError("SIM", 5)
        http_exc = to_http_exception(exc)
        assert http_exc.status_code == 404
        assert http_exc.detail["message"] == "SIM with ID 5 not found"

    def test_to_http_exception_base_exception(self):
        exc = ReconixException("Server error")
        http_exc = to_http_exception(exc)
        assert http_exc.status_code == 500
        assert http_exc.detail["code"] == "INTERNAL_ERROR"
