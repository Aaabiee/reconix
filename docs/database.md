---
title: Database Architecture
nav_order: 3
---

# Reconix — Database Architecture

Comprehensive reference for the Reconix database layer: tables, relationships, data flows, state machines, read replica routing, and usage patterns.

---

## Entity Relationship Diagram

![Database ERD](assets/img/database-erd.png)

---

## Data Flow Diagram

![Database Data Flow](assets/img/database-dataflow.png)

---

## Infrastructure

| Component         | Technology                | Configuration                                    |
| ----------------- | ------------------------- | ------------------------------------------------ |
| Primary database  | PostgreSQL 16 (asyncpg)   | Pool: 20 connections + 20 overflow, pre-ping     |
| Read replica      | PostgreSQL 16 (optional)  | Pool: 10 connections + 10 overflow, auto-fallback |
| ORM               | SQLAlchemy 2.0 async      | Declarative models, `BaseRepository<T>` pattern  |
| Session lifecycle | `async_sessionmaker`      | Commit on success, rollback on exception         |
| Pool health       | `pool_pre_ping=True`      | Stale connection detection before every query    |
| Pool recycling    | `pool_recycle=3600`       | Force reconnect after 1 hour                     |
| Multi-driver      | PostgreSQL, MySQL, Oracle | `DatabaseEngineFactory` adapter in `db.py`       |

### Connection Flow

```text
FastAPI Route
    │
    ▼
Depends(get_db)  ─── or ─── Depends(get_read_db)
    │                              │
    ▼                              ▼
async_sessionmaker(primary)   async_sessionmaker(replica)
    │                              │
    ▼                              ▼
AsyncEngine (write pool)      AsyncEngine (read pool)
    │                              │  ← falls back to primary
    ▼                              ▼     if replica not configured
PostgreSQL Primary            PostgreSQL Read Replica
```

---

## Tables

### 1. users

Stores all system accounts. Supports four roles with 19 fine-grained permissions. Includes brute-force protection via login attempt tracking and time-based account lockout.

| Column                  | Type           | Constraints                | Description                          |
| ----------------------- | -------------- | -------------------------- | ------------------------------------ |
| `id`                    | Integer        | PK, auto-increment         | Unique user identifier               |
| `email`                 | String(255)    | UNIQUE, NOT NULL           | Login credential                     |
| `hashed_password`       | String(255)    | NOT NULL                   | bcrypt hash (12 rounds)              |
| `full_name`             | String(255)    | NOT NULL                   | Display name                         |
| `role`                  | Enum(UserRole) | NOT NULL, default=OPERATOR | ADMIN, OPERATOR, AUDITOR, API_CLIENT |
| `organization`          | String(255)    | nullable                   | Employer or agency                   |
| `is_active`             | Boolean        | NOT NULL, default=TRUE     | Soft disable without deletion        |
| `failed_login_attempts` | Integer        | NOT NULL, default=0        | Counter for lockout trigger          |
| `locked_until`          | DateTime(tz)   | nullable                   | Account locked until this timestamp  |
| `last_login`            | DateTime(tz)   | nullable                   | Last successful authentication       |

**Used by:**

- `POST /auth/login` — Authenticate, check lockout, update `last_login`
- `POST /auth/refresh` — Verify user exists via `sub` claim
- All authenticated routes — `get_current_user` fetches from this table
- `UserService` — CRUD, `increment_login_attempts()`, `lock_user_account()`

**Security controls:** Constant-time dummy verify on non-existent emails (timing attack mitigation). Account locked for 15 minutes after 5 failed attempts. Same error message for invalid email vs invalid password (no user enumeration).

---

### 2. recycled_sims

Core domain entity. Each record represents a SIM card detected as recycled by a telecom operator. Tracks whether old NIN/BVN linkages exist and the cleanup lifecycle.

| Column                | Type                | Constraints               | Description                             |
| --------------------- | ------------------- | ------------------------- | --------------------------------------- |
| `id`                  | Integer             | PK, indexed               | Unique SIM record identifier            |
| `sim_serial`          | String(50)          | UNIQUE, NOT NULL, indexed | SIM card serial number                  |
| `msisdn`              | String(20)          | UNIQUE, NOT NULL, indexed | Phone number (+234 format)              |
| `imsi`                | String(20)          | NOT NULL, indexed         | International Mobile Subscriber ID      |
| `operator_code`       | String(10)          | NOT NULL, indexed         | MTN, GLO, AIRTEL, 9MOBILE              |
| `date_recycled`       | DateTime(tz)        | NOT NULL                  | When the SIM was recycled               |
| `previous_owner_nin`  | String(20)          | nullable, indexed         | Former owner NIN (encrypted at rest)    |
| `previous_nin_linked` | Boolean             | NOT NULL, default=FALSE   | Does old NIN linkage still exist?       |
| `previous_bvn_linked` | Boolean             | NOT NULL, default=FALSE   | Does old BVN linkage still exist?       |
| `cleanup_status`      | Enum(CleanupStatus) | NOT NULL, default=PENDING | PENDING, IN_PROGRESS, COMPLETED, FAILED |

**Used by:**

- `POST /recycled-sims` — Register a single detected recycled SIM (admin/operator)
- `POST /recycled-sims/bulk` — Bulk upload up to 10,000 records from telecom feed (admin only)
- `GET /recycled-sims` — Paginated list with `cleanup_status` filter
- `GET /dashboard/stats` — COUNT by cleanup_status for dashboard cards
- `DelinkService.complete_delink_request()` — Sets `cleanup_status = COMPLETED`

**Validation:** MSISDN validated against Nigerian format `^(\+234|0)[0-9]{10}$`. NIN validated as 11 digits. IMSI validated as 15 digits.

---

### 3. nin_linkages

Tracks MSISDN-to-NIN bindings sourced from NIMC. Uses soft-delete pattern: `is_active` set to `FALSE` when delinked, preserving the historical record.

| Column          | Type                   | Constraints                 | Description                         |
| --------------- | ---------------------- | --------------------------- | ----------------------------------- |
| `msisdn`        | String(20)             | NOT NULL, indexed           | Phone number                        |
| `nin`           | String(20)             | NOT NULL, indexed           | National Identification Number      |
| `is_active`     | Boolean                | NOT NULL, default=TRUE      | FALSE after delinking               |
| `source`        | Enum(NINLinkageSource) | NOT NULL, default=NIMC_API  | NIMC_API, MANUAL, BULK_UPLOAD       |
| `linked_date`   | DateTime(tz)           | NOT NULL                    | When NIMC linked this NIN to MSISDN |
| `unlinked_date` | DateTime(tz)           | nullable                    | When the linkage was delinked       |

**Used by:**

- `POST /nin-linkages/verify` — Check if an MSISDN has an active NIN linkage
- `POST /nin-linkages/bulk-check` — Batch check multiple MSISDNs in a single query (no N+1)
- `NINLinkageService.unlink()` — Sets `is_active=FALSE` during delink execution

---

### 4. bvn_linkages

Tracks MSISDN-to-BVN bindings sourced from NIBSS. Same soft-delete pattern as NIN linkages. Includes `bank_code` to identify which financial institution holds the linkage.

| Column          | Type                   | Constraints                 | Description                           |
| --------------- | ---------------------- | --------------------------- | ------------------------------------- |
| `msisdn`        | String(20)             | NOT NULL, indexed           | Phone number                          |
| `bvn`           | String(20)             | NOT NULL, indexed           | Bank Verification Number              |
| `is_active`     | Boolean                | NOT NULL, default=TRUE      | FALSE after delinking                 |
| `bank_code`     | String(10)             | nullable                    | Financial institution code (e.g. 007) |
| `source`        | Enum(BVNLinkageSource) | NOT NULL, default=NIBSS_API | NIBSS_API, MANUAL, BULK_UPLOAD        |
| `linked_date`   | DateTime(tz)           | NOT NULL                    | When NIBSS linked this BVN to MSISDN  |
| `unlinked_date` | DateTime(tz)           | nullable                    | When the linkage was delinked         |

---

### 5. delink_requests

Workflow orchestration table. Each record represents a request to delink a recycled SIM from old NIN/BVN bindings. Implements a state machine.

| Column            | Type                      | Constraints                    | Description                      |
| ----------------- | ------------------------- | ------------------------------ | -------------------------------- |
| `id`              | Integer                   | PK, indexed                    | Unique request identifier        |
| `recycled_sim_id` | Integer                   | FK(recycled_sims.id), NOT NULL | Which SIM is being delinked      |
| `request_type`    | Enum(DelinkRequestType)   | NOT NULL, default=BOTH         | NIN, BVN, or BOTH                |
| `status`          | Enum(DelinkRequestStatus) | NOT NULL, default=PENDING      | Current workflow state           |
| `initiated_by`    | Integer                   | FK(users.id), NOT NULL         | Operator who created the request |
| `approved_by`     | Integer                   | FK(users.id), nullable         | Admin who approved/rejected      |
| `reason`          | Text                      | nullable                       | Justification for the delink     |
| `error_message`   | Text                      | nullable                       | Failure details if FAILED        |

**State Machine:**

```text
                ┌─────────► CANCELLED
                │
PENDING ────► PROCESSING ────► COMPLETED
                │                   │
                └──────► FAILED     │
                                    ▼
                          recycled_sims.cleanup_status = COMPLETED
                          nin_linkages.is_active = FALSE
                          bvn_linkages.is_active = FALSE
                          notifications created for affected parties
```

**Side effects on completion:**

1. `recycled_sims.cleanup_status` updated to `COMPLETED`
2. `nin_linkages` matching the SIM's MSISDN are soft-deleted
3. `bvn_linkages` matching the SIM's MSISDN are soft-deleted
4. `notifications` created for former owner, bank, and NIMC

---

### 6. notifications

Tracks multi-channel notification dispatch to affected parties during the delink workflow.

| Column              | Type                            | Constraints                      | Description                          |
| ------------------- | ------------------------------- | -------------------------------- | ------------------------------------ |
| `delink_request_id` | Integer                         | FK(delink_requests.id), NOT NULL | Which delink triggered this          |
| `recipient_type`    | Enum(NotificationRecipientType) | NOT NULL                         | FORMER_OWNER, BANK, NIMC, NEW_OWNER |
| `channel`           | Enum(NotificationChannel)       | NOT NULL, default=EMAIL          | SMS, EMAIL, API_CALLBACK             |
| `recipient_address` | String(255)                     | NOT NULL                         | Phone number or email address        |
| `status`            | Enum(NotificationStatus)        | NOT NULL, default=PENDING        | PENDING, SENT, DELIVERED, FAILED     |

---

### 7. audit_logs (IMMUTABLE)

Append-only compliance trail. Every state-changing action is logged with before/after values, IP, and user agent. Records cannot be updated or deleted through the ORM.

| Column          | Type        | Constraints                 | Description                            |
| --------------- | ----------- | --------------------------- | -------------------------------------- |
| `user_id`       | Integer     | FK(users.id), nullable      | Who performed the action (null=system) |
| `action`        | String(100) | NOT NULL, indexed           | create, update, delete, login, etc.    |
| `resource_type` | String(100) | NOT NULL, indexed           | RecycledSIM, DelinkRequest, User, etc. |
| `resource_id`   | String(50)  | NOT NULL, indexed           | ID of the affected resource            |
| `old_value`     | JSON        | nullable                    | State before the change                |
| `new_value`     | JSON        | nullable                    | State after the change                 |
| `ip_address`    | String(45)  | nullable                    | Client IP (IPv4 or IPv6)               |

**PII handling:** All log output passes through `PIIMaskingFilter` which redacts NIN/BVN/MSISDN patterns before writing to stdout. The JSON fields may contain PII but are only accessible to admin/auditor roles.

---

### 8. api_keys

Machine-to-machine authentication for external system integrations. Keys are stored as bcrypt hashes with constant-time comparison.

---

### 9. webhook_subscriptions

Event subscription management for external stakeholder sync. Banks and NIMC register callback URLs to receive delink event notifications. Callback URLs are validated server-side (SSRF protection blocks private IPs, loopback, and cloud metadata endpoints).

---

### 10. revoked_tokens

JWT blacklist table. Stores JTI claims of revoked tokens. Checked on every authenticated request and during token refresh. Expired entries are auto-cleaned via `TokenRevocationService.cleanup_expired()`.

---

### 11. idempotency_keys

Request deduplication table. The `IdempotencyMiddleware` intercepts POST/PUT/PATCH requests carrying an `Idempotency-Key` header. If the key has been seen before, the stored response is replayed. Keys are scoped per-user to prevent IDOR.

---

## End-to-End Data Flow

### Step 1: SIM Ingestion

```text
Telecom CSV ──► POST /recycled-sims/bulk ──► recycled_sims (up to 10,000 rows)
                                                cleanup_status = PENDING
```

### Step 2: Linkage Verification

```text
POST /nin-linkages/bulk-check ──► nin_linkages WHERE msisdn IN (...) AND is_active=TRUE
POST /bvn-linkages/bulk-check ──► bvn_linkages WHERE msisdn IN (...) AND is_active=TRUE
```

Both queries are batched into a single SQL `WHERE IN` clause (no N+1).

### Step 3: Delink Request Creation

```text
POST /delink-requests ──► delink_requests (status=PENDING, request_type=BOTH)
                              validates recycled_sim_id FK exists
```

### Step 4: Admin Approval

```text
POST /delink-requests/{id}/approve ──► status = PROCESSING (or FAILED on rejection)
```

### Step 5: Delink Execution

```text
DelinkService.complete_delink_request()
    ├── recycled_sims.cleanup_status = COMPLETED
    ├── nin_linkages.is_active = FALSE
    ├── bvn_linkages.is_active = FALSE
    ├── delink_requests.status = COMPLETED
    └── notifications created (SMS + API callbacks)
```

### Step 6: Dashboard Reporting (via Read Replica)

```text
GET /dashboard/stats ──► COUNT(*) recycled_sims GROUP BY cleanup_status
                         COUNT(*) nin_linkages WHERE is_active=TRUE
                         COUNT(*) bvn_linkages WHERE is_active=TRUE
                         COUNT(*) delink_requests GROUP BY status
```

---

## Read Replica Routing

When `DATABASE_READ_REPLICA_URL` is set, dashboard queries are routed to the replica. All write operations use the primary. If no replica is configured, all queries fall back to the primary transparently.

| Dependency      | Engine       | Routes                                          |
| --------------- | ------------ | ----------------------------------------------- |
| `get_db()`      | Primary      | All write routes, auth, CRUD operations         |
| `get_read_db()` | Read replica | `GET /dashboard/stats`, `GET /dashboard/trends` |

---

## Retention and Cleanup

| Table              | Retention Policy                    | Cleanup Mechanism                          |
| ------------------ | ----------------------------------- | ------------------------------------------ |
| `audit_logs`       | `AUDIT_LOG_RETENTION_DAYS` (365)    | `POST /retention/purge-audit-logs` (admin) |
| `revoked_tokens`   | Until `expires_at` passes           | `TokenRevocationService.cleanup_expired()` |
| `idempotency_keys` | 5-second dedup window               | Automatic expiry via `expires_at`          |
| All other tables   | No automatic purge                  | Manual via admin operations                |
