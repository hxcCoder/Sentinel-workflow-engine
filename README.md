# SentinelLab

A defensive security backend built for learning and demonstrating real-world
backend security concepts: authentication, audit logging, RBAC, rule-based
detection, and alert lifecycle management.

## What it does

- JWT authentication with refresh token rotation
- Role-based access control: admin, analyst, viewer
- Structured audit logging
- Rule-based detection engine
- Alert persistence and lifecycle tracking
- AppSec lab, file analysis, MITRE enrichment, and reporting are planned

## Stack

- Backend: Python, FastAPI
- Database: PostgreSQL, SQLAlchemy async
- Migrations: Alembic
- Auth: JWT, bcrypt, refresh token rotation

## Status

Active development, building milestone by milestone. The current source of
truth is [docs/architecture-registry.md](docs/architecture-registry.md).

| Milestone | Status |
|---|---|
| M1: Foundation and config | Done |
| M2: Auth, JWT, RBAC | Done |
| M3: Audit system | Done |
| M4: Detection engine | Done |
| M5: Alerts and operational closure | Done for current scope |
| M6: AppSec lab | Planned |
| M7: File analyzer | Planned |
| M8: Blue Team and MITRE | Planned |
| M9: Reports | Planned |

## Run locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Documentation

- [North Star](northstar.md)
- [Architecture registry](docs/architecture-registry.md)
- [Session log](docs/session-log.md)

## System flow

```mermaid
flowchart TD
    EXT["External apps\nGaleria Puerto / others"]

    subgraph API ["API Layer - /api/v1/"]
        R_AUTH["routes/auth.py\nregister / login / refresh / logout"]
        R_ALERTS["routes/alerts.py\nlist / get / update"]
        R_DET["routes/detection.py\nmanual detection run"]
        DEPS["deps.py\nget_current_user() / require_roles()"]
    end

    subgraph SERVICES ["Services"]
        SVC_AUTH["AuthService\nJWT / bcrypt / refresh rotation"]
        SVC_AUDIT["AuditService\nimmutable event log"]
        SVC_ALERT["AlertService\nupsert by fingerprint / lifecycle"]
        SVC_AEV["AlertEventService\ntimeline / snapshot"]
    end

    subgraph DETECTION ["Detection Engine"]
        SCHED["APScheduler\n5 minute detection cycle"]
        ENGINE["DetectionEngine\nrun(db, start, end)"]
        BASE["DetectionRule ABC\nevaluate(db, start, end)"]
        R001["AUTH_001\nBruteforce by IP"]
        R002["AUTH_002\nSuspicious refresh by IP"]
    end

    subgraph MODELS ["Models - PostgreSQL"]
        M_USER["users\nid / email / role / is_active"]
        M_RT["refresh_tokens\ntoken_hash / revoked_at / expires_at"]
        M_AUDIT["audit_logs\nevent_type / actor_id / ip_address / severity"]
        M_ALERT["alerts\nfingerprint / rule_id / severity / status"]
        M_AEV["alert_events\nalert_id / event_type / snapshot"]
    end

    EXT -. planned ingest .-> R_DET
    R_AUTH --> DEPS
    R_ALERTS --> DEPS
    R_DET --> DEPS

    R_AUTH --> SVC_AUTH
    R_ALERTS --> SVC_ALERT
    R_DET --> ENGINE

    SVC_AUTH --> SVC_AUDIT
    SVC_AUTH --> M_USER
    SVC_AUTH --> M_RT

    SVC_AUDIT --> M_AUDIT
    SVC_ALERT --> SVC_AEV
    SVC_ALERT --> M_ALERT
    SVC_AEV --> M_AEV

    ENGINE --> BASE
    BASE --> R001
    BASE --> R002
    R001 --> M_AUDIT
    R002 --> M_AUDIT
    ENGINE --> SVC_ALERT

    SCHED --> ENGINE
```
