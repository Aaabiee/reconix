import pytest
from fast_api.middleware.metrics import MetricsCollector


class TestMetricsCollector:

    def setup_method(self):
        collector = MetricsCollector()
        collector.reset()

    def test_singleton_instance(self):
        c1 = MetricsCollector()
        c2 = MetricsCollector()
        assert c1 is c2

    def test_record_request_increments_count(self):
        c = MetricsCollector()
        c.record_request("GET", "/api/v1/sims", 200, 0.05)
        assert c.request_count["GET:/api/v1/sims:200"] == 1

    def test_record_request_accumulates_latency(self):
        c = MetricsCollector()
        c.record_request("GET", "/api/v1/sims", 200, 0.1)
        c.record_request("GET", "/api/v1/sims", 200, 0.2)
        assert c.request_latency_sum["GET:/api/v1/sims"] == pytest.approx(0.3)
        assert c.request_latency_count["GET:/api/v1/sims"] == 2

    def test_record_request_tracks_errors_4xx(self):
        c = MetricsCollector()
        c.record_request("POST", "/api/v1/auth/login", 401, 0.01)
        assert c.error_count["POST:/api/v1/auth/login:401"] == 1

    def test_record_request_tracks_errors_5xx(self):
        c = MetricsCollector()
        c.record_request("GET", "/api/v1/sims", 500, 0.01)
        assert c.error_count["GET:/api/v1/sims:500"] == 1

    def test_record_request_no_error_for_2xx(self):
        c = MetricsCollector()
        c.record_request("GET", "/api/v1/sims", 200, 0.01)
        assert len(c.error_count) == 0

    def test_increment_active(self):
        c = MetricsCollector()
        c.increment_active()
        assert c.active_requests == 1
        c.increment_active()
        assert c.active_requests == 2

    def test_decrement_active(self):
        c = MetricsCollector()
        c.increment_active()
        c.increment_active()
        c.decrement_active()
        assert c.active_requests == 1

    def test_decrement_active_not_below_zero(self):
        c = MetricsCollector()
        c.decrement_active()
        assert c.active_requests == 0
        c.decrement_active()
        assert c.active_requests == 0

    def test_get_metrics_prometheus_format(self):
        c = MetricsCollector()
        c.record_request("GET", "/api/v1/sims", 200, 0.05)
        metrics = c.get_metrics()
        assert "# HELP reconix_http_requests_total" in metrics
        assert "# TYPE reconix_http_requests_total counter" in metrics
        assert "reconix_http_requests_total" in metrics
        assert "reconix_http_active_requests" in metrics
        assert "reconix_http_request_duration_seconds" in metrics

    def test_get_metrics_includes_error_section(self):
        c = MetricsCollector()
        c.record_request("GET", "/fail", 500, 0.01)
        metrics = c.get_metrics()
        assert "reconix_http_errors_total" in metrics

    def test_normalize_path_replaces_numeric_ids(self):
        assert MetricsCollector._normalize_path("/api/v1/sims/42") == "/api/v1/sims/{id}"

    def test_normalize_path_preserves_non_numeric(self):
        assert MetricsCollector._normalize_path("/api/v1/sims") == "/api/v1/sims"

    def test_normalize_path_multiple_ids(self):
        result = MetricsCollector._normalize_path("/api/v1/sims/42/linkages/99")
        assert result == "/api/v1/sims/{id}/linkages/{id}"

    def test_reset_clears_all_counters(self):
        c = MetricsCollector()
        c.record_request("GET", "/test", 200, 0.1)
        c.increment_active()
        c.reset()
        assert len(c.request_count) == 0
        assert len(c.request_latency_sum) == 0
        assert len(c.error_count) == 0
        assert c.active_requests == 0
