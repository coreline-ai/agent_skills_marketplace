# Rollback Procedure

## Scope
Rollback target for deployment issues in API/Web/Worker containers and schema changes.

## 1) Immediate Stabilization
1. Stop traffic or switch LB target to previous healthy environment.
2. Freeze admin mutations (ingest/manual update/API key issuance) during rollback window.

## 2) Application Rollback
1. Checkout previous release tag/commit.
2. Rebuild and restart services:
   ```bash
   docker-compose up --build -d
   ```
3. Verify:
   - `GET /health` on API and Web
   - `GET /api/admin/worker-status` heartbeat

## 3) Database Rollback
1. Check current Alembic revision:
   ```bash
   docker-compose exec -T api alembic current
   ```
2. Downgrade one revision if the latest migration caused failure:
   ```bash
   docker-compose exec -T api alembic downgrade -1
   ```
3. Re-run API/Web smoke tests.

## 4) Post-Rollback Checks
1. Public read path:
   - `GET /api/skills?size=1`
   - `GET /api/skills/search/ai?q=coding`
2. Admin path:
   - login token issuance
   - dashboard stats
3. Developer API path:
   - API key auth success/failure cases
   - rate limit behavior

## 5) Incident Notes
Record:
- rollback start/end time
- affected release hash
- downgraded migration revision (if any)
- user-facing impact window
- follow-up fix owner and ETA
