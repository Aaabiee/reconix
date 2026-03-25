---
title: Deployment
nav_order: 7
---

# Reconix — Deployment

---

## Architecture

```text
                    Internet
                       │
                 [Load Balancer]
                   /         \
          [Frontend]         [Backend]
          Next.js 16         FastAPI + Gunicorn
          Port 3000          Port 8000
                               │
                      ┌────────┴────────┐
                      │                 │
                [PostgreSQL 16]   [Read Replica]
                 Port 5432         (optional)
                      │
                   [Redis]
                 Port 6379
               (optional cache)
```

---

## Docker

### Backend Dockerfile

- **Base**: Python 3.12-slim
- **Server**: Gunicorn with Uvicorn workers via `gunicorn.conf.py`
- **Workers**: Dynamic (`CPU * 2 + 1`, max 9), with `preload_app` and `max_requests=2000`
- **User**: Non-root (`reconix` user)
- **Health check**: `GET /health` every 30s
- **Graceful shutdown**: 35s stop grace period
- **DB startup**: Retry with exponential backoff (5 attempts)

### Frontend Dockerfile

- **Build**: Multi-stage Node.js build
- **Output**: Standalone Next.js
- **CDN**: `NEXT_PUBLIC_CDN_URL` for static asset prefix

### Docker Compose

```bash
# Local development (all services)
docker compose up -d

# Services:
# - Backend:  http://localhost:8000
# - Frontend: http://localhost:3000
# - Health:   http://localhost:8000/health
# - Metrics:  http://localhost:8000/metrics
```

---

## Database Migrations (Alembic)

```bash
# Apply all pending migrations
pipenv run migrate

# Generate a new migration from model changes
pipenv run makemigration -m "add stakeholder table"

# Check current migration state
pipenv run alembic -c fast_api/alembic.ini current
```

Alembic is configured for async operation with all 12 ORM models auto-imported in `fast_api/alembic/env.py`.

---

## Initial Setup (Seed Admin)

```bash
# Create the first admin user (password via prompt or ADMIN_PASSWORD env var)
pipenv run seed --email admin@reconix.ng --name "System Administrator"

# Or with env var (for CI/automation)
ADMIN_PASSWORD="your-secure-password" pipenv run seed
```

The seed script validates 12-character minimum passwords, skips if the user already exists, and never accepts passwords via CLI arguments (prevents shell history leaks).

---

## CI/CD Pipeline

GitHub Actions (`.github/workflows/ci.yml`):

1. **Lint** — Python and TypeScript linting
2. **Type-check** — `tsc --noEmit`
3. **SCSS check** — Validate component stylesheets
4. **Backend tests** — `pytest -q`
5. **Frontend tests** — `jest --coverage`
6. **Docker build** — Build and validate container images
7. **Security scan** — `pip-audit` + `npm audit` + Semgrep SAST

---

## Environment Variables

| Variable                    | Required   | Default                     | Description                            |
| --------------------------- | ---------- | --------------------------- | -------------------------------------- |
| `DATABASE_URL`              | Yes        | —                           | PostgreSQL connection string           |
| `JWT_SECRET_KEY`            | Yes        | —                           | Min 32 chars, HS256 signing key        |
| `FIELD_ENCRYPTION_KEY`      | Yes (prod) | —                           | Min 32 chars, PII encryption key       |
| `ENVIRONMENT`               | No         | `development`               | development, testing, production       |
| `CORS_ORIGINS`              | No         | `["http://localhost:3000"]`  | Allowed origins (HTTPS in prod)        |
| `ENABLE_JSON_LOGGING`       | No         | `true`                      | Structured JSON log output             |
| `ENABLE_METRICS`            | No         | `true`                      | Expose `/metrics` endpoint             |
| `ENABLE_IDEMPOTENCY`        | No         | `true`                      | Enable idempotency key middleware      |
| `ENABLE_TRACING`            | No         | `true`                      | Enable distributed tracing middleware  |
| `ENABLE_WEBSOCKET`          | No         | `true`                      | Enable WebSocket endpoint              |
| `AUDIT_LOG_RETENTION_DAYS`  | No         | `365`                       | Days before audit logs are purged      |
| `SENTRY_DSN`                | No         | —                           | Sentry DSN for error tracking          |
| `REDIS_URL`                 | No         | —                           | Redis connection URL                   |
| `VAULT_URL`                 | No         | —                           | HashiCorp Vault server URL             |
| `VAULT_TOKEN`               | No         | —                           | Vault authentication token             |
| `DATABASE_READ_REPLICA_URL` | No         | —                           | Read replica for dashboard queries     |
| `NEXT_PUBLIC_CDN_URL`       | No         | —                           | CDN prefix for static assets           |

---

## Production Validation

On startup with `ENVIRONMENT=production`, the following are enforced:

- `JWT_SECRET_KEY` must be set and at least 32 characters
- `DATABASE_URL` must not contain default credentials
- `CORS_ORIGINS` must use HTTPS
- `DATABASE_ECHO_SQL` must be `false`
- `DEBUG` must be `false`
- `FIELD_ENCRYPTION_KEY` must be at least 32 characters

Failure to pass any check causes the application to exit with a critical error.

---

## Backup & Restore

### Backup

```bash
python scripts/backup_db.py --output-dir /backups --retention-days 30
```

- Uses `pg_dump` with custom format and compression level 9
- Creates timestamped files: `reconix_<db>_<timestamp>.sql.gz`
- Sets file permissions to `0o600` (owner read/write only)
- Cleans up backups older than retention period
- No `shell=True` (command injection safe)

### Restore

```bash
python scripts/restore_db.py --backup-file backups/reconix_reconix_20240301.sql.gz --confirm
```

- Validates backup file path (blocks path traversal)
- Uses `pg_restore` with `--clean --if-exists`
- Requires explicit `--confirm` flag or interactive confirmation

---

## Health Monitoring

### Health Check Endpoints

| Endpoint            | Purpose                                       |
| ------------------- | --------------------------------------------- |
| `GET /health`       | Full health with DB pool info (200 or 503)    |
| `GET /health/live`  | Liveness probe, always returns 200            |
| `GET /health/ready` | Readiness probe, 503 until DB connected       |
| `GET /metrics`      | Prometheus metrics (restricted in production) |

`GET /health` returns:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "pool": {
    "pool_size": 20,
    "checked_in": 18,
    "checked_out": 2,
    "overflow": 0
  }
}
```

### Uptime Poller

```bash
# Run once
python scripts/health_check.py --url http://localhost:8000/health

# Continuous polling with Slack alerts
python scripts/health_check.py --url https://api.reconix.ng/health \
  --interval 30 --webhook https://hooks.slack.com/...
```
