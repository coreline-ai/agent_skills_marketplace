# Trust Layer Design

## Displayed Signals
- `source`: skill source URL / source links
- `trust_last_verified_at`: last verification timestamp
- `quality_score`: parser/quality validator score
- `trust_score`: computed trust score (0-100)
- `trust_level`: `ok | warning | limited`
- `trust_flags`: risk/quality/freshness indicators

## Score Formula

```text
trust_score =
  quality_score * 0.45
  + security_score * 0.25
  + verification_score * 0.10
  + official_score * 0.05
  + freshness_score * 0.15
```

- `security_score`: lowered when scan detects blockable risk
- `freshness_score`: based on `github_updated_at`
- output range: `0..100`

## Exposure Policy
- `limited` and `trust_score < 35` rows are hidden in public listing.
- others remain visible but are ranked down via trust secondary sort.

## Operations
- Admin override endpoint:
  - `POST /api/admin/skills/{id}/trust-override`
- Audit history endpoint:
  - `GET /api/admin/skills/{id}/trust-audit`
- Audit table:
  - `skill_trust_audits` (`actor`, `action`, `reason`, `before`, `after`)
