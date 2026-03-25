from __future__ import annotations

import hmac
import hashlib
import ipaddress
import logging
import httpx
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fast_api.db import BaseRepository
from fast_api.models.webhook import WebhookSubscription
from fast_api.exceptions import ValidationError, AuthenticationError

logger = logging.getLogger(__name__)

BLOCKED_HOSTS = frozenset({"localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal"})


def _is_safe_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""

        if hostname in BLOCKED_HOSTS:
            return False

        if parsed.scheme not in ("https", "http"):
            return False

        try:
            addr = ipaddress.ip_address(hostname)
            if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
                return False
        except ValueError:
            pass

        if hostname.endswith(".internal") or hostname.endswith(".local"):
            return False

        return True
    except Exception:
        return False


class SyncService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = BaseRepository(db, WebhookSubscription)

    async def dispatch_event(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        stmt = select(WebhookSubscription).where(
            WebhookSubscription.is_active == True
        )
        result = await self.db.execute(stmt)
        subscriptions = result.scalars().all()

        dispatched = 0
        failed = 0
        errors = []

        for sub in subscriptions:
            if sub.events and event_type not in sub.events:
                continue

            if not _is_safe_url(sub.callback_url):
                failed += 1
                errors.append({
                    "subscriber": sub.subscriber_name,
                    "error": "Callback URL blocked by SSRF protection",
                })
                logger.warning(f"SSRF blocked: {sub.subscriber_name} callback URL targets internal address")
                continue

            signature = self._generate_signature(payload, sub.secret_key)

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    await client.post(
                        sub.callback_url,
                        json={"event_type": event_type, "payload": payload},
                        headers={
                            "X-Webhook-Signature": signature,
                            "Content-Type": "application/json",
                        },
                    )

                await self.repository.update(
                    sub.id, {"last_triggered_at": datetime.now(timezone.utc)}
                )
                dispatched += 1

            except Exception as exc:
                failed += 1
                errors.append({
                    "subscriber": sub.subscriber_name,
                    "error": str(exc),
                })
                logger.warning(
                    f"Webhook dispatch failed for {sub.subscriber_name}: {exc}"
                )

        await self.db.commit()

        return {
            "event_type": event_type,
            "dispatched": dispatched,
            "failed": failed,
            "errors": errors if errors else None,
        }

    async def receive_update(
        self, source: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        if not source or not payload:
            raise ValidationError("source and payload are required")

        logger.info(f"Received update from {source}: event keys={list(payload.keys())}")

        return {
            "status": "accepted",
            "source": source,
            "received_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def validate_webhook_signature(
        payload: bytes, signature: str, secret: str
    ) -> bool:
        expected = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    @staticmethod
    def _generate_signature(payload: dict[str, Any], secret: str) -> str:
        import json
        payload_bytes = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hmac.new(
            secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()
