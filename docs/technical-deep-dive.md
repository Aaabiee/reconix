---
title: Technical Deep Dive
nav_order: 8
---

# Reconix — Technical Deep Dive

Complete technical specification of every stage in the application lifecycle, the interdependencies between stages, and the exact format of data exchanged at each boundary.

---

## Application Lifecycle Stages

The Reconix platform processes recycled SIM cards through six sequential stages. Each stage produces output consumed by the next, forming a directed pipeline with no circular dependencies.

```text
Stage 1          Stage 2          Stage 3          Stage 4          Stage 5          Stage 6
INGEST  ──────►  DETECT  ──────►  VERIFY  ──────►  DELINK  ──────►  NOTIFY  ──────►  REPORT
Telecom feed     Scan for         Check NIN/BVN    Approve and      Alert former     Dashboard
into DB          stale linkages   against NIMC     execute unlink   owner + banks    + corroborate
```

---

## Stage 1: SIM Ingestion

**Purpose:** Import recycled SIM records from telecom operators into the platform.

**Entry points:**

- `POST /api/v1/recycled-sims` — single record (admin/operator)
- `POST /api/v1/recycled-sims/bulk` — batch of up to 10,000 records (admin only)

**Input schema (per record):**

```json
{
  "sim_serial": "89234567890123456789",
  "msisdn": "+2347012345678",
  "imsi": "621234567890123",
  "operator_code": "MTN",
  "date_recycled": "2024-03-01T00:00:00Z",
  "date_deactivated": "2024-02-15T00:00:00Z",
  "previous_owner_nin": "12345678901"
}
```

**Validation rules applied:**

| Field              | Rule                          | Enforced by        |
| ------------------ | ----------------------------- | ------------------ |
| `msisdn`           | `^\+?234[0-9]{10}$`          | Pydantic schema    |
| `imsi`             | `^[0-9]{15}$`                | Pydantic schema    |
| `sim_serial`       | 1-50 chars, unique in DB      | DB unique index    |
| `operator_code`    | max 10 chars                  | Pydantic schema    |
| `date_recycled`    | valid ISO 8601 datetime       | Pydantic schema    |
| JSON body content  | No SQLi/XSS/shell patterns    | InputGuard middleware |

**Output (stored in `recycled_sims` table):**

The record is persisted with two additional computed fields:

- `cleanup_status = PENDING` (default)
- `msisdn_status = RECYCLED` (default)

**Downstream dependency:** Stage 2 (Detection) reads from this table.

**Bulk upload response:**

```json
{
  "total_records": 5000,
  "successful": 4998,
  "failed": 2,
  "errors": [
    {"record_index": 1247, "error": "Duplicate sim_serial"},
    {"record_index": 3891, "error": "Invalid MSISDN format"}
  ]
}
```

---

## Stage 2: Detection Scan

**Purpose:** Identify which recycled SIMs still have active NIN/BVN linkages that need delinking.

**Entry point:** `POST /api/v1/recycled-sims/detect` (admin only)

**Input:** No request body. Scans all `recycled_sims` where `cleanup_status = PENDING`.

**Processing algorithm:**

```text
FOR each RecycledSIM WHERE cleanup_status = PENDING:
    nin_count = COUNT(nin_linkages WHERE msisdn = SIM.msisdn AND is_active = TRUE)
    bvn_count = COUNT(bvn_linkages WHERE msisdn = SIM.msisdn AND is_active = TRUE)

    IF nin_count > 0 OR bvn_count > 0:
        SIM.previous_nin_linked = (nin_count > 0)
        SIM.previous_bvn_linked = (bvn_count > 0)
        SIM.msisdn_status = CONFLICTED
        flagged++
    ELSE:
        SIM.msisdn_status = AVAILABLE
        clean++

COMMIT all updates
```

**Output:**

```json
{
  "message": "Detection scan completed",
  "total_scanned": 5000,
  "conflicted": 1247,
  "clean": 3753
}
```

**Interdependency:** This stage reads from `recycled_sims` (Stage 1 output) and cross-references against `nin_linkages` and `bvn_linkages` tables. It writes back to `recycled_sims` only — updating `msisdn_status` and the `previous_*_linked` boolean flags.

**Downstream dependency:** Stage 3 (Verification) and Stage 4 (Delink) consume the `CONFLICTED` status to determine which SIMs need action.

---

## Stage 3: Linkage Verification

**Purpose:** Verify the current state of NIN/BVN linkages for specific MSISDNs, either individually or in batch.

**Entry points:**

- `POST /api/v1/nin-linkages/verify` — single MSISDN NIN check
- `POST /api/v1/bvn-linkages/verify` — single MSISDN BVN check
- `POST /api/v1/nin-linkages/bulk-check` — batch NIN check (up to 1,000)
- `POST /api/v1/bvn-linkages/bulk-check` — batch BVN check (up to 1,000)

**NIN verify request:**

```json
{
  "msisdn": "+2347012345678"
}
```

**NIN verify response:**

```json
{
  "msisdn": "+2347012345678",
  "nin": "12345678901",
  "is_linked": true,
  "linked_since": "2022-06-15T00:00:00Z",
  "verified_at": "2024-03-01T12:00:00Z"
}
```

**BVN verify response (additional field):**

```json
{
  "msisdn": "+2347012345678",
  "bvn": "10987654321",
  "is_linked": true,
  "bank_code": "007",
  "linked_since": "2021-09-20T00:00:00Z",
  "verified_at": "2024-03-01T12:00:00Z"
}
```

**Bulk check request:**

```json
{
  "msisdns": ["+2347012345678", "+2348098765432", "+2349011223344"]
}
```

**Bulk check response:**

```json
{
  "total_checked": 3,
  "linked_count": 2,
  "unlinked_count": 1,
  "results": [
    {"msisdn": "+2347012345678", "nin": "12345678901", "is_linked": true, "linked_since": "2022-06-15T00:00:00Z"},
    {"msisdn": "+2348098765432", "nin": null, "is_linked": false, "linked_since": null},
    {"msisdn": "+2349011223344", "nin": "99887766554", "is_linked": true, "linked_since": "2023-01-10T00:00:00Z"}
  ]
}
```

**SQL optimization:** Bulk check uses a single `WHERE msisdn IN (...)` query. No N+1 problem.

**Interdependency:** Reads from `nin_linkages` and `bvn_linkages` tables. Does not modify any data. This stage is purely read-only and can be called independently of the detection scan.

**Downstream dependency:** The verification results inform operators whether a delink request should be created (Stage 4).

---

## Stage 4: Delink Workflow

**Purpose:** Orchestrate the approval and execution of delinking a recycled SIM from its old NIN/BVN bindings.

### 4.1 Request Creation

**Entry point:** `POST /api/v1/delink-requests` (admin/operator)

**Request:**

```json
{
  "recycled_sim_id": 42,
  "request_type": "both",
  "reason": "SIM recycled by MTN, old NIN/BVN still linked"
}
```

`request_type` determines which linkages to delink: `nin` (NIN only), `bvn` (BVN only), or `both`.

**Response:**

```json
{
  "id": 17,
  "recycled_sim_id": 42,
  "request_type": "both",
  "status": "pending",
  "initiated_by": 3,
  "approved_by": null,
  "reason": "SIM recycled by MTN, old NIN/BVN still linked",
  "error_message": null,
  "completed_at": null,
  "created_at": "2024-03-01T14:00:00Z",
  "updated_at": "2024-03-01T14:00:00Z"
}
```

**Validation:** The `recycled_sim_id` must reference an existing `recycled_sims` record (FK constraint).

### 4.2 Admin Approval

**Entry point:** `POST /api/v1/delink-requests/{id}/approve` (admin only)

**Request:**

```json
{
  "approved": true
}
```

On `approved: true`, the status transitions from `PENDING` to `PROCESSING`.

On `approved: false`:

```json
{
  "approved": false,
  "reason": "Insufficient evidence of recycling"
}
```

Status transitions to `FAILED` with `error_message` set to the rejection reason.

### 4.3 Delink Execution

When `complete_delink_request()` is called, the following database operations execute in a single transaction:

```text
TRANSACTION BEGIN

  1. IF request_type IN (NIN, BOTH):
       SELECT nin_linkages WHERE msisdn = recycled_sim.msisdn AND is_active = TRUE
       UPDATE nin_linkages SET is_active = FALSE, unlinked_date = NOW()

  2. IF request_type IN (BVN, BOTH):
       SELECT bvn_linkages WHERE msisdn = recycled_sim.msisdn AND is_active = TRUE
       UPDATE bvn_linkages SET is_active = FALSE, unlinked_date = NOW()

  3. UPDATE recycled_sims SET
       cleanup_status = COMPLETED,
       previous_nin_linked = FALSE,
       previous_bvn_linked = FALSE

  4. INSERT INTO notifications (3 records):
       - recipient_type=former_owner, channel=sms, template=delink_complete_former_owner
       - recipient_type=bank, channel=api_callback, template=delink_complete_bank
       - recipient_type=nimc, channel=api_callback, template=delink_complete_nimc

  5. UPDATE delink_requests SET status = COMPLETED, completed_at = NOW()

COMMIT
```

**Tables modified in a single delink execution:**

| Table              | Operation | Fields Changed                                        |
| ------------------ | --------- | ----------------------------------------------------- |
| `nin_linkages`     | UPDATE    | `is_active = FALSE`, `unlinked_date = NOW()`          |
| `bvn_linkages`     | UPDATE    | `is_active = FALSE`, `unlinked_date = NOW()`          |
| `recycled_sims`    | UPDATE    | `cleanup_status`, `previous_nin_linked`, `previous_bvn_linked` |
| `notifications`    | INSERT    | 3 new records (former_owner, bank, nimc)              |
| `delink_requests`  | UPDATE    | `status = COMPLETED`, `completed_at`                  |

### 4.4 State Machine

```text
                  ┌──────────► CANCELLED (by creator or admin)
                  │
  PENDING ────► PROCESSING ────► COMPLETED
                  │                   │
                  └──────► FAILED     ├──► nin_linkages.is_active = FALSE
                                      ├──► bvn_linkages.is_active = FALSE
                                      ├──► recycled_sims.cleanup_status = COMPLETED
                                      └──► 3 notifications created
```

**Interdependency:** This stage reads from `recycled_sims` (Stage 1) to validate the FK, modifies `nin_linkages` and `bvn_linkages` (Stage 3 data sources), and creates records in `notifications` (Stage 5 input).

---

## Stage 5: Notification Dispatch

**Purpose:** Alert affected parties that a delink has been executed.

**Entry point (automatic):** Created by `_create_completion_notifications()` during Stage 4 execution.

**Entry point (manual):** `POST /api/v1/notifications` (admin/operator)

**Notification record schema:**

```json
{
  "delink_request_id": 17,
  "recipient_type": "former_owner",
  "channel": "sms",
  "recipient_address": "+2347012345678",
  "status": "pending",
  "message_template": "delink_complete_former_owner"
}
```

**Supported recipient types:** `former_owner`, `bank`, `nimc`, `new_owner`, `next_of_kin`, `nibss`

**Supported channels:** `sms`, `email`, `api_callback`

**Notification state machine:**

```text
PENDING ──► SENT ──► DELIVERED
                └──► FAILED
```

**Interdependency:** Notifications are always linked to a `delink_requests` record via FK. The `recipient_address` for the `former_owner` type comes from `recycled_sims.msisdn`. Bank and NIMC addresses come from webhook subscription configurations.

---

## Stage 6: Reporting & Identity Corroboration

**Purpose:** Provide a unified view of identity mappings, aggregate dashboard statistics, and cross-reference data across multiple sources.

### 6.1 MSISDN Status Check

**Entry point:** `GET /api/v1/identity/msisdn/{msisdn}/status`

**Response:**

```json
{
  "msisdn": "+2347012345678",
  "status": "CONFLICTED",
  "is_recycled": true,
  "active_nin_linkages": 1,
  "active_bvn_linkages": 1,
  "can_assign_to_new_user": false,
  "cleanup_status": "pending",
  "operator_code": "MTN"
}
```

**Status determination logic:**

| Condition                          | Status       | can_assign_to_new_user |
| ---------------------------------- | ------------ | ---------------------- |
| Recycled AND has active linkages   | `CONFLICTED` | `false`                |
| Recycled AND no active linkages    | `AVAILABLE`  | `true`                 |
| Not recycled AND has linkages      | `ACTIVE`     | `false`                |
| Not recycled AND no linkages       | `AVAILABLE`  | `true`                 |

### 6.2 Full Linkage History

**Entry point:** `GET /api/v1/identity/msisdn/{msisdn}/linkages`

**Response:**

```json
{
  "msisdn": "+2347012345678",
  "nin_linkages": [
    {
      "nin": "12345678901",
      "is_active": false,
      "source": "nimc_api",
      "linked_date": "2022-06-15T00:00:00Z",
      "unlinked_date": "2024-03-01T15:30:00Z"
    }
  ],
  "bvn_linkages": [
    {
      "bvn": "10987654321",
      "bank_code": "007",
      "is_active": false,
      "source": "nibss_api",
      "linked_date": "2021-09-20T00:00:00Z",
      "unlinked_date": "2024-03-01T15:30:00Z"
    }
  ],
  "total_nin": 1,
  "total_bvn": 1,
  "active_nin": 0,
  "active_bvn": 0
}
```

This returns both active and historical (delinked) records, providing a complete audit trail.

### 6.3 Unified Identity Mapping

**Entry point:** `GET /api/v1/identity/lookup?msisdn=+2347012345678`

**Response:**

```json
{
  "msisdn": "+2347012345678",
  "nin": "12345678901",
  "bvn": "10987654321",
  "operator_code": "MTN",
  "is_recycled": true,
  "nin_linkage_active": false,
  "bvn_linkage_active": false,
  "confidence_score": 0.85,
  "conflicts": null,
  "sources_consulted": [
    {"name": "reconix_sims", "available": true},
    {"name": "reconix_nin", "available": true},
    {"name": "reconix_bvn", "available": true}
  ],
  "last_verified": "2024-03-01T12:00:00Z",
  "assessed_at": "2024-03-01T16:00:00Z"
}
```

### 6.4 Confidence Score Algorithm

```text
source_ratio = available_sources / total_sources

data_completeness = count_of(
    nin IS NOT NULL,
    bvn IS NOT NULL,
    operator_code IS NOT NULL,
    is_recycled IS NOT NULL
) / 4

conflict_penalty = MIN(conflict_count * 0.25, 0.5)

confidence_score = MAX(0.0, MIN(1.0,
    source_ratio * 0.4 + data_completeness * 0.6 - conflict_penalty
))
```

### 6.5 External Corroboration

**Entry point:** `GET /api/v1/identity/corroborate?msisdn=+2347012345678` (admin only)

**Processing flow:**

```text
1. Load local data (same as /lookup)
2. Call NIMCAdapter.get_nin_for_msisdn(msisdn) → external_nin
3. Call NIBSSAdapter.get_bvn_for_msisdn(msisdn) → external_bvn
4. Call TelecomAdapter.get_sim_status(msisdn) → external_recycled

5. Compare:
   IF external_nin != local_nin → append conflict
   IF external_bvn != local_bvn → append conflict
   IF external_recycled != local_is_recycled → append conflict

6. Recompute confidence_score with new sources and penalties
7. Return IdentityMapping with all sources listed
```

**Conflict record format:**

```json
{
  "field": "nin",
  "local_value": "12345678901",
  "external_value": "99887766554",
  "external_source": "nimc_api",
  "resolution": "requires_manual_review"
}
```

**Interdependency:** This stage reads from all prior stages — `recycled_sims`, `nin_linkages`, `bvn_linkages`, and optionally calls external APIs. It is purely read-only and never modifies data.

### 6.6 Dashboard Statistics

**Entry point:** `GET /api/v1/dashboard/stats` (routed to read replica)

**Response:**

```json
{
  "total_recycled_sims": 50000,
  "total_cleanup_pending": 12000,
  "total_cleanup_in_progress": 500,
  "total_cleanup_completed": 35000,
  "total_cleanup_failed": 2500,
  "active_nin_linkages": 8500,
  "active_bvn_linkages": 6200,
  "total_delink_requests": 40000,
  "delink_pending": 1500,
  "delink_completed": 35000,
  "delink_failed": 3500
}
```

**SQL queries (all COUNT aggregates, run on read replica):**

```text
COUNT(recycled_sims) GROUP BY cleanup_status
COUNT(nin_linkages) WHERE is_active = TRUE
COUNT(bvn_linkages) WHERE is_active = TRUE
COUNT(delink_requests) GROUP BY status
```

---

## Middleware Pipeline

Every HTTP request passes through 14 middleware layers before reaching the route handler. The middleware executes in this order (outermost to innermost):

```text
Request ──► CORS ──► SizeLimiter ──► InputGuard ──► RequestID ──► SecurityHeaders
         ──► CustomSecurity ──► AuditLogger ──► Metrics ──► Idempotency
         ──► SunsetHeaders ──► Tracing ──► Sentry ──► HTTPS ──► Route Handler
```

### Request tracing headers

Every response includes:

```text
X-Request-ID: <uuid>       (correlation ID, propagated or generated)
X-Trace-ID: <32-char hex>  (distributed trace ID)
X-Span-ID: <16-char hex>   (span within the trace)
API-Version: v1            (current API version)
```

### Input Guard scanning

The `InputSanitizationMiddleware` scans both URL query strings (URL-decoded) and JSON request bodies (up to 64KB, nested to depth 5) against 13 regex patterns covering SQL injection, XSS, shell execution, path traversal, and null byte injection. Blocked requests receive HTTP 400 before reaching the route handler.

---

## Authentication & Token Lifecycle

```text
Login ──► access_token (24h TTL, unique JTI)
          refresh_token (7d TTL, unique JTI)
               │
               ├─ API request ──► JWT verified ──► JTI checked against revoked_tokens
               │
               ├─ Refresh ──► old refresh JTI revoked ──► new pair issued
               │
               └─ Logout ──► access JTI revoked ──► subsequent use returns 401
```

**JWT payload (access token):**

```json
{
  "sub": "3",
  "email": "operator@reconix.ng",
  "role": "operator",
  "type": "access",
  "jti": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
  "iat": 1709308800,
  "exp": 1709395200
}
```

**JWT algorithm whitelist:** HS256, HS384, HS512 only. Any other value (including "none") causes the application to exit on startup.

---

## Sync Orchestrator

The sync orchestrator pulls data from external stakeholder systems into Reconix. It does not write to any external system.

```text
SyncOrchestrator.sync_all()
  │
  ├── For each active Stakeholder WHERE status = ACTIVE:
  │     │
  │     ├── NIMC stakeholder:
  │     │     Get SIMs needing NIN check (previous_nin_linked=true, pending)
  │     │     Call NIMCAdapter.get_nin_for_msisdn() for each
  │     │     Create NINLinkage if new data found
  │     │
  │     ├── NIBSS stakeholder:
  │     │     Get SIMs needing BVN check (previous_bvn_linked=true, pending)
  │     │     Call NIBSSAdapter.get_bvn_for_msisdn() for each
  │     │     Create BVNLinkage if new data found
  │     │
  │     └── Telecom stakeholder:
  │           Call TelecomAdapter.get_recycled_sims(since=last_sync)
  │           Create RecycledSIM for each new MSISDN
  │
  └── Update stakeholder.last_sync_at, last_sync_status, last_sync_records
```

**Outbound adapter security:**

- HTTPS only (HTTP blocked)
- SSRF protection: private IPs, loopback, `.internal`, `.local`, `169.254.169.254` blocked
- No redirect following (`follow_redirects=False`)
- Per-stakeholder rate limiting (configurable, default 60/min)
- Configurable timeout (default 30s)
- TLS verification enabled

---

## WebSocket Real-Time Notifications

**Connection:** `ws://host/ws/{channel}?token=<jwt>`

**Allowed channels:** `notifications`, `delink_updates`, `sim_alerts`, `system`

**Connection limits:** 5 connections per user across all channels

**Message format (JSON text frame):**

```json
{
  "type": "delink_completed",
  "data": {
    "delink_request_id": 17,
    "msisdn": "+2347012345678",
    "status": "completed"
  },
  "timestamp": "2024-03-01T15:30:00Z"
}
```

**Ping/pong:** Client sends `"ping"` text, server responds with `"pong"` text. Used for keepalive.
