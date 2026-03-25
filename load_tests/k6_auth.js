import http from "k6/http";
import { check, sleep, group } from "k6";
import { Rate, Counter, Trend } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

const errorRate = new Rate("errors");
const loginDuration = new Trend("login_duration", true);
const refreshDuration = new Trend("refresh_duration", true);
const loginCounter = new Counter("login_requests");

export const options = {
  stages: [
    { duration: "30s", target: 10 },
    { duration: "1m", target: 25 },
    { duration: "30s", target: 50 },
    { duration: "1m", target: 50 },
    { duration: "30s", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<2000", "p(99)<5000"],
    errors: ["rate<0.1"],
    login_duration: ["p(95)<3000"],
  },
};

const TEST_USERS = [
  { email: "loadtest1@reconix.ng", password: "LoadTest1Pass!2024" },
  { email: "loadtest2@reconix.ng", password: "LoadTest2Pass!2024" },
  { email: "loadtest3@reconix.ng", password: "LoadTest3Pass!2024" },
];

const headers = {
  "Content-Type": "application/json",
  Accept: "application/json",
};

export default function () {
  const user = TEST_USERS[Math.floor(Math.random() * TEST_USERS.length)];

  group("Authentication Flow", function () {
    const loginRes = http.post(
      `${BASE_URL}/api/v1/auth/login`,
      JSON.stringify({
        email: user.email,
        password: user.password,
      }),
      { headers, tags: { name: "login" } }
    );

    loginDuration.add(loginRes.timings.duration);
    loginCounter.add(1);

    const loginOk = check(loginRes, {
      "login status is 200": (r) => r.status === 200,
      "login has access_token": (r) => {
        try {
          return JSON.parse(r.body).access_token !== undefined;
        } catch {
          return false;
        }
      },
      "login response time < 2s": (r) => r.timings.duration < 2000,
    });

    errorRate.add(!loginOk);

    if (!loginOk || loginRes.status !== 200) {
      sleep(1);
      return;
    }

    const tokens = JSON.parse(loginRes.body);
    const authHeaders = {
      ...headers,
      Authorization: `Bearer ${tokens.access_token}`,
    };

    sleep(0.5);

    const refreshRes = http.post(
      `${BASE_URL}/api/v1/auth/refresh`,
      JSON.stringify({ refresh_token: tokens.refresh_token }),
      { headers, tags: { name: "refresh" } }
    );

    refreshDuration.add(refreshRes.timings.duration);

    check(refreshRes, {
      "refresh status is 200": (r) => r.status === 200,
      "refresh has new tokens": (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.access_token !== undefined && body.refresh_token !== undefined;
        } catch {
          return false;
        }
      },
    });

    sleep(0.5);

    const logoutRes = http.post(`${BASE_URL}/api/v1/auth/logout`, null, {
      headers: authHeaders,
      tags: { name: "logout" },
    });

    check(logoutRes, {
      "logout status is 200": (r) => r.status === 200,
    });
  });

  sleep(Math.random() * 2 + 1);
}

export function handleSummary(data) {
  return {
    stdout: JSON.stringify(
      {
        test: "auth_load_test",
        timestamp: new Date().toISOString(),
        metrics: {
          http_req_duration_p95: data.metrics.http_req_duration?.values?.["p(95)"],
          http_req_duration_p99: data.metrics.http_req_duration?.values?.["p(99)"],
          login_duration_p95: data.metrics.login_duration?.values?.["p(95)"],
          error_rate: data.metrics.errors?.values?.rate,
          total_requests: data.metrics.http_reqs?.values?.count,
        },
      },
      null,
      2
    ),
  };
}
