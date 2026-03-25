import os
import pytest

os.environ["FIELD_ENCRYPTION_KEY"] = "test-encryption-key-for-testing-only-32chars-min"

from fast_api.crypto import (
    encrypt_value,
    decrypt_value,
    reset_key,
    _xor_encrypt,
    EncryptedString,
)


class TestEncryptDecrypt:

    def setup_method(self):
        reset_key()

    def test_encrypt_produces_different_output(self):
        plaintext = "12345678901"
        encrypted = encrypt_value(plaintext)
        assert encrypted != plaintext

    def test_decrypt_reverses_encrypt(self):
        plaintext = "12345678901"
        encrypted = encrypt_value(plaintext)
        decrypted = decrypt_value(encrypted)
        assert decrypted == plaintext

    def test_roundtrip_various_strings(self):
        test_cases = [
            "12345678901",
            "+2347012345678",
            "621234567890123",
            "test@example.com",
            "short",
            "a" * 500,
        ]
        for text in test_cases:
            encrypted = encrypt_value(text)
            assert decrypt_value(encrypted) == text

    def test_encrypt_produces_different_ciphertexts(self):
        plaintext = "12345678901"
        ct1 = encrypt_value(plaintext)
        ct2 = encrypt_value(plaintext)
        assert ct1 != ct2

    def test_decrypt_tampered_ciphertext_raises(self):
        plaintext = "12345678901"
        encrypted = encrypt_value(plaintext)
        tampered = encrypted[:-4] + "XXXX"
        with pytest.raises(ValueError, match="Integrity check failed"):
            decrypt_value(tampered)

    def test_decrypt_short_ciphertext_raises(self):
        with pytest.raises(ValueError, match="Invalid encrypted value"):
            decrypt_value("dG9vc2hvcnQ=")

    def test_empty_string_returns_empty(self):
        assert encrypt_value("") == ""
        assert decrypt_value("") == ""

    def test_none_handling_in_empty(self):
        assert encrypt_value("") == ""
        assert decrypt_value("") == ""


class TestXorEncrypt:

    def setup_method(self):
        reset_key()

    def test_xor_encrypt_is_reversible(self):
        import hashlib
        key = hashlib.sha256(b"test-key").digest()
        iv = b"\x00" * 16
        data = b"hello world test"
        encrypted = _xor_encrypt(data, key, iv)
        decrypted = _xor_encrypt(encrypted, key, iv)
        assert decrypted == data


class TestResetKey:

    def test_reset_clears_cache(self):
        encrypt_value("test")
        reset_key()
        encrypt_value("test2")


class TestEncryptedStringType:

    def setup_method(self):
        reset_key()

    def test_process_bind_param_encrypts(self):
        col = EncryptedString()
        result = col.process_bind_param("12345678901", None)
        assert result != "12345678901"
        assert result is not None

    def test_process_result_value_decrypts(self):
        col = EncryptedString()
        encrypted = encrypt_value("12345678901")
        result = col.process_result_value(encrypted, None)
        assert result == "12345678901"

    def test_process_bind_param_none(self):
        col = EncryptedString()
        assert col.process_bind_param(None, None) is None

    def test_process_result_value_none(self):
        col = EncryptedString()
        assert col.process_result_value(None, None) is None

    def test_roundtrip_through_type(self):
        col = EncryptedString()
        original = "+2347012345678"
        bound = col.process_bind_param(original, None)
        result = col.process_result_value(bound, None)
        assert result == original
