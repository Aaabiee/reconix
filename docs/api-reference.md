---
title: API Reference
nav_order: 5
---

# Reconix — API Reference

All endpoints are under the `/api/v1` prefix. Authentication uses JWT Bearer tokens unless otherwise noted.

---

## Authentication

| Method | Endpoint             | Auth   | Description                                          |
| ------ | -------------------- | ------ | ---------------------------------------------------- |
| `POST` | `/auth/login`        | Public | Authenticate, returns JWT + refresh token            |
| `POST` | `/auth/refresh`      | Public | Rotate refresh token (one-time use, old JTI revoked) |
| `POST` | `/auth/logout`       | Bearer | Revoke access token JTI                              |

### Login

```text
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "operator@reconix.ng",
  "password": "your-password-here"
}
```

**Response (200):**

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 86400
}
```

**Error responses:** 401 (invalid credentials), 423 (account locked), 429 (rate limited)

---

## Recycled SIMs

| Method  | Endpoint              | Auth           | Description                         |
| ------- | --------------------- | -------------- | ----------------------------------- |
| `GET`   | `/recycled-sims`      | Bearer         | List recycled SIMs (paginated)      |
| `POST`  | `/recycled-sims`      | Admin/Operator | Register a recycled SIM             |
| `POST`  | `/recycled-sims/bulk` | Admin          | Bulk upload (up to 10,000 records)  |
| `GET`   | `/recycled-sims/{id}` | Bearer         | SIM detail view                     |
| `PATCH` | `/recycled-sims/{id}` | Admin/Operator | Update cleanup status               |

**Query parameters for list:** `skip` (default 0), `limit` (1-100, default 50), `cleanup_status` (optional filter)

---

## NIN Linkages

| Method | Endpoint                  | Auth   | Description                             |
| ------ | ------------------------- | ------ | --------------------------------------- |
| `POST` | `/nin-linkages/verify`    | Bearer | Verify NIN linkage for an MSISDN        |
| `POST` | `/nin-linkages/bulk-check`| Bearer | Batch NIN check (single query, no N+1)  |

---

## BVN Linkages

| Method | Endpoint                  | Auth   | Description                             |
| ------ | ------------------------- | ------ | --------------------------------------- |
| `POST` | `/bvn-linkages/verify`    | Bearer | Verify BVN linkage for an MSISDN        |
| `POST` | `/bvn-linkages/bulk-check`| Bearer | Batch BVN check (single query, no N+1)  |

---

## Delink Requests

| Method | Endpoint                            | Auth           | Description                |
| ------ | ----------------------------------- | -------------- | -------------------------- |
| `GET`  | `/delink-requests`                  | Bearer         | List delink requests       |
| `POST` | `/delink-requests`                  | Admin/Operator | Create delink request      |
| `GET`  | `/delink-requests/{id}`             | Bearer         | Delink request detail      |
| `POST` | `/delink-requests/{id}/approve`     | Admin          | Approve or reject          |
| `POST` | `/delink-requests/{id}/cancel`      | Admin/Operator | Cancel pending/processing  |

---

## Notifications

| Method | Endpoint                | Auth           | Description                    |
| ------ | ----------------------- | -------------- | ------------------------------ |
| `GET`  | `/notifications`        | Bearer         | List notifications (paginated) |
| `POST` | `/notifications`        | Admin/Operator | Send notification              |
| `GET`  | `/notifications/{id}`   | Bearer         | Notification detail            |

---

## Dashboard

| Method | Endpoint            | Auth   | Description                    |
| ------ | ------------------- | ------ | ------------------------------ |
| `GET`  | `/dashboard/stats`  | Bearer | Aggregated statistics          |
| `GET`  | `/dashboard/trends` | Bearer | Trends over configurable period|

Dashboard queries are routed to the read replica when configured.

---

## Audit Logs

| Method | Endpoint     | Auth          | Description                |
| ------ | ------------ | ------------- | -------------------------- |
| `GET`  | `/audit-logs`| Admin/Auditor | Immutable audit trail      |

---

## NDPR Data Subject Rights

| Method | Endpoint                        | Auth   | Description                          |
| ------ | ------------------------------- | ------ | ------------------------------------ |
| `GET`  | `/data-subject/privacy-policy`  | Public | NDPR privacy policy                  |
| `GET`  | `/data-subject/my-data`         | Bearer | Export personal data                 |
| `POST` | `/data-subject/delete-my-data`  | Bearer | Request data deletion                |
| `GET`  | `/data-subject/consent`         | Bearer | View consent record                  |
| `POST` | `/data-subject/access-request`  | Bearer | Submit NDPR data subject request     |

---

## Identity Mapping (One-Stop-Shop)

Reconix aggregates data from NIMC, NIBSS, telecoms, and banks to provide a unified view of MSISDN-to-identity mappings. All endpoints are read-only — Reconix does not write to any stakeholder system.

| Method | Endpoint                              | Auth           | Description                                      |
| ------ | ------------------------------------- | -------------- | ------------------------------------------------ |
| `GET`  | `/identity/msisdn/{number}/status`    | Bearer         | MSISDN lifecycle status, assignment readiness    |
| `GET`  | `/identity/msisdn/{number}/linkages`  | Bearer         | Full NIN/BVN linkage history for an MSISDN       |
| `GET`  | `/identity/lookup?msisdn={number}`    | Bearer         | Unified identity mapping with confidence score   |
| `POST` | `/identity/batch-lookup`              | Admin/Operator | Batch lookup up to 100 MSISDNs                   |
| `GET`  | `/identity/corroborate?msisdn={num}`  | Admin          | Live cross-reference with external NIMC/NIBSS    |
| `GET`  | `/identity/conflicts`                 | Admin/Auditor  | List MSISDNs with conflicting data across sources|

### MSISDN Status Response

```json
{
  "msisdn": "+2348012345678",
  "status": "CONFLICTED",
  "is_recycled": true,
  "active_nin_linkages": 1,
  "active_bvn_linkages": 1,
  "can_assign_to_new_user": false,
  "cleanup_status": "pending",
  "operator_code": "MTN"
}
```

Possible `status` values: `ACTIVE`, `RECYCLED`, `CONFLICTED`, `BLOCKED`, `AVAILABLE`

The `can_assign_to_new_user` field tells telecoms whether a recycled number is safe to reassign. A number is only assignable when all old NIN/BVN linkages have been cleared via the delink workflow.

---

## Webhooks

| Method   | Endpoint                          | Auth           | Description                 |
| -------- | --------------------------------- | -------------- | --------------------------- |
| `POST`   | `/webhooks/register`              | Admin/Operator | Register webhook            |
| `POST`   | `/webhooks/receive`               | API Key        | Receive external webhook    |
| `GET`    | `/webhooks/subscriptions`         | Bearer         | List subscriptions          |
| `DELETE` | `/webhooks/subscriptions/{id}`    | Admin          | Deactivate subscription     |

---

## Infrastructure Endpoints

| Method | Endpoint   | Auth   | Description                       |
| ------ | ---------- | ------ | --------------------------------- |
| `GET`  | `/health`  | Public | Health check with DB pool status  |
| `GET`  | `/metrics` | Public | Prometheus-compatible metrics     |
| `WS`   | `/ws/{ch}` | Bearer | WebSocket real-time notifications |

### WebSocket Channels

Connect via `ws://host/ws/{channel}?token=<jwt>`. Available channels: `notifications`, `delink_updates`, `sim_alerts`, `system`.

---

## Rate Limiting

| Scope          | Limit       |
| -------------- | ----------- |
| Auth endpoints | 5 per minute|
| General API    | 100 per minute|
| NDPR access    | 10 per minute|
| NDPR deletion  | 2 per hour  |

---

## Pagination

All list endpoints accept:

- `skip` — offset (default: 0, min: 0)
- `limit` — page size (default: 50, min: 1, max: 100)

Response format:

```json
{
  "items": [...],
  "total": 150,
  "skip": 0,
  "limit": 50
}
```
