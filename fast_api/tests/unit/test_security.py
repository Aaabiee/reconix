import pytest
from datetime import timedelta
from fast_api.auth.authlib.jwt_handler import JWTHandler
from fast_api.auth.authlib.password import PasswordManager
from fast_api.exceptions import AuthenticationError


class TestHashPassword:

    def test_hash_password(self):
        password = "testpassword123"
        hashed = PasswordManager.hash_password(password)
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")

    def test_hash_password_different_hashes(self):
        password = "testpassword123"
        hash1 = PasswordManager.hash_password(password)
        hash2 = PasswordManager.hash_password(password)
        assert hash1 != hash2

    def test_verify_password_correct(self):
        password = "testpassword123"
        hashed = PasswordManager.hash_password(password)
        assert PasswordManager.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        password = "testpassword123"
        hashed = PasswordManager.hash_password(password)
        assert PasswordManager.verify_password("wrongpassword1", hashed) is False

    def test_password_too_short_raises(self):
        with pytest.raises(ValueError, match="must be at least"):
            PasswordManager.hash_password("short")

    def test_password_exactly_min_length(self):
        password = "a" * 12
        hashed = PasswordManager.hash_password(password)
        assert PasswordManager.verify_password(password, hashed) is True


class TestAccessToken:

    def test_create_access_token_contains_claims(self):
        data = {"sub": "42", "email": "user@example.com", "role": "admin"}
        token = JWTHandler.create_access_token(data)
        payload = JWTHandler.verify_token(token, expected_type="access")
        assert payload["sub"] == "42"
        assert payload["email"] == "user@example.com"
        assert payload["role"] == "admin"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_access_token_custom_expiry(self):
        data = {"sub": "1"}
        token = JWTHandler.create_access_token(
            data, expires_delta=timedelta(minutes=5)
        )
        payload = JWTHandler.verify_token(token)
        assert payload["sub"] == "1"

    def test_verify_access_token_valid(self):
        data = {"sub": "1", "email": "test@example.com"}
        token = JWTHandler.create_access_token(data)
        payload = JWTHandler.verify_token(token)
        assert payload["sub"] == "1"
        assert payload["email"] == "test@example.com"


class TestRefreshToken:

    def test_create_refresh_token_has_refresh_type(self):
        data = {"sub": "1", "email": "test@example.com"}
        token = JWTHandler.create_refresh_token(data)
        payload = JWTHandler.verify_token(token, expected_type="refresh")
        assert payload["type"] == "refresh"
        assert "jti" in payload
        assert "exp" in payload

    def test_refresh_token_has_unique_jti(self):
        data = {"sub": "1"}
        token1 = JWTHandler.create_refresh_token(data)
        token2 = JWTHandler.create_refresh_token(data)
        payload1 = JWTHandler.verify_token(token1, expected_type="refresh")
        payload2 = JWTHandler.verify_token(token2, expected_type="refresh")
        assert payload1["jti"] != payload2["jti"]


class TestVerifyToken:

    def test_verify_token_expired_raises(self):
        data = {"sub": "1"}
        token = JWTHandler.create_access_token(
            data, expires_delta=timedelta(seconds=-1)
        )
        with pytest.raises(AuthenticationError, match="expired"):
            JWTHandler.verify_token(token)

    def test_verify_token_wrong_type_raises(self):
        data = {"sub": "1"}
        token = JWTHandler.create_access_token(data)
        with pytest.raises(AuthenticationError, match="Expected refresh token"):
            JWTHandler.verify_token(token, expected_type="refresh")

    def test_verify_token_invalid_string(self):
        with pytest.raises(AuthenticationError, match="Invalid token"):
            JWTHandler.verify_token("not.a.valid.jwt")

    def test_verify_token_empty_string(self):
        with pytest.raises(AuthenticationError):
            JWTHandler.verify_token("")

    def test_verify_refresh_as_access_raises(self):
        data = {"sub": "1"}
        token = JWTHandler.create_refresh_token(data)
        with pytest.raises(AuthenticationError, match="Expected access token"):
            JWTHandler.verify_token(token, expected_type="access")


class TestAPIKey:

    def test_hash_api_key(self):
        key = "sk_test_1234567890abcdef"
        hashed = PasswordManager.hash_api_key(key)
        assert hashed != key
        assert len(hashed) > 0

    def test_verify_api_key_correct(self):
        key = "sk_test_1234567890abcdef"
        hashed = PasswordManager.hash_api_key(key)
        assert PasswordManager.verify_api_key(key, hashed) is True

    def test_verify_api_key_incorrect(self):
        key = "sk_test_1234567890abcdef"
        hashed = PasswordManager.hash_api_key(key)
        assert PasswordManager.verify_api_key("wrong_key_here_!", hashed) is False

    def test_generate_api_key_uniqueness(self):
        key1 = PasswordManager.generate_api_key()
        key2 = PasswordManager.generate_api_key()
        assert key1 != key2
        assert len(key1) > 32
        assert len(key2) > 32

    def test_generate_api_key_is_url_safe(self):
        key = PasswordManager.generate_api_key()
        safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
        assert all(c in safe_chars for c in key)
