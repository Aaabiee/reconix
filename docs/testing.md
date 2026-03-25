---
title: Testing
nav_order: 6
---

# Reconix — Testing

678 tests across unit, component, integration, E2E, and load test layers (483 backend, 195 frontend).

---

## Test Coverage

| Layer                | Tests    | Coverage                                                                                  |
| -------------------- | -------- | ----------------------------------------------------------------------------------------- |
| Backend Unit         | 273      | Validators, security, input guard, crypto, cache, vault, corroboration, PII               |
| Backend Component    | 120      | All endpoints including identity, MSISDN status, detection scan, NDPR, WebSocket, health  |
| Backend Integration  | 90       | Body injection, IDOR, shell exec, delink unlinking, RBAC, token lifecycle                 |
| Frontend Unit        | 37       | Services, hooks, state management                                                         |
| Frontend Component   | 62       | All 22 components including NotificationBell                                              |
| Frontend Integration | 82       | Auth flow, dashboard, delink, observability, WebSocket, NDPR                              |
| E2E (Playwright)     | 14       | Auth, security headers, navigation, responsive                                            |
| k6 Load Tests        | 3 suites | Auth (50 VUs), API read-heavy (100 VUs), stress (500 VUs)                                 |

---

## Running Tests

### Backend

```bash
# All backend tests
pipenv run pytest -q

# By layer
pipenv run pytest fast_api/tests/unit/ -q
pipenv run pytest fast_api/tests/component/ -q
pipenv run pytest fast_api/tests/integration/ -q
```

### Frontend

```bash
npm test -- --coverage
```

### E2E (Playwright)

```bash
cd e2e && npx playwright install && npx playwright test
```

### Load Tests (k6)

```bash
# Authentication flow load test (ramp to 50 VUs)
k6 run load_tests/k6_auth.js

# API read-heavy load test (ramp to 100 VUs)
k6 run load_tests/k6_api.js --env ACCESS_TOKEN=<token>

# Stress test (ramp to 500 VUs)
k6 run load_tests/k6_stress.js --env ACCESS_TOKEN=<token>
```

---

## Test Infrastructure

### Backend Test Stack

- **pytest** with async support (`pytest-asyncio`)
- **httpx** `AsyncClient` with `ASGITransport` for testing FastAPI without a server
- **In-memory SQLite** (`sqlite+aiosqlite:///:memory:`) for isolated database tests
- **Dependency overrides** for `get_db` to inject test sessions

### Frontend Test Stack

- **Jest** with `jsdom` environment
- **@testing-library/react** for component rendering
- **ts-jest** for TypeScript transformation
- **Module aliases** (`@/` mapped to `src/`)

### Test Fixtures (conftest.py)

**User fixtures:** `test_user` (operator), `test_admin`, `test_auditor`, `locked_user`

**Token fixtures:** `access_token`, `admin_access_token`, `auditor_access_token`

**Domain fixtures:** `test_recycled_sim`, `test_nin_linkage`, `test_bvn_linkage`, `test_delink_request`, `test_notification`, `test_audit_log`

---

## Load Test Thresholds

### k6_auth.js

| Metric            | Threshold |
| ------------------ | --------- |
| p95 latency        | < 2000 ms |
| p99 latency        | < 5000 ms |
| Login p95          | < 3000 ms |
| Error rate         | < 10%     |

### k6_api.js

| Metric            | Threshold |
| ------------------ | --------- |
| p95 latency        | < 1000 ms |
| p99 latency        | < 3000 ms |
| List SIMs p95      | < 1500 ms |
| Dashboard p95      | < 2000 ms |
| Error rate         | < 5%      |

### k6_stress.js

| Metric            | Threshold |
| ------------------ | --------- |
| p95 latency        | < 5000 ms |
| Error rate         | < 30%     |
| HTTP failure rate  | < 30%     |

---

## Security Test Coverage

Tests specifically targeting OWASP vulnerabilities:

- **SQL injection** — `'; DROP TABLE`, `UNION SELECT`, parameterized query validation
- **XSS** — `<script>alert(1)</script>` in query params and request bodies
- **Command injection** — `; rm -rf /`, path traversal `../../etc/passwd`
- **IDOR** — Accessing resources by ID without ownership, cross-user data access
- **RBAC** — Operator cannot access admin routes, auditor cannot write
- **Brute force** — Account lockout after 5 failed attempts
- **Token security** — Expired token rejected, wrong type rejected, revoked token rejected
- **Request size** — Oversized requests (>10MB) rejected with 413
- **Security headers** — CSP, HSTS, X-Frame-Options verified present
