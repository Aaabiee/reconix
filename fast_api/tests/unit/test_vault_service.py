import pytest
import os
from fast_api.services.vault_service import VaultService


class TestVaultServiceFallback:

    def test_connect_without_hvac_returns_false(self):
        service = VaultService(vault_url="", vault_token="")
        result = service.connect()
        assert result is False
        assert service.is_connected is False

    def test_env_fallback_reads_env_vars(self, monkeypatch):
        monkeypatch.setenv("RECONIX_DATABASE_URL", "postgresql://test:pass@db/reconix")
        service = VaultService(vault_url="", vault_token="")
        result = service._env_fallback("reconix/database", "url")
        assert result == "postgresql://test:pass@db/reconix"

    def test_env_fallback_with_simple_key(self, monkeypatch):
        monkeypatch.setenv("RECONIX_AUTH_JWT_SECRET_KEY", "my-secret")
        service = VaultService(vault_url="", vault_token="")
        result = service._env_fallback("reconix/auth", "jwt_secret_key")
        assert result == "my-secret"

    def test_get_database_url_falls_back_to_env(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host/db")
        service = VaultService(vault_url="", vault_token="")
        result = service.get_database_url()
        assert result == "postgresql://user:pass@host/db"

    def test_get_jwt_secret_falls_back_to_env(self, monkeypatch):
        monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-key-at-least-32-chars!")
        service = VaultService(vault_url="", vault_token="")
        result = service.get_jwt_secret()
        assert result == "test-jwt-secret-key-at-least-32-chars!"

    def test_get_encryption_key_falls_back_to_env(self, monkeypatch):
        monkeypatch.setenv("FIELD_ENCRYPTION_KEY", "test-enc-key-32chars-minimum-ok!")
        service = VaultService(vault_url="", vault_token="")
        result = service.get_encryption_key()
        assert result == "test-enc-key-32chars-minimum-ok!"

    def test_get_secret_without_connection(self):
        service = VaultService(vault_url="", vault_token="")
        result = service.get_secret("nonexistent/path")
        assert result is None

    def test_is_connected_default_false(self):
        service = VaultService()
        assert service.is_connected is False

    def test_connect_without_url_returns_false(self):
        service = VaultService(vault_url="", vault_token="some-token")
        result = service.connect()
        assert result is False

    def test_connect_without_token_returns_false(self):
        service = VaultService(vault_url="http://vault:8200", vault_token="")
        result = service.connect()
        assert result is False
