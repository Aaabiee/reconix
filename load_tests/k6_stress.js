import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend, Counter } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const ACCESS_TOKEN = __ENV.ACCESS_TOKEN || "";

const errorRate = new Rate("errors");
const reqDuration = new Trend("req_duration", true);
const timeouts = new Counter("timeouts");

export const options = {
  scenarios: {
    stress: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "1m", target: 50 },
        { duration: "2m", target: 150 },
        { duration: "2m", target: 300 },
        { duration: "3m", target: 300 },
        { duration: "1m", target: 500 },
        { duration: "2m", target: 500 },
        { duration: "2m", target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<5000"],
    errors: ["rate<0.3"],
    http_req_failed: ["rate<0.3"],
  },
};

const headers = {
  "Content-Type": "application/json",
  Accept: "application/json",
  Authorization: `Bearer ${ACCESS_TOKEN}`,
};

const endpoints = [
  { method: "GET", path: "/health", auth: false },
  { method: "GET", path: "/api/v1/recycled-sims?skip=0&limit=10", auth: true },
  { method: "GET", path: "/api/v1/dashboard/stats", auth: true },
  { method: "GET", path: "/api/v1/dashboard/trends?days=7", auth: true },
  { method: "GET", path: "/api/v1/data-subject/privacy-policy", auth: false },
];

export default function () {
  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  const url = `${BASE_URL}${endpoint.path}`;
  const reqHeaders = endpoint.auth ? headers : { Accept: "application/json" };

  const res = http.request(endpoint.method, url, null, {
    headers: reqHeaders,
    timeout: "10s",
    tags: { name: endpoint.path.split("?")[0] },
  });

  reqDuration.add(res.timings.duration);

  if (res.timings.duration >= 10000) {
    timeouts.add(1);
  }

  const ok = check(res, {
    "status is not 5xx": (r) => r.status < 500,
    "response time < 5s": (r) => r.timings.duration < 5000,
  });

  errorRate.add(!ok);

  sleep(Math.random() * 0.5);
}

export function handleSummary(data) {
  const p95 = data.metrics.http_req_duration?.values?.["p(95)"] || 0;
  const p99 = data.metrics.http_req_duration?.values?.["p(99)"] || 0;
  const errRate = data.metrics.errors?.values?.rate || 0;
  const total = data.metrics.http_reqs?.values?.count || 0;

  let verdict = "PASS";
  if (p95 > 5000) verdict = "FAIL (p95 latency)";
  else if (errRate > 0.3) verdict = "FAIL (error rate)";

  return {
    stdout: JSON.stringify(
      {
        test: "stress_test",
        verdict,
        timestamp: new Date().toISOString(),
        metrics: {
          http_req_duration_p95: p95,
          http_req_duration_p99: p99,
          error_rate: errRate,
          total_requests: total,
          timeouts: data.metrics.timeouts?.values?.count || 0,
        },
      },
      null,
      2
    ),
  };
}
