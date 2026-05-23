# SentinelLab Architecture Registry

Single source of truth for the current backend architecture. Update this file at
the end of every working session when architecture, behavior, milestones, or
known gaps change.

## Last updated

2026-05-23

## Current session summary

M5 operational closure completed for the current backend scope:

- alert repository added
- alert route/service API aligned
- lifecycle endpoints added
- alert timeline endpoint added
- scheduler startup/shutdown wired into FastAPI lifespan
- detection job now tracks `_last_run`

## Next concrete step

Decide the next milestone:

- M6 AppSec Lab, or
- harden ingest first by implementing authenticated `/api/v1/ingest/events`.

## System identity

| Field | Value |
|---|---|
| Project | SentinelLab |
| Type | Security Event Processing Engine (SEPE) |
| Stack | FastAPI, SQLAlchemy async, PostgreSQL, Alembic |
| Auth | JWT access token, refresh rotation, bcrypt, RBAC |
| Architecture stage | M5 - operational closure complete for current scope |
| Backend maturity | Regular to professional transition |

## Current reality check

| Area | Current state | Notes |
|---|---|---|
| Auth | Implemented | JWT, refresh tokens, bcrypt, RBAC roles |
| Audit | Implemented | `AuditLog` plus `AuditService` |
| Detection engine | Implemented | Rule loop with isolated rule failure handling |
| Detection rules | Implemented | Manual route and scheduler both include `AUTH_001` and `AUTH_002` |
| Alerts | Implemented | Model, upsert, lifecycle methods, API routes, timeline endpoint |
| Alert API | Implemented | List, get, update, acknowledge, resolve, false positive, reopen, timeline |
| Scheduler | Implemented | APScheduler wrapper starts/stops from FastAPI lifespan |
| Repositories | Started | `AlertRepository` owns alert read queries |
| Domain | Empty | `app/domain/__init__.py` only |

## Module map

```text
app/
+-- main.py                         # FastAPI app, lifespan, route registration
+-- api/
|   +-- deps.py                     # auth dependencies and role guards
|   +-- v1/routes/
|       +-- auth.py                 # auth endpoints
|       +-- alerts.py               # alert list/get/update/lifecycle/timeline
|       +-- detection.py            # manual detection run route
+-- core/
|   +-- config.py                   # settings
|   +-- logging.py                  # structured logging setup
|   +-- security.py                 # JWT, password hashing, refresh hash
+-- db/
|   +-- base.py                     # SQLAlchemy DeclarativeBase
|   +-- session.py                  # async session factory and dependency
+-- detection/
|   +-- base.py                     # DetectionRule ABC and DetectionFinding
|   +-- engine.py                   # DetectionEngine
|   +-- rules/
|       +-- auth_bruteforce.py      # AUTH_001
|       +-- suspicious_refresh.py   # AUTH_002
+-- models/
|   +-- user.py
|   +-- refresh_token.py
|   +-- audit_log.py
|   +-- alert.py
|   +-- alert_event.py
+-- repositories/
|   +-- __init__.py
|   +-- alert_repository.py         # alert read queries
+-- scheduler/
|   +-- scheduler.py                # APScheduler start/stop/status
|   +-- jobs/detection_job.py       # run_detection_cycle()
+-- schemas/
|   +-- auth.py
|   +-- user.py
|   +-- alert.py
|   +-- alert_event.py
|   +-- detection.py
+-- services/
    +-- auth_service.py
    +-- audit_service.py
    +-- alert_service.py
    +-- alert_event_service.py
```

## Detection rules registry

| ID | Class | Trigger | Severity | Threshold |
|---|---|---|---|---|
| AUTH_001 | `AuthBruteforceRule` | repeated login failures by IP | high | 5 by default |
| AUTH_002 | `SuspiciousRefreshRule` | repeated refresh events by IP | medium to critical | 8 / 20 in scheduler job |

## Detection execution paths

| Path | Status | Behavior |
|---|---|---|
| `POST /api/v1/detection/run` | Present | Runs `DetectionEngine` for a requested time window with `AUTH_001` and `AUTH_002` |
| `run_detection_cycle()` | Present | Runs both rules from `_last_run` or the last 5 minutes and upserts findings |
| APScheduler startup | Implemented | `main.py` starts/stops scheduler in lifespan |
| `_last_run` tracking | Implemented | Updated only after a successful detection cycle |

## Alert API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/alerts/` | List alerts with status, severity, rule, source, limit, offset filters |
| GET | `/api/v1/alerts/{alert_id}` | Get one alert |
| PATCH | `/api/v1/alerts/{alert_id}` | Generic alert metadata/status update |
| POST | `/api/v1/alerts/{alert_id}/acknowledge` | Move open alert to `in_progress` |
| POST | `/api/v1/alerts/{alert_id}/resolve` | Resolve an alert with optional notes |
| POST | `/api/v1/alerts/{alert_id}/false-positive` | Mark alert as false positive with optional notes |
| POST | `/api/v1/alerts/{alert_id}/reopen` | Reopen a resolved or false-positive alert |
| GET | `/api/v1/alerts/{alert_id}/timeline` | Return alert timeline events |

## Alert lifecycle states

```text
open
  -> in_progress
  -> resolved
  -> false_positive

resolved / false_positive
  -> open via reopen()
```

Current model enum values:

- `open`
- `in_progress`
- `resolved`
- `false_positive`

## Database tables

| Table | Purpose |
|---|---|
| `users` | SentinelLab users and RBAC role |
| `refresh_tokens` | refresh token rotation and revocation |
| `audit_logs` | immutable security/audit events |
| `alerts` | deduplicated detection findings by fingerprint |
| `alert_events` | alert timeline events and snapshots |

## Alembic migrations

```text
6bcb71fff912_create_users_and_refresh_tokens_tables.py
d5e914c3a171_create_audit_logs_table.py
8b6d1f39eebf_add_audit_log_detection_indexes.py
1acd54906d64_create_alerts_table.py
43bcd5d9516d_create_alert_events_table.py
60c101305e48_add_alerts_indexes.py
662504550980_rename_assigned_to_user_id_to_assigned_.py
```

## Known technical debt

| Item | Risk | Priority |
|---|---|---|
| `domain/` empty | Intent unclear; may drift or become dead architecture | Medium |
| No ingest endpoint found in current routes | External event contract is not implemented in current route map | High |
| Repository pattern only started with alerts | Auth/audit services still own SQLAlchemy query details | Medium |

## External integration intent

External applications should eventually send security events to SentinelLab. The
intended contract is:

```json
{
  "event_type": "string",
  "timestamp": "ISO8601",
  "actor_id": "string or null",
  "metadata": {},
  "source_app": "galeria-puerto"
}
```

Current code reality: no `/api/v1/ingest/events` route was found in the current
route map. The closest implemented entry point is manual detection execution at
`POST /api/v1/detection/run`.

## Documentation rules

- `README.md` is for onboarding and a brief public overview.
- `northstar.md` is for direction and product boundaries.
- `docs/architecture-registry.md` is the technical source of truth.
- `docs/session-log.md` is the atomic change log.
- Document what exists in code. Put planned work in next steps or debt.
- If docs and code disagree, code wins and docs must be updated.
