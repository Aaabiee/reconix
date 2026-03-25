import json
import logging
import pytest
from fast_api.logging_config import (
    mask_pii,
    redact_dict,
    JSONFormatter,
    PIIMaskingFilter,
    configure_logging,
    SENSITIVE_KEYS,
)


class TestMaskPII:

    def test_masks_11_digit_nin(self):
        assert "***NIN/BVN***" in mask_pii("NIN is 12345678901")

    def test_masks_11_digit_bvn(self):
        assert "***NIN/BVN***" in mask_pii("BVN: 99887766554")

    def test_masks_msisdn_plus234(self):
        assert "***MSISDN***" in mask_pii("Phone +2347012345678")

    def test_masks_msisdn_local(self):
        assert "***MSISDN***" in mask_pii("Phone 07012345678")

    def test_masks_msisdn_234_no_plus(self):
        assert "***MSISDN***" in mask_pii("Phone 2347012345678")

    def test_masks_15_digit_imsi(self):
        assert "***IMSI***" in mask_pii("IMSI 621234567890123")

    def test_does_not_mask_normal_text(self):
        text = "This is a normal message with no PII"
        assert mask_pii(text) == text

    def test_does_not_mask_short_numbers(self):
        text = "Order 12345 confirmed"
        assert mask_pii(text) == text

    def test_masks_multiple_pii_in_one_string(self):
        text = "NIN 12345678901 phone +2347012345678"
        result = mask_pii(text)
        assert "***NIN/BVN***" in result
        assert "***MSISDN***" in result


class TestRedactDict:

    def test_redacts_password_key(self):
        data = {"password": "secret123", "name": "test"}
        result = redact_dict(data)
        assert result["password"] == "[REDACTED]"
        assert result["name"] == "test"

    def test_redacts_token_key(self):
        data = {"token": "abc.def.ghi"}
        result = redact_dict(data)
        assert result["token"] == "[REDACTED]"

    def test_redacts_api_key(self):
        data = {"api_key": "sk_live_123"}
        result = redact_dict(data)
        assert result["api_key"] == "[REDACTED]"

    def test_redacts_refresh_token(self):
        data = {"refresh_token": "rt_abc123"}
        result = redact_dict(data)
        assert result["refresh_token"] == "[REDACTED]"

    def test_masks_pii_in_string_values(self):
        data = {"message": "User NIN is 12345678901"}
        result = redact_dict(data)
        assert "***NIN/BVN***" in result["message"]

    def test_handles_nested_dicts(self):
        data = {"user": {"password": "secret", "name": "test"}}
        result = redact_dict(data)
        assert result["user"]["password"] == "[REDACTED]"
        assert result["user"]["name"] == "test"

    def test_stops_at_depth_5(self):
        data = {"a": {"b": {"c": {"d": {"e": {"f": {"g": "deep"}}}}}}}
        result = redact_dict(data)
        deep = result["a"]["b"]["c"]["d"]["e"]["f"]
        assert deep.get("_truncated") is True

    def test_masks_pii_in_list_string_values(self):
        data = {"phones": ["+2347012345678", "safe_value"]}
        result = redact_dict(data)
        assert "***MSISDN***" in result["phones"][0]
        assert result["phones"][1] == "safe_value"

    def test_handles_non_string_values(self):
        data = {"count": 42, "active": True}
        result = redact_dict(data)
        assert result["count"] == 42
        assert result["active"] is True

    def test_all_sensitive_keys_covered(self):
        for key in SENSITIVE_KEYS:
            data = {key: "some_value"}
            result = redact_dict(data)
            assert result[key] == "[REDACTED]", f"Key '{key}' was not redacted"


class TestJSONFormatter:

    def test_produces_valid_json(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            "test", logging.INFO, "", 0, "Test message", (), None
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert "timestamp" in parsed
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test"
        assert parsed["message"] == "Test message"

    def test_includes_request_id(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            "test", logging.INFO, "", 0, "msg", (), None
        )
        record.request_id = "req-123"
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["request_id"] == "req-123"

    def test_includes_extra_data(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            "test", logging.INFO, "", 0, "msg", (), None
        )
        record.extra_data = {"key": "value"}
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["data"]["key"] == "value"

    def test_masks_pii_in_message(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            "test", logging.INFO, "", 0, "NIN 12345678901", (), None
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert "***NIN/BVN***" in parsed["message"]

    def test_includes_exception_info(self):
        formatter = JSONFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys
            record = logging.LogRecord(
                "test", logging.ERROR, "", 0, "Error", (), sys.exc_info()
            )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["exception"]["type"] == "ValueError"


class TestPIIMaskingFilter:

    def test_masks_pii_in_msg(self):
        f = PIIMaskingFilter()
        record = logging.LogRecord(
            "test", logging.INFO, "", 0,
            "User NIN 12345678901", (), None
        )
        f.filter(record)
        assert "***NIN/BVN***" in record.msg

    def test_handles_tuple_args(self):
        f = PIIMaskingFilter()
        record = logging.LogRecord(
            "test", logging.INFO, "", 0,
            "Phone: %s", ("+2347012345678",), None
        )
        f.filter(record)
        assert "***MSISDN***" in record.args[0]

    def test_handles_dict_args(self):
        f = PIIMaskingFilter()
        record = logging.LogRecord(
            "test", logging.INFO, "", 0,
            "%(phone)s", None, None
        )
        record.args = {"phone": "+2347012345678"}
        f.filter(record)
        assert "***MSISDN***" in record.args["phone"]

    def test_returns_true(self):
        f = PIIMaskingFilter()
        record = logging.LogRecord(
            "test", logging.INFO, "", 0, "msg", (), None
        )
        assert f.filter(record) is True


class TestConfigureLogging:

    def test_configure_json_mode(self):
        configure_logging("INFO", json_output=True)
        root = logging.getLogger()
        assert len(root.handlers) > 0
        assert isinstance(root.handlers[-1].formatter, JSONFormatter)

    def test_configure_text_mode(self):
        configure_logging("INFO", json_output=False)
        root = logging.getLogger()
        assert len(root.handlers) > 0
        assert not isinstance(root.handlers[-1].formatter, JSONFormatter)

    def test_sets_log_level(self):
        configure_logging("DEBUG", json_output=False)
        root = logging.getLogger()
        assert root.level == logging.DEBUG
