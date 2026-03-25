import pytest
from fast_api.services.audit_service import _mask_audit_value


class TestAuditPIIMasking:

    def test_password_redacted(self):
        result = _mask_audit_value({"password": "secret123", "name": "Test"})
        assert result["password"] == "[REDACTED]"
        assert result["name"] == "Test"

    def test_hashed_password_redacted(self):
        result = _mask_audit_value({"hashed_password": "$2b$12$xxx"})
        assert result["hashed_password"] == "[REDACTED]"

    def test_token_redacted(self):
        result = _mask_audit_value({"token": "eyJhbGciOiJ..."})
        assert result["token"] == "[REDACTED]"

    def test_api_key_redacted(self):
        result = _mask_audit_value({"api_key": "sk_live_xxx"})
        assert result["api_key"] == "[REDACTED]"

    def test_nin_redacted(self):
        result = _mask_audit_value({"nin": "12345678901"})
        assert result["nin"] == "[REDACTED]"

    def test_bvn_redacted(self):
        result = _mask_audit_value({"bvn": "12345678901"})
        assert result["bvn"] == "[REDACTED]"

    def test_previous_owner_nin_redacted(self):
        result = _mask_audit_value({"previous_owner_nin": "12345678901"})
        assert result["previous_owner_nin"] == "[REDACTED]"

    def test_eleven_digit_number_partially_masked(self):
        result = _mask_audit_value({"msisdn_value": "08012345678"})
        assert result["msisdn_value"] == "080****5678"

    def test_nested_pii_redacted(self):
        result = _mask_audit_value({
            "user": {"password": "secret", "email": "test@example.com"}
        })
        assert result["user"]["password"] == "[REDACTED]"
        assert result["user"]["email"] == "test@example.com"

    def test_none_input_returns_none(self):
        assert _mask_audit_value(None) is None

    def test_non_pii_values_preserved(self):
        result = _mask_audit_value({
            "action": "create",
            "status": "pending",
            "count": 42,
        })
        assert result["action"] == "create"
        assert result["status"] == "pending"
        assert result["count"] == 42

    def test_depth_limit_prevents_infinite_recursion(self):
        deep = {"a": {"b": {"c": {"d": {"e": {"f": {"password": "deep"}}}}}}}
        result = _mask_audit_value(deep)
        assert result is not None
