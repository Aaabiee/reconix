import pytest
from fast_api.middleware.sentry_integration import _scrub_event, _scrub_dict, init_sentry


class TestSentryScrubbing:

    def test_scrub_dict_redacts_sensitive_keys(self):
        data = {
            "email": "user@example.com",
            "password": "secret123",
            "token": "eyJ...",
            "name": "Test User",
        }
        result = _scrub_dict(data)
        assert result["email"] == "user@example.com"
        assert result["password"] == "[REDACTED]"
        assert result["token"] == "[REDACTED]"
        assert result["name"] == "Test User"

    def test_scrub_dict_handles_nested(self):
        data = {
            "user": {
                "email": "test@example.com",
                "api_key": "sk_live_abc123",
            }
        }
        result = _scrub_dict(data)
        assert result["user"]["api_key"] == "[REDACTED]"
        assert result["user"]["email"] == "test@example.com"

    def test_scrub_dict_truncates_deep_nesting(self):
        data = {"a": {"b": {"c": {"d": {"e": {"f": {"g": "deep"}}}}}}}
        result = _scrub_dict(data, depth=4)
        assert result["a"]["b"]["_truncated"] is True

    def test_scrub_dict_redacts_pii_keys(self):
        data = {
            "nin": "12345678901",
            "bvn": "12345678901",
            "msisdn": "+2348012345678",
            "imsi": "621200000000001",
        }
        result = _scrub_dict(data)
        assert result["nin"] == "[REDACTED]"
        assert result["bvn"] == "[REDACTED]"
        assert result["msisdn"] == "[REDACTED]"
        assert result["imsi"] == "[REDACTED]"

    def test_scrub_event_redacts_headers(self):
        event = {
            "request": {
                "headers": {
                    "Authorization": "Bearer eyJ...",
                    "Content-Type": "application/json",
                    "Cookie": "session=abc123",
                },
                "data": {"password": "secret"},
            }
        }
        result = _scrub_event(event, {})
        assert result["request"]["headers"]["Authorization"] == "[REDACTED]"
        assert result["request"]["headers"]["Content-Type"] == "application/json"
        assert result["request"]["headers"]["Cookie"] == "[REDACTED]"
        assert result["request"]["data"]["password"] == "[REDACTED]"

    def test_scrub_event_redacts_cookies(self):
        event = {
            "request": {
                "headers": {},
                "cookies": "session=abc; token=xyz",
            }
        }
        result = _scrub_event(event, {})
        assert result["request"]["cookies"] == "[REDACTED]"

    def test_scrub_event_no_request_key(self):
        event = {"level": "error", "message": "test"}
        result = _scrub_event(event, {})
        assert result == event

    def test_init_sentry_without_dsn(self):
        result = init_sentry(dsn="", environment="testing")
        assert result is False
