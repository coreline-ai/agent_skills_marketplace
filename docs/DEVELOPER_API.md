# Developer API Productization

## API Key Lifecycle
- Issue: `POST /api/admin/api-keys`
- Revoke: `POST /api/admin/api-keys/{id}/revoke`
- Rotate: `POST /api/admin/api-keys/{id}/rotate`
- List: `GET /api/admin/api-keys`
- Usage: `GET /api/admin/api-keys/{id}/usage`

## Auth & Scope
- Header: `x-api-key: <plain_key>`
- Optional: `Authorization: Bearer <plain_key>`
- Scope enforcement:
  - required scope: `read` (for developer read endpoints)

## Rate Limit
- Per-key minute window (`rate_limit_per_minute`)
- Over-limit response:
  - HTTP `429`
  - detail.code: `rate_limit_exceeded`

## Usage Aggregation
- Daily usage table: `api_key_usage_daily`
- Monthly usage table: `api_key_usage_monthly`
- Developer self usage:
  - `GET /api/developer/usage`

## Developer Endpoints
- `GET /api/developer/skills`
- `GET /api/developer/skills/{id}`
- `GET /api/developer/usage`

## Sandbox Key / Test Guide
Use a short-lived low-rate key for development tests:

```bash
curl -X POST "http://localhost:8000/api/admin/api-keys" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "sandbox-local",
    "scopes": ["read"],
    "rate_limit_per_minute": 3,
    "expires_at": "2026-12-31T23:59:59Z"
  }'
```

Then call:

```bash
curl -H "x-api-key: $API_KEY" "http://localhost:8000/api/developer/skills?q=agent&size=5"
```

## Standard Error Payload
All API key errors return:

```json
{
  "detail": {
    "message": "human readable message",
    "code": "machine_readable_code"
  }
}
```
