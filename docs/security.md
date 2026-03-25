---
title: Security
nav_order: 4
---

# Reconix — Security

Reconix is hardened against the full OWASP Top 10. This page details every security control applied across the platform.

---

## OWASP Top 10 Compliance Matrix

| OWASP Category                 | Status       | Controls                                                                    |
| ------------------------------ | ------------ | --------------------------------------------------------------------------- |
| A01: Broken Access Control     | **Hardened** | RBAC (4 roles, 19 permissions), IDOR protection, user-scoped idempotency    |
| A02: Cryptographic Failures    | **Hardened** | bcrypt (12 rounds), HMAC-SHA256 PII encryption, no plaintext fallback       |
| A03: Injection                 | **Hardened** | SQLAlchemy ORM (parameterized), input guard blocks SQLi/XSS/RCE patterns    |
| A04: Insecure Design           | **Hardened** | Defense-in-depth (14 middleware layers), rate limiting, account lockout      |
| A05: Security Misconfiguration | **Hardened** | Production config validation, strict CSP (no unsafe-eval), docs hidden      |
| A06: Vulnerable Components     | **Hardened** | pip-audit + npm audit + Semgrep SAST in CI                                  |
| A07: Auth Failures             | **Hardened** | Token rotation, JTI revocation, timing-safe dummy verify, 5-attempt lockout |
| A08: Data Integrity Failures   | **Hardened** | Idempotency keys, schema enforcement, transactional writes                  |
| A09: Logging & Monitoring      | **Hardened** | Structured JSON logs, PII auto-masking, Prometheus metrics, audit trail     |
| A10: SSRF                      | **Hardened** | Webhook URL validation blocks private IPs, loopback, metadata endpoints     |

---

## Security Headers

### Backend (SecurityHeadersMiddleware)

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `Cache-Control: no-store` (on API responses)

### CustomSecurityMiddleware

- TRACE/TRACK method blocking (HTTP verb tampering prevention)
- URL length enforcement (max 2048 chars)
- Header size enforcement (max 8192 bytes total)
- Content-Type enforcement on state-changing methods (only JSON/multipart)
- Host header validation (required)
- Slow request logging (>5s threshold)
- `Cross-Origin-Opener-Policy: same-origin`
- `Cross-Origin-Resource-Policy: same-origin`
- `Cross-Origin-Embedder-Policy: require-corp`

### Frontend (next.config.js)

- Production CSP removes `unsafe-eval` from `script-src`
- `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
- CDN origins whitelisted in `img-src` and `connect-src`
- WebSocket origins whitelisted in `connect-src`

---

## Authentication & Authorization

### RBAC (4 roles, 19 permissions)

| Role         | Permissions                                                    |
| ------------ | -------------------------------------------------------------- |
| `ADMIN`      | All 19 permissions — full system access                        |
| `OPERATOR`   | 12 permissions — SIM management, delink, notifications         |
| `AUDITOR`    | 5 permissions — read-only audit logs and reports               |
| `API_CLIENT` | Scoped per API key — machine-to-machine                        |

### Token Security

- Access tokens: 24-hour TTL, `type=access`, HS256 signing
- Refresh tokens: 7-day TTL, `type=refresh`, unique JTI via `secrets.token_hex`
- Refresh tokens rotated on every use (one-time use)
- Logout revokes access token JTI in `revoked_tokens` table
- Reuse of revoked refresh token returns 401

### Brute-Force Protection

- Rate limiting: 5 requests/minute on auth endpoints
- Account lockout: 5 failed attempts triggers 15-minute lockout
- Constant-time dummy bcrypt verify on non-existent emails
- No user enumeration: identical error for invalid email vs password

---

## Input Validation

### InputSanitizationMiddleware

Scans both **query strings AND JSON request bodies** (up to 64KB, nested to depth 5) for dangerous patterns:

- SQL injection: `UNION SELECT`, `DROP TABLE`, `EXEC`, `GROUP_CONCAT`, `LOAD_FILE`, `INTO OUTFILE`
- XSS: `<script>`, `javascript:`, `onerror=`, etc.
- Command injection: `; rm -rf`, `; bash`, `; python`, `; perl`, `; nc`, `$(cmd)`, backtick execution
- Path traversal: `../../`, null bytes (`\x00`)
- Comment-based bypass: `/* */` SQL comments blocked
- Path traversal: `../../`, `/etc/passwd`, etc.

Pattern matching is case-insensitive to prevent bypass via mixed case.

### Nigerian Data Validators

- MSISDN: `^(\+234|0)[7-9]\d{9}$`
- NIN: 11 digits
- BVN: 11 digits
- IMSI: 15 digits

---

## IDOR Protection (Broken Object-Level Authorization)

Every resource-level endpoint enforces ownership or role-based access:

| Endpoint                       | Access Rule                                          |
| ------------------------------ | ---------------------------------------------------- |
| `GET /delink-requests/{id}`    | Only creator or admin/auditor can view               |
| `POST /delink-requests/cancel` | Only creator or admin can cancel                     |
| `GET /recycled-sims/{id}`      | Requires admin, operator, or auditor role            |
| `PATCH /recycled-sims/{id}`    | Requires admin or operator role                      |
| `GET /notifications/{id}`      | Requires admin, operator, or auditor role            |
| `GET /webhooks/subscriptions`  | Non-admin users see only their own subscriptions     |
| `GET /data-subject/my-data`    | Returns only the authenticated user's own data       |

---

## Webhook Security

- Webhook `secret_key` encrypted at rest using `EncryptedString` (HMAC-SHA256)
- Inbound webhooks require HMAC-SHA256 signature verification against stored secrets
- Outbound webhook URLs validated for SSRF (private IPs, loopback, metadata blocked)
- Secret keys auto-generated via `secrets.token_urlsafe(32)` (256-bit entropy)

---

## JWT Algorithm Restriction

The `JWT_ALGORITHM` config is restricted to a whitelist at startup. If set to any value other than `HS256`, `HS384`, or `HS512`, the application exits immediately. This prevents the "none" algorithm attack.

---

## PII Protection

### Encryption at Rest

- `FIELD_ENCRYPTION_KEY` (min 32 chars) used for HMAC-SHA256 PII encryption
- `EncryptedString` SQLAlchemy type decorator encrypts on write, decrypts on read
- HMAC integrity verification prevents tampered ciphertext from decrypting
- Webhook secret keys encrypted at rest using the same mechanism

### PII Masking in Logs

- `PIIMaskingFilter` redacts NIN (11 digits), BVN (11 digits), MSISDN (+234...) patterns
- `SENSITIVE_KEYS` set redacts `password`, `token`, `api_key`, `secret`, `authorization`, `cookie`
- Sentry `before_send` hook scrubs PII keys including `nin`, `bvn`, `msisdn`, `imsi`

---

## NDPR Compliance

Nigeria Data Protection Regulation (2019) compliance features:

| Endpoint                                      | Right                  | Description                     |
| --------------------------------------------- | ---------------------- | ------------------------------- |
| `GET /api/v1/data-subject/privacy-policy`     | Right to be informed   | Full NDPR disclosure            |
| `GET /api/v1/data-subject/my-data`            | Right of access        | Export personal data            |
| `POST /api/v1/data-subject/delete-my-data`    | Right to erasure       | Request data deletion           |
| `GET /api/v1/data-subject/consent`            | Consent management     | View consent record             |
| `POST /api/v1/data-subject/access-request`    | Data subject request   | Submit formal DSAR              |

- Admin accounts cannot self-delete
- Audit logs retained per NDPR Section 2.1(1)(b) — anonymized, not deleted
- Data Protection Officer contact: `dpo@reconix.ng`
- No cross-border transfers without NDPB approval
