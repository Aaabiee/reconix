from __future__ import annotations

import time
import threading
from collections import defaultdict
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, PlainTextResponse


class MetricsCollector:

    _instance = None
    _lock = threading.Lock()

    def __new__(cls) -> MetricsCollector:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._lock_data = threading.Lock()
        self.request_count: dict[str, int] = defaultdict(int)
        self.request_latency_sum: dict[str, float] = defaultdict(float)
        self.request_latency_count: dict[str, int] = defaultdict(int)
        self.error_count: dict[str, int] = defaultdict(int)
        self.active_requests: int = 0

    def record_request(
        self, method: str, path: str, status_code: int, duration: float
    ) -> None:
        normalized_path = self._normalize_path(path)
        key = f'{method}:{normalized_path}'
        status_key = f'{method}:{normalized_path}:{status_code}'

        with self._lock_data:
            self.request_count[status_key] += 1
            self.request_latency_sum[key] += duration
            self.request_latency_count[key] += 1
            if status_code >= 400:
                self.error_count[status_key] += 1

    def increment_active(self) -> None:
        with self._lock_data:
            self.active_requests += 1

    def decrement_active(self) -> None:
        with self._lock_data:
            self.active_requests = max(0, self.active_requests - 1)

    def get_metrics(self) -> str:
        lines: list[str] = []

        lines.append("# HELP reconix_http_requests_total Total HTTP requests")
        lines.append("# TYPE reconix_http_requests_total counter")
        with self._lock_data:
            for key, count in sorted(self.request_count.items()):
                method, path, status = key.rsplit(":", 2)
                lines.append(
                    f'reconix_http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}'
                )

        lines.append("")
        lines.append("# HELP reconix_http_request_duration_seconds HTTP request latency")
        lines.append("# TYPE reconix_http_request_duration_seconds summary")
        with self._lock_data:
            for key in sorted(self.request_latency_count.keys()):
                method, path = key.split(":", 1)
                total = self.request_latency_sum[key]
                count = self.request_latency_count[key]
                lines.append(
                    f'reconix_http_request_duration_seconds_sum{{method="{method}",path="{path}"}} {total:.6f}'
                )
                lines.append(
                    f'reconix_http_request_duration_seconds_count{{method="{method}",path="{path}"}} {count}'
                )

        lines.append("")
        lines.append("# HELP reconix_http_errors_total Total HTTP errors (4xx/5xx)")
        lines.append("# TYPE reconix_http_errors_total counter")
        with self._lock_data:
            for key, count in sorted(self.error_count.items()):
                method, path, status = key.rsplit(":", 2)
                lines.append(
                    f'reconix_http_errors_total{{method="{method}",path="{path}",status="{status}"}} {count}'
                )

        lines.append("")
        lines.append("# HELP reconix_http_active_requests Current active requests")
        lines.append("# TYPE reconix_http_active_requests gauge")
        with self._lock_data:
            lines.append(f"reconix_http_active_requests {self.active_requests}")

        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _normalize_path(path: str) -> str:
        parts = path.rstrip("/").split("/")
        normalized = []
        for part in parts:
            if part.isdigit():
                normalized.append("{id}")
            else:
                normalized.append(part)
        return "/".join(normalized)

    def reset(self) -> None:
        with self._lock_data:
            self.request_count.clear()
            self.request_latency_sum.clear()
            self.request_latency_count.clear()
            self.error_count.clear()
            self.active_requests = 0


class MetricsMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path == "/metrics":
            return await call_next(request)

        collector = MetricsCollector()
        collector.increment_active()
        start = time.monotonic()

        try:
            response = await call_next(request)
            duration = time.monotonic() - start
            collector.record_request(
                request.method, request.url.path, response.status_code, duration
            )
            return response
        finally:
            collector.decrement_active()


def metrics_endpoint() -> PlainTextResponse:
    collector = MetricsCollector()
    return PlainTextResponse(
        content=collector.get_metrics(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
