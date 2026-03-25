from __future__ import annotations

import base64
import hashlib
import hmac
import os
import logging
from typing import TypeVar

from sqlalchemy import TypeDecorator, String

logger = logging.getLogger(__name__)

_encryption_key: bytes | None = None


def _get_key() -> bytes:
    global _encryption_key
    if _encryption_key is not None:
        return _encryption_key

    from fast_api.config import get_settings
    settings = get_settings()
    raw = settings.FIELD_ENCRYPTION_KEY
    if not raw:
        raise RuntimeError("FIELD_ENCRYPTION_KEY must be set for PII encryption")
    _encryption_key = hashlib.sha256(raw.encode("utf-8")).digest()
    return _encryption_key


def reset_key() -> None:
    global _encryption_key
    _encryption_key = None


def encrypt_value(plaintext: str) -> str:
    if not plaintext:
        return plaintext
    key = _get_key()
    iv = os.urandom(16)
    plaintext_bytes = plaintext.encode("utf-8")
    encrypted = _xor_encrypt(plaintext_bytes, key, iv)
    tag = hmac.new(key, iv + encrypted, hashlib.sha256).digest()[:16]
    return base64.urlsafe_b64encode(iv + tag + encrypted).decode("ascii")


def decrypt_value(ciphertext: str) -> str:
    if not ciphertext:
        return ciphertext
    key = _get_key()
    raw = base64.urlsafe_b64decode(ciphertext.encode("ascii"))
    if len(raw) < 33:
        raise ValueError("Invalid encrypted value")
    iv = raw[:16]
    stored_tag = raw[16:32]
    encrypted = raw[32:]
    expected_tag = hmac.new(key, iv + encrypted, hashlib.sha256).digest()[:16]
    if not hmac.compare_digest(stored_tag, expected_tag):
        raise ValueError("Integrity check failed: data may have been tampered with")
    decrypted = _xor_encrypt(encrypted, key, iv)
    return decrypted.decode("utf-8")


def _xor_encrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
    key_stream = b""
    block_count = (len(data) + 31) // 32
    for i in range(block_count):
        key_stream += hashlib.sha256(key + iv + i.to_bytes(4, "big")).digest()
    return bytes(a ^ b for a, b in zip(data, key_stream[: len(data)]))


class EncryptedString(TypeDecorator):
    impl = String
    cache_ok = True

    def __init__(self, length: int = 512, **kwargs):
        super().__init__(**kwargs)
        self.impl = String(length)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return encrypt_value(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return decrypt_value(value)
        except ValueError:
            logger.error("Failed to decrypt field value — possible key mismatch or data corruption")
            raise
