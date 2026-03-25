import pytest
from fast_api.validators.nigerian import NigerianValidators


class TestValidateNIN:

    def test_validate_nin_valid(self):
        is_valid, error = NigerianValidators.validate_nin("12345678901")
        assert is_valid is True
        assert error == ""

    def test_validate_nin_valid_all_zeros(self):
        is_valid, error = NigerianValidators.validate_nin("00000000000")
        assert is_valid is True

    def test_validate_nin_invalid_too_short(self):
        is_valid, error = NigerianValidators.validate_nin("1234567890")
        assert is_valid is False
        assert "11 digits" in error

    def test_validate_nin_invalid_too_long(self):
        is_valid, error = NigerianValidators.validate_nin("123456789012")
        assert is_valid is False
        assert "11 digits" in error

    def test_validate_nin_invalid_non_numeric(self):
        is_valid, error = NigerianValidators.validate_nin("1234567890a")
        assert is_valid is False

    def test_validate_nin_invalid_with_spaces(self):
        is_valid, error = NigerianValidators.validate_nin("123 456 7890")
        assert is_valid is False

    def test_validate_nin_empty(self):
        is_valid, error = NigerianValidators.validate_nin("")
        assert is_valid is False
        assert "cannot be empty" in error


class TestValidateBVN:

    def test_validate_bvn_valid(self):
        is_valid, error = NigerianValidators.validate_bvn("22345678901")
        assert is_valid is True
        assert error == ""

    def test_validate_bvn_invalid_too_short(self):
        is_valid, error = NigerianValidators.validate_bvn("1234567890")
        assert is_valid is False
        assert "11 digits" in error

    def test_validate_bvn_invalid_too_long(self):
        is_valid, error = NigerianValidators.validate_bvn("123456789012")
        assert is_valid is False

    def test_validate_bvn_invalid_alpha(self):
        is_valid, error = NigerianValidators.validate_bvn("abcdefghijk")
        assert is_valid is False

    def test_validate_bvn_empty(self):
        is_valid, error = NigerianValidators.validate_bvn("")
        assert is_valid is False
        assert "cannot be empty" in error


class TestValidateMSISDN:

    def test_validate_msisdn_valid_international(self):
        is_valid, error = NigerianValidators.validate_msisdn("+2347012345678")
        assert is_valid is True
        assert error == ""

    def test_validate_msisdn_valid_international_8(self):
        is_valid, error = NigerianValidators.validate_msisdn("+2348012345678")
        assert is_valid is True

    def test_validate_msisdn_valid_international_9(self):
        is_valid, error = NigerianValidators.validate_msisdn("+2349012345678")
        assert is_valid is True

    def test_validate_msisdn_valid_local(self):
        is_valid, error = NigerianValidators.validate_msisdn("07012345678")
        assert is_valid is True
        assert error == ""

    def test_validate_msisdn_valid_without_plus(self):
        is_valid, error = NigerianValidators.validate_msisdn("2347012345678")
        assert is_valid is True

    def test_validate_msisdn_invalid_wrong_prefix(self):
        is_valid, error = NigerianValidators.validate_msisdn("+2346012345678")
        assert is_valid is False

    def test_validate_msisdn_invalid_too_short(self):
        is_valid, error = NigerianValidators.validate_msisdn("+234701234567")
        assert is_valid is False

    def test_validate_msisdn_invalid_alpha(self):
        is_valid, error = NigerianValidators.validate_msisdn("+234abc")
        assert is_valid is False

    def test_validate_msisdn_invalid_us_number(self):
        is_valid, error = NigerianValidators.validate_msisdn("+12125551234")
        assert is_valid is False

    def test_validate_msisdn_empty(self):
        is_valid, error = NigerianValidators.validate_msisdn("")
        assert is_valid is False
        assert "cannot be empty" in error


class TestNormalizeMSISDN:

    def test_normalize_msisdn_international(self):
        result = NigerianValidators.normalize_msisdn("+2347012345678")
        assert result == "+2347012345678"

    def test_normalize_msisdn_without_plus(self):
        result = NigerianValidators.normalize_msisdn("2347012345678")
        assert result == "+2347012345678"

    def test_normalize_msisdn_local(self):
        result = NigerianValidators.normalize_msisdn("07012345678")
        assert result == "+2347012345678"

    def test_normalize_msisdn_no_prefix(self):
        result = NigerianValidators.normalize_msisdn("7012345678")
        assert result == "7012345678"

    def test_normalize_msisdn_strips_whitespace(self):
        result = NigerianValidators.normalize_msisdn("  07012345678  ")
        assert result == "+2347012345678"


class TestValidateIMSI:

    def test_validate_imsi_valid(self):
        is_valid, error = NigerianValidators.validate_imsi("621234567890123")
        assert is_valid is True
        assert error == ""

    def test_validate_imsi_invalid_too_short(self):
        is_valid, error = NigerianValidators.validate_imsi("62123456789012")
        assert is_valid is False
        assert "15 digits" in error

    def test_validate_imsi_invalid_too_long(self):
        is_valid, error = NigerianValidators.validate_imsi("6212345678901234")
        assert is_valid is False

    def test_validate_imsi_invalid_alpha(self):
        is_valid, error = NigerianValidators.validate_imsi("62123456789012a")
        assert is_valid is False

    def test_validate_imsi_empty(self):
        is_valid, error = NigerianValidators.validate_imsi("")
        assert is_valid is False
        assert "cannot be empty" in error


class TestValidateSIMSerial:

    def test_validate_sim_serial_valid(self):
        is_valid, error = NigerianValidators.validate_sim_serial("89234567890123456789")
        assert is_valid is True
        assert error == ""

    def test_validate_sim_serial_valid_short(self):
        is_valid, error = NigerianValidators.validate_sim_serial("A")
        assert is_valid is True

    def test_validate_sim_serial_valid_max_length(self):
        is_valid, error = NigerianValidators.validate_sim_serial("A" * 50)
        assert is_valid is True

    def test_validate_sim_serial_empty(self):
        is_valid, error = NigerianValidators.validate_sim_serial("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_validate_sim_serial_too_long(self):
        is_valid, error = NigerianValidators.validate_sim_serial("A" * 51)
        assert is_valid is False
        assert "between 1 and 50" in error


class TestValidatePhoneNumber:

    def test_validate_phone_number_valid(self):
        is_valid, error = NigerianValidators.validate_phone_number("07012345678")
        assert is_valid is True

    def test_validate_phone_number_invalid_international(self):
        is_valid, error = NigerianValidators.validate_phone_number("+2347012345678")
        assert is_valid is False

    def test_validate_phone_number_invalid_prefix(self):
        is_valid, error = NigerianValidators.validate_phone_number("05012345678")
        assert is_valid is False

    def test_validate_phone_number_empty(self):
        is_valid, error = NigerianValidators.validate_phone_number("")
        assert is_valid is False
        assert "cannot be empty" in error
