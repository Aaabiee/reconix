# Reconix Production Readiness & Security Roadmap

## Executive Summary

Full security audit and production readiness assessment of the Reconix identity reconciliation platform.
This document catalogs every vulnerability, deployment gap, and remediation applied or required
before this system can serve production traffic handling Nigerian national identity data (NIN/BVN/MSISDN).

---

## Phase 1: Critical Security Hardening (MUST FIX)

### 1.1 Authentication & Secrets

| ID   | Issue                                                   | Location                 | Severity | Status     |
| ---- | ------------------------------------------------------- | ------------------------ | -------- | ---------- |
| S-01 | Hardcoded default JWT secret key                        | `fast_api/config.py`     | CRITICAL | FIXED      |
| S-02 | Hardcoded default database credentials                  | `fast_api/config.py`     | CRITICAL | FIXED      |
| S-03 | Password schema allows 8 chars while config requires 12 | `fast_api/auth/authlib/` | HIGH     | FIXED      |
| S-04 | No production environment validation on startup         | `fast_api/config.py`     | CRITICAL | FIXED      |
| S-05 | Refresh token not rotated on use                        | `fast_api/api.py`        | HIGH     | FIXED      |
| S-06 | Logout does not invalidate tokens server-side           | `fast_api/api.py`        | MEDIUM   | FIXED      |
| S-07 | JWT tokens stored in localStorage (XSS-vulnerable)      | `src/services/api.ts`    | CRITICAL | FIXED      |
| S-08 | Demo credentials exposed in production login page       | `src/app/page.tsx`       | HIGH     | FIXED      |

### 1.2 Injection & Input Validation

| ID   | Issue                                                       | Location                | Severity | Status |
| ---- | ----------------------------------------------------------- | ----------------------- | -------- | ------ |
| S-09 | Input sanitization only logs, never blocks                  | `fast_api/api.py`       | CRITICAL | FIXED  |
| S-10 | Pattern matching is case-sensitive (bypassed by mixed case) | `fast_api/api.py`       | HIGH     | FIXED  |
| S-11 | Body read in middleware breaks downstream parsing           | `fast_api/api.py`       | HIGH     | FIXED  |
| S-12 | No request body size enforcement                            | `fast_api/config.py`    | HIGH     | FIXED  |
| S-13 | Dashboard trends `days` param has no upper bound            | `fast_api/api.py`       | MEDIUM   | FIXED  |
| S-14 | Pagination allows up to 1000 records per request            | Multiple endpoint files | MEDIUM   | FIXED  |
| S-15 | `resource_id` path param not validated for format           | `fast_api/api.py`       | MEDIUM   | FIXED  |
| S-16 | Bulk upload has no transaction wrapper                      | `fast_api/api.py`       | MEDIUM   | FIXED  |

### 1.3 CORS, CSRF & Transport Security

| ID   | Issue                                             | Location           | Severity | Status |
| ---- | ------------------------------------------------- | ------------------ | -------- | ------ |
| S-17 | CORS allows wildcard methods and headers          | `fast_api/main.py` | HIGH     | FIXED  |
| S-18 | No CSRF protection on state-changing endpoints    | Multiple           | HIGH     | FIXED  |
| S-19 | No HTTPS redirect enforcement                     | `fast_api/main.py` | HIGH     | FIXED  |
| S-20 | Frontend has no CSP or security headers           | `next.config.js`   | HIGH     | FIXED  |
| S-21 | Frontend fallback to HTTP localhost in production | `next.config.js`   | MEDIUM   | FIXED  |

### 1.4 Rate Limiting & DoS Prevention

| ID   | Issue                                             | Location           | Severity | Status |
| ---- | ------------------------------------------------- | ------------------ | -------- | ------ |
| S-22 | Rate limiter created but never applied to routes  | `fast_api/main.py` | CRITICAL | FIXED  |
| S-23 | Login endpoint has no rate limiting (brute force) | `fast_api/api.py`  | CRITICAL | FIXED  |
| S-24 | No per-IP connection throttling                   | Backend-wide       | HIGH     | FIXED  |

### 1.5 API Key & Authorization

| ID   | Issue                                                   | Location                 | Severity | Status |
| ---- | ------------------------------------------------------- | ------------------------ | -------- | ------ |
| S-25 | API key verification loads ALL active keys into memory  | `fast_api/auth/authlib/` | HIGH     | FIXED  |
| S-26 | `verify_api_key()` returns None silently on missing key | `fast_api/auth/authlib/` | MEDIUM   | FIXED  |
| S-27 | Delink rejection not recorded when `approved=False`     | `fast_api/api.py`        | MEDIUM   | FIXED  |

---

## Phase 2: Deployment Readiness (MUST FIX)

### 2.1 Backend Infrastructure

| ID   | Issue                                                  | Location                | Severity | Status |
| ---- | ------------------------------------------------------ | ----------------------- | -------- | ------ |
| D-01 | Dockerfile runs as root                                | `Dockerfile`            | CRITICAL | FIXED  |
| D-02 | Single uvicorn worker (no concurrency)                 | `Dockerfile`            | HIGH     | FIXED  |
| D-03 | Healthcheck uses `requests` library (not installed)    | `Dockerfile`            | HIGH     | FIXED  |
| D-04 | Health endpoint doesn't check database connectivity    | `fast_api/main.py`      | HIGH     | FIXED  |
| D-05 | No graceful shutdown for in-flight requests            | `fast_api/main.py`      | HIGH     | FIXED  |
| D-06 | Logging uses basicConfig with no format or file output | `fast_api/main.py`      | MEDIUM   | FIXED  |
| D-07 | OpenAPI docs exposed in production                     | `fast_api/main.py`      | MEDIUM   | FIXED  |
| D-08 | Database pool_pre_ping not applied to all drivers      | `fast_api/db.py`        | MEDIUM   | FIXED  |
| D-09 | Audit middleware missing `Response` import (crash)     | `fast_api/main.py`      | HIGH     | FIXED  |
| D-10 | Generic `except Exception` masks real errors           | Multiple endpoint files | MEDIUM   | FIXED  |

### 2.2 Frontend Infrastructure

| ID   | Issue                                        | Location              | Severity | Status     |
| ---- | -------------------------------------------- | --------------------- | -------- | ---------- |
| D-11 | No Dockerfile for frontend                   | `Dockerfile.frontend` | HIGH     | FIXED      |
| D-12 | Image optimization disabled                  | `next.config.js`      | LOW      | FIXED      |
| D-13 | No environment separation (dev/staging/prod) | `.env.example`        | MEDIUM   | FIXED      |
| D-14 | Console.error calls leak data in production  | Multiple components   | LOW      | FIXED      |

### 2.3 Orchestration & CI/CD

| ID   | Issue                                             | Location     | Severity | Status |
| ---- | ------------------------------------------------- | ------------ | -------- | ------ |
| D-15 | No docker-compose for local/staging orchestration | Project root | HIGH     | FIXED  |
| D-16 | No .dockerignore files                            | Project root | MEDIUM   | FIXED  |
| D-17 | No CI/CD pipeline definition                      | Project root | HIGH     | FIXED  |

---

## Phase 3: Operational Excellence (SHOULD FIX)

### 3.1 Observability

| ID   | Issue                      | Recommendation                                              | Priority | Status      |
| ---- | -------------------------- | ----------------------------------------------------------- | -------- | ----------- |
| O-01 | No structured logging      | Adopt JSON logging with correlation IDs for log aggregation | HIGH     | IMPLEMENTED |
| O-02 | No APM/tracing integration | Integrate OpenTelemetry for distributed tracing             | MEDIUM   | IMPLEMENTED |
| O-03 | No error tracking service  | Add Sentry SDK to both frontend and backend                 | HIGH     | IMPLEMENTED |
| O-04 | No uptime monitoring       | Configure health check polling via external service         | MEDIUM   | IMPLEMENTED |
| O-05 | No metrics endpoint        | Expose Prometheus-compatible `/metrics` endpoint            | MEDIUM   | IMPLEMENTED |

### 3.2 Data Protection & Compliance

| ID   | Issue                        | Recommendation                                                       | Priority | Status      |
| ---- | ---------------------------- | -------------------------------------------------------------------- | -------- | ----------- |
| C-01 | No data encryption at rest   | Enable TDE on PostgreSQL or use application-level encryption for PII | HIGH     | IMPLEMENTED |
| C-02 | No secret vault integration  | Integrate HashiCorp Vault with environment variable fallback         | HIGH     | IMPLEMENTED |
| C-03 | No data retention automation | Implement automated purge jobs per AUDIT_LOG_RETENTION_DAYS          | MEDIUM   | IMPLEMENTED |
| C-04 | No PII masking in logs       | Ensure NIN/BVN/MSISDN are masked in all log output                   | HIGH     | IMPLEMENTED |
| C-05 | No backup/restore tested     | Document and test database backup/restore procedures                 | HIGH     | IMPLEMENTED |
| C-06 | NDPR compliance audit        | NDPR data subject rights endpoints and privacy policy                | HIGH     | IMPLEMENTED |

### 3.3 Performance & Scalability

| ID   | Issue                                  | Recommendation                                          | Priority | Status      |
| ---- | -------------------------------------- | ------------------------------------------------------- | -------- | ----------- |
| P-01 | N+1 query in bulk NIN check            | Batch MSISDN lookups into single query                  | MEDIUM   | IMPLEMENTED |
| P-02 | No database connection pool monitoring | Add pool exhaustion alerts                              | MEDIUM   | IMPLEMENTED |
| P-03 | No caching layer (Redis)               | Add Redis for session/token blacklist and query caching | HIGH     | IMPLEMENTED |
| P-04 | No CDN for static assets               | CDN asset prefix + immutable cache headers configured   | MEDIUM   | IMPLEMENTED |
| P-05 | No database read replicas              | Read replica routing for dashboard/reporting queries    | LOW      | IMPLEMENTED |

### 3.4 Testing & Quality

| ID   | Issue                                | Recommendation                                    | Priority | Status      |
| ---- | ------------------------------------ | ------------------------------------------------- | -------- | ----------- |
| T-01 | No E2E tests                         | Add Playwright or Cypress for critical user flows | HIGH     | IMPLEMENTED |
| T-02 | No load/stress testing               | k6 load, API, and stress test suites              | HIGH     | IMPLEMENTED |
| T-03 | No dependency vulnerability scanning | Add `pip-audit` and `npm audit` to CI pipeline    | HIGH     | IMPLEMENTED |
| T-04 | No SAST/DAST scanning                | Integrate Semgrep (SAST) and OWASP ZAP (DAST)     | MEDIUM   | IMPLEMENTED |

---

## Phase 4: Future Enhancements (NICE TO HAVE)

| ID   | Enhancement                                                        | Priority | Status      |
| ---- | ------------------------------------------------------------------ | -------- | ----------- |
| F-01 | Implement refresh token rotation with server-side revocation list  | HIGH     | IMPLEMENTED |
| F-02 | Add WebSocket support for real-time notifications                  | MEDIUM   | IMPLEMENTED |
| F-03 | API versioning deprecation strategy with sunset headers            | LOW      | IMPLEMENTED |
| F-04 | Implement idempotency keys for POST endpoints                      | MEDIUM   | IMPLEMENTED |
| F-05 | Add request deduplication middleware                               | LOW      | IMPLEMENTED |
| F-06 | Multi-region deployment with active-passive failover               | LOW      | IMPLEMENTED |
| F-07 | Implement RBAC with fine-grained permissions (beyond role strings) | MEDIUM   | IMPLEMENTED |
| F-08 | Add OpenAPI client SDK generation for consumer integrations        | LOW      | IMPLEMENTED |

---

## Phase 5: Stakeholder Aggregation Platform

Reconix operates as a **read-only aggregator** — it connects outbound to stakeholder systems (NIMC, NIBSS, telecoms, banks) to pull identity-linkage data, cross-references it, and exposes the corroborated picture. No stakeholder writes to Reconix; Reconix does not write to any stakeholder system.

### 5.1 Stakeholder Registry

| ID   | Feature                                                             | Priority | Status      |
| ---- | ------------------------------------------------------------------- | -------- | ----------- |
| A-01 | Stakeholder model (NIMC, NIBSS, telecom, bank connection configs)   | HIGH     | IMPLEMENTED |
| A-02 | Secure outbound HTTPS-only adapters with SSRF protection            | HIGH     | IMPLEMENTED |
| A-03 | Per-stakeholder rate limiting and timeout configuration             | MEDIUM   | IMPLEMENTED |
| A-04 | Connection health check per stakeholder                             | MEDIUM   | IMPLEMENTED |

### 5.2 Data Aggregation & Corroboration

| ID   | Feature                                                             | Priority | Status      |
| ---- | ------------------------------------------------------------------- | -------- | ----------- |
| A-05 | Corroboration engine (cross-reference local + external sources)     | HIGH     | IMPLEMENTED |
| A-06 | Confidence scoring (source availability + data completeness)        | HIGH     | IMPLEMENTED |
| A-07 | Conflict detection (local vs external data disagreements)           | HIGH     | IMPLEMENTED |
| A-08 | Unified identity mapping endpoint (GET /identity/lookup)            | HIGH     | IMPLEMENTED |
| A-09 | Batch identity lookup (POST /identity/batch-lookup, max 100)        | MEDIUM   | IMPLEMENTED |
| A-10 | Admin-only corroboration with live external queries                 | MEDIUM   | IMPLEMENTED |
| A-11 | Conflict listing endpoint (GET /identity/conflicts)                 | MEDIUM   | IMPLEMENTED |

### 5.3 Sync Orchestration

| ID   | Feature                                                             | Priority | Status      |
| ---- | ------------------------------------------------------------------- | -------- | ----------- |
| A-12 | Sync orchestrator (pull from all active stakeholders)               | HIGH     | IMPLEMENTED |
| A-13 | Per-stakeholder sync (sync single stakeholder by code)              | MEDIUM   | IMPLEMENTED |
| A-14 | NIMC adapter (NIN lookup, verification, batch)                      | HIGH     | IMPLEMENTED |
| A-15 | NIBSS adapter (BVN lookup, verification, batch)                     | HIGH     | IMPLEMENTED |
| A-16 | Telecom adapter (recycled SIM feed pull, SIM status, owner verify)  | HIGH     | IMPLEMENTED |
| A-17 | Sync status tracking (last_sync_at, records count, status)          | MEDIUM   | IMPLEMENTED |

---

## OWASP Top 10 Compliance Matrix

| OWASP Category                 | Status   | Notes                                                                        |
| ------------------------------ | -------- | ---------------------------------------------------------------------------- |
| A01: Broken Access Control     | HARDENED | RBAC enforced server-side, IDOR protection via ownership checks              |
| A02: Cryptographic Failures    | HARDENED | bcrypt passwords, JWT HS256, HTTPS enforced, no plaintext secrets            |
| A03: Injection                 | HARDENED | SQLAlchemy ORM (parameterized), input sanitization blocks dangerous patterns |
| A04: Insecure Design           | HARDENED | Defense-in-depth, rate limiting, account lockout, audit logging              |
| A05: Security Misconfiguration | HARDENED | Production config validation, no default secrets, security headers           |
| A06: Vulnerable Components     | HARDENED | Pinned versions, pip-audit + npm audit + Semgrep SAST in CI (T-03, T-04)     |
| A07: Auth Failures             | HARDENED | Rate-limited login, account lockout, token expiry, refresh rotation          |
| A08: Data Integrity Failures   | HARDENED | Input validation, schema enforcement, transaction safety, idempotency keys   |
| A09: Logging & Monitoring      | HARDENED | Structured JSON logging with PII masking, Prometheus metrics (O-01, O-05)    |
| A10: SSRF                      | HARDENED | External API URLs configured server-side only, no user-supplied URLs         |

---

## Security Headers Applied

### Backend (via SecurityHeadersMiddleware)

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `Cache-Control: no-store` (on API responses)

### CustomSecurityMiddleware (via custom_middleware.py)

- TRACE/TRACK method blocking (HTTP verb tampering prevention)
- URL length enforcement (max 2048 chars)
- Header size enforcement (max 8192 bytes total)
- Content-Type enforcement on state-changing methods (only JSON/multipart)
- Host header validation (required)
- Slow request logging (>5s threshold)
- `Cross-Origin-Opener-Policy: same-origin`
- `Cross-Origin-Resource-Policy: same-origin`
- `Cross-Origin-Embedder-Policy: require-corp`
- `X-Permitted-Cross-Domain-Policies: none`

### Frontend (via next.config.js headers)

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
- `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:;` (production — 'unsafe-eval' removed)

---

## Authentication & OAuth2 Architecture

### Token Flow

```text
Client                  Backend                  Database
| -- POST /auth/login -->  |                           |
| ------------------------ | ------------------------- |
|                          | <- user record ---------- |
| <- access + refresh ---  |                           |
|                          |                           |
| -- POST /auth/refresh -> |                           |
|                          | -- check jti revoked? --> |
|                          | -- revoke old jti ------> |
| <- new access+refresh -- |                           |
|                          |                           |
| -- POST /auth/logout --> |                           |
|                          | -- revoke access jti ---> |
| <- 200 OK -------------  |                           |
```

### Components (fast_api/auth/authlib/)

- **oauth2.py** — OAuth2 Bearer scheme via FastAPI `HTTPBearer`. Extracts token from `Authorization: Bearer <token>`, decodes JWT, validates `sub` claim, fetches user from DB, checks `is_active`. Returns 401 on invalid/expired/malformed tokens. Safe int cast on `user_id` to prevent 500 on crafted tokens.
- **jwt_handler.py** — Stateless JWT creation/verification. Access tokens (24h, type=access), refresh tokens (7d, type=refresh, unique `jti` via `secrets.token_hex`). HS256 signing with server-side secret.
- **password.py** — bcrypt hashing via passlib (12 rounds). Minimum password length enforced. API key generation via `secrets.token_urlsafe(48)`.
- **api_key.py** — `X-API-Key` header verification. Loads only active, non-expired keys. Constant-time comparison via bcrypt verify.
- **rbac.py** — Role-based access: `require_role(["admin", "operator"])` dependency factory.
- **permissions.py** — Fine-grained RBAC: 19 `Permission` enums mapped to 4 roles. `require_permission(Permission.AUDIT_READ)` dependency.

### Token Revocation (fast_api/services/token_revocation_service.py)

- Server-side `revoked_tokens` table stores revoked JTIs
- On `/refresh`: old refresh token JTI is revoked, checked before issuing new pair
- On `/logout`: access token JTI is revoked
- Reuse of revoked refresh token returns 401
- Expired revocation records auto-cleaned via `cleanup_expired()`

### Security Hardening Applied

- Constant-time dummy verify on non-existent user (timing attack mitigation)
- Account lockout after 5 failed attempts (15 min)
- Rate limiting: 5/min on auth endpoints, 100/min general
- No user enumeration (same error for invalid email vs password)
- Refresh tokens rotated on every use (one-time use)
- SSRF protection on webhook callback URLs
- Idempotency keys scoped per-user (IDOR prevention)

---

## Deployment Architecture

```text
                    Internet
                       |
                 [Load Balancer]
                   /         \
          [Frontend]         [Backend]
          Next.js            FastAPI + Gunicorn
          Port 3000          Port 8000
                               |
                         [PostgreSQL]
                          Port 5432
```

### Container Strategy

- **Frontend**: Multi-stage Node.js build -> standalone Next.js output
- **Backend**: Python 3.12-slim -> Gunicorn with Uvicorn workers, non-root user
- **Database**: Official PostgreSQL 16 with persistent volume
- **Orchestration**: Docker Compose for dev/staging, Kubernetes for production

---

## Restructured Backend Architecture

```text
fast_api/
├── config.py                    # Pydantic settings with production validation
├── db.py                        # Engine, session, init_db, close_db, get_db
├── main.py                      # App factory, lifespan, middleware stack
├── api.py                       # Router aggregating all route modules
├── logging_config.py            # Structured JSON logging + PII masking
├── crypto.py                    # Application-level PII field encryption
├── auth/
│   └── authlib/
│       ├── jwt_handler.py       # JWT creation, verification, refresh rotation
│       ├── password.py          # Password hashing (passlib/bcrypt)
│       ├── oauth2.py            # OAuth2 Bearer token extraction, user lookup, safe int cast
│       ├── api_key.py           # API key verification from X-API-Key header
│       ├── rbac.py              # require_role() factory
│       └── permissions.py       # Fine-grained permission-based RBAC (19 permissions)
├── routes/
│   ├── auth.py                  # Login, refresh, logout
│   ├── recycled_sims.py         # SIM CRUD, bulk upload
│   ├── delink_requests.py       # Delink workflow
│   ├── dashboard.py             # Stats and trends
│   ├── webhooks.py              # Stakeholder sync
│   ├── retention.py             # Audit log retention purge
│   ├── data_subject.py          # NDPR data subject rights (access, deletion, consent)
│   └── ws.py                    # WebSocket real-time notifications
├── models/                      # 11 SQLAlchemy models (+ IdempotencyKey, RevokedToken)
├── schemas/                     # 12 Pydantic schemas (+ DataSubject)
├── services/                    # 12 business logic services (+ CacheService, VaultService, DataSubjectService)
├── middleware/                  # 14 middleware files (+ tracing, sentry, sunset_headers)
├── validators/                  # nigerian.py, pagination.py
├── exceptions/                  # Custom exceptions + HTTP handlers
└── tests/                       # unit/ + component/ + integration/
```

## Frontend Architecture

```text
reconix/                                 # Project root
├── index.html                           # HTML document shell
├── index.scss                           # Global Tailwind + Material styles
├── App.tsx                              # Root app shell (sidebar + header)
├── App.spec.tsx                         # App shell tests
├── Dockerfile                           # Unified backend + frontend image
├── Dockerfile.build                     # Build with validation stages
├── package.json                         # Frontend dependencies
├── tsconfig.json                        # @/* -> ./src/*
├── tailwind.config.ts                   # Brand colors, Material elevations
├── next.config.js                       # CSP, HSTS, security headers
├── public/
│   └── branding/                        # SVG logo, banner, dashboard pattern
└── src/
    ├── main.tsx                         # Authenticated app bootstrap
    ├── main.scss                        # Layout-level styles
    ├── main.html                        # Semantic HTML template
    ├── main.spec.ts                     # Bootstrap tests
    ├── app/                             # Next.js App Router pages
    └── components/                      # 20 feature directories
        ├── login/                       # login.component.tsx + .scss + .spec.ts
        ├── data-table/                  # data-table.component.tsx + .scss + .spec.ts
        ├── sidebar/                     # sidebar.component.tsx + .scss + .spec.ts
        └── ...17 more
```

## Test Coverage

| Layer                | Tests    | Coverage Areas                                                                                              |
| -------------------- | -------- | ----------------------------------------------------------------------------------------------------------- |
| fast_api Unit        | 230+     | Validators, security, input guard, audit PII masking, crypto, tracing, cache, vault, read replica, delink   |
| fast_api Component   | 95+      | All endpoint routes with auth/role verification, NDPR data subject, WebSocket, metrics, health              |
| fast_api Integration | 85+      | Body injection, IDOR, shell exec, workflows, RBAC, observability, NDPR, token lifecycle, JTI revocation     |
| src Unit             | 37       | Services, hooks, state management                                                                           |
| src Component        | 62       | DataTable, Modal, StatsCard, LoginForm, NotificationBell (*.component.spec.ts)                              |
| src Integration      | 30+      | Auth flow, dashboard, delink workflow, observability, WebSocket, NDPR data subject rights                   |
| k6 Load Tests        | 3 suites | Auth load, API read-heavy, stress test (up to 500 VUs)                                                      |
| **Total**            | **540+** |                                                                                                             |

## Infrastructure

- `Dockerfile` - Unified backend + frontend image (Gunicorn + Node.js)
- `Dockerfile.build` - Build with py_compile, tsc, and test validation stages
- `docker-compose.yml` - PostgreSQL + unified app service
- `.github/workflows/ci.yml` - Test, lint, type-check, SCSS check, Docker build, security scan
- `Pipfile` / `Pipfile.lock` - Python dependency management (Python 3.12)
- `scripts/backup_db.py` - PostgreSQL backup with retention cleanup
- `scripts/restore_db.py` - PostgreSQL restore with path validation
- `scripts/health_check.py` - Uptime monitoring health check poller
- `scripts/generate_sdk.py` - OpenAPI client SDK generator
- `load_tests/k6_auth.js` - Authentication load test (ramp to 50 VUs)
- `load_tests/k6_api.js` - API read-heavy load test (ramp to 100 VUs)
- `load_tests/k6_stress.js` - Stress test (ramp to 500 VUs)
- `infra/k8s/deployment.yaml` - Kubernetes deployment, service, PDB, HPA
- `infra/k8s/multi-region.yaml` - Multi-region ingress, secrets, failover config
- `ROADMAP.md` - This file
