#!/usr/bin/env python3
"""Uptime monitoring health check poller.

Polls the /health endpoint at a configurable interval and logs results.
Designed to run as a cron job or systemd timer for external uptime monitoring.

Usage:
    python scripts/health_check.py --url http://localhost:8000/health --interval 30
    python scripts/health_check.py --url https://api.reconix.ng/health --webhook https://hooks.slack.com/...
"""

import argparse
import json
import logging
import sys
import time
import urllib.request
import urllib.error

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("reconix.healthcheck")

TIMEOUT_SECONDS = 10


def check_health(url: str) -> dict:
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "Reconix-HealthCheck/1.0")
        start = time.monotonic()
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            duration_ms = (time.monotonic() - start) * 1000
            body = json.loads(resp.read().decode("utf-8"))
            return {
                "status": "up",
                "http_status": resp.status,
                "response_ms": round(duration_ms, 2),
                "details": body,
            }
    except urllib.error.HTTPError as e:
        return {
            "status": "degraded",
            "http_status": e.code,
            "response_ms": 0,
            "error": str(e),
        }
    except urllib.error.URLError as e:
        return {
            "status": "down",
            "http_status": 0,
            "response_ms": 0,
            "error": str(e.reason),
        }
    except Exception as e:
        return {
            "status": "down",
            "http_status": 0,
            "response_ms": 0,
            "error": str(e),
        }


def send_webhook_alert(webhook_url: str, result: dict) -> None:
    if not webhook_url:
        return

    payload = json.dumps({
        "text": f"Reconix Health Check: {result['status'].upper()} "
                f"(HTTP {result['http_status']}, {result['response_ms']}ms)",
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS)
    except Exception as e:
        logger.error(f"Webhook alert failed: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconix uptime health check poller")
    parser.add_argument(
        "--url",
        default="http://localhost:8000/health",
        help="Health endpoint URL",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=0,
        help="Polling interval in seconds (0 = run once)",
    )
    parser.add_argument(
        "--webhook",
        default="",
        help="Webhook URL for alerting on failures",
    )
    parser.add_argument(
        "--exit-on-failure",
        action="store_true",
        help="Exit with code 1 on health check failure",
    )
    args = parser.parse_args()

    while True:
        result = check_health(args.url)

        if result["status"] == "up":
            logger.info(
                f"HEALTHY — HTTP {result['http_status']} in {result['response_ms']}ms "
                f"db={result['details'].get('database', 'unknown')}"
            )
        else:
            logger.error(f"UNHEALTHY — {result['status']}: {result.get('error', '')}")
            send_webhook_alert(args.webhook, result)
            if args.exit_on_failure and args.interval == 0:
                sys.exit(1)

        if args.interval <= 0:
            break

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
