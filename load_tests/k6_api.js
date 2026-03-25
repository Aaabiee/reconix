import http from "k6/http";
import { check, sleep, group } from "k6";
import { Rate, Trend } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const ACCESS_TOKEN = __ENV.ACCESS_TOKEN || "";

const errorRate = new Rate("errors");
const listSimsDuration = new Trend("list_sims_duration", true);
const dashboardDuration = new Trend("dashboard_duration", true);
const healthDuration = new Trend("health_duration", true);

export const options = {
  scenarios: {
    read_heavy: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "30s", target: 20 },
        { duration: "2m", target: 50 },
        { duration: "1m", target: 100 },
        { duration: "2m", target: 100 },
        { duration: "30s", target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<1000", "p(99)<3000"],
    errors: ["rate<0.05"],
    list_sims_duration: ["p(95)<1500"],
    dashboard_duration: ["p(95)<2000"],
    health_duration: ["p(99)<500"],
  },
};

const headers = {
  "Content-Type": "application/json",
  Accept: "application/json",
  Authorization: `Bearer ${ACCESS_TOKEN}`,
};

export default function () {
  group("Health Check", function () {
    const res = http.get(`${BASE_URL}/health`, {
      tags: { name: "health" },
    });
    healthDuration.add(res.timings.duration);
    const ok = check(res, {
      "health status is 200": (r) => r.status === 200,
      "health response has status": (r) => {
        try {
          return JSON.parse(r.body).status !== undefined;
        } catch {
          return false;
        }
      },
    });
    errorRate.add(!ok);
  });

  group("List Recycled SIMs", function () {
    const page = Math.floor(Math.random() * 5);
    const res = http.get(
      `${BASE_URL}/api/v1/recycled-sims?skip=${page * 50}&limit=50`,
      { headers, tags: { name: "list_sims" } }
    );
    listSimsDuration.add(res.timings.duration);
    const ok = check(res, {
      "list sims status is 200": (r) => r.status === 200,
      "list sims has items": (r) => {
        try {
          return JSON.parse(r.body).items !== undefined;
        } catch {
          return false;
        }
      },
      "list sims response time < 1.5s": (r) => r.timings.duration < 1500,
    });
    errorRate.add(!ok);
  });

  group("Dashboard Stats", function () {
    const res = http.get(`${BASE_URL}/api/v1/dashboard/stats`, {
      headers,
      tags: { name: "dashboard_stats" },
    });
    dashboardDuration.add(res.timings.duration);
    const ok = check(res, {
      "dashboard stats status is 200": (r) => r.status === 200,
      "dashboard stats response time < 2s": (r) => r.timings.duration < 2000,
    });
    errorRate.add(!ok);
  });

  group("Dashboard Trends", function () {
    const days = [7, 14, 30][Math.floor(Math.random() * 3)];
    const res = http.get(`${BASE_URL}/api/v1/dashboard/trends?days=${days}`, {
      headers,
      tags: { name: "dashboard_trends" },
    });
    const ok = check(res, {
      "dashboard trends status is 200": (r) => r.status === 200,
    });
    errorRate.add(!ok);
  });

  sleep(Math.random() * 2 + 0.5);
}

export function handleSummary(data) {
  return {
    stdout: JSON.stringify(
      {
        test: "api_load_test",
        timestamp: new Date().toISOString(),
        metrics: {
          http_req_duration_p95: data.metrics.http_req_duration?.values?.["p(95)"],
          http_req_duration_p99: data.metrics.http_req_duration?.values?.["p(99)"],
          list_sims_p95: data.metrics.list_sims_duration?.values?.["p(95)"],
          dashboard_p95: data.metrics.dashboard_duration?.values?.["p(95)"],
          error_rate: data.metrics.errors?.values?.rate,
          total_requests: data.metrics.http_reqs?.values?.count,
        },
      },
      null,
      2
    ),
  };
}
