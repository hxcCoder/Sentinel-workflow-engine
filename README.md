# SentinelLab

A defensive security platform built for learning and demonstrating 
real-world backend security concepts — threat detection, audit logging, 
RBAC, and AppSec analysis.

## What it does

- JWT authentication with refresh token rotation
- Role-based access control (admin, analyst, viewer)
- Structured audit logging (JSON)
- Threat detection engine with Sigma-style rules
- AppSec lab with intentionally vulnerable endpoints (OWASP Top 10)
- Static file analyzer (hashes, strings, metadata)
- MITRE ATT&CK log ingestion and classification
- PDF report generation

## Stack

- **Backend:** Python + FastAPI
- **Database:** PostgreSQL + SQLAlchemy (async)
- **Cache/Queue:** Redis + ARQ
- **Migrations:** Alembic
- **Auth:** JWT + bcrypt + refresh token rotation

## Status

Active development — building milestone by milestone.

| Milestone | Status |
|-----------|--------|
| M1: Foundation & Config | ✅ Done |
| M2: Auth, JWT, RBAC | ✅ Done |
| M3: Audit System | 🔨 In progress |
| M4: Detection Engine | ⏳ Pending |
| M5: Alerts | ⏳ Pending |
| M6: AppSec Lab | ⏳ Pending |
| M7: File Analyzer | ⏳ Pending |
| M8: Blue Team + MITRE | ⏳ Pending |
| M9: Reports | ⏳ Pending |

## Run locally

```bash
# Clone and setup
git clone https://github.com/hxcCoder/Sentinel-workflow-engine
cd Sentinel-workflow-engine

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your values

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

## Graphics:

# SentinelLab — Architecture

## System flow

```mermaid
flowchart TD
    EXT["🌐 External apps\nGalería Puerto / others"]

    subgraph API ["API Layer — /api/v1/"]
        R_AUTH["routes/auth.py\nregister · login · refresh · logout"]
        R_ALERTS["routes/alerts.py\nlist · get · acknowledge · resolve · reopen"]
        R_DET["routes/detection.py\ningest/events · rules · evaluate"]
        DEPS["deps.py\nget_current_user() · require_roles()"]
    end

    subgraph SERVICES ["Services"]
        SVC_AUTH["AuthService\nJWT · bcrypt · refresh rotation"]
        SVC_AUDIT["AuditService\nimmutable event log"]
        SVC_ALERT["AlertService\nupsert by fingerprint · lifecycle"]
        SVC_AEV["AlertEventService\ntimeline · snapshot"]
    end

    subgraph DETECTION ["Detection Engine"]
        SCHED["scheduler.py\nAPScheduler every 5 min\nlast_run tracking"]
        ENGINE["DetectionEngine\nrun(db, start, end)"]
        BASE["DetectionRule ABC\nevaluate(db, start, end)"]
        R001["AUTH_001\nBruteforce\nLOGIN_FAILED by IP ≥ 5"]
        R002["AUTH_002\nSuspicious Refresh\nREFRESH by IP ≥ 8"]
    end

    subgraph MODELS ["Models — PostgreSQL"]
        M_USER["users\nid · email · role · is_active"]
        M_RT["refresh_tokens\ntoken_hash · revoked_at · expires_at"]
        M_AUDIT["audit_logs\nevent_type · actor_id · ip_address · severity"]
        M_ALERT["alerts\nfingerprint · rule_id · severity · status\nattack_tactic · attack_technique"]
        M_AEV["alert_events\nalert_id · event_type · snapshot"]
    end

    EXT -->|"POST /ingest/events"| R_DET
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
    R001 -->|"query"| M_AUDIT
    R002 -->|"query"| M_AUDIT
    ENGINE -->|"findings"| SVC_ALERT

    SCHED -->|"every 5 min"| ENGINE
```

## Detection cycle

```mermaid
sequenceDiagram
    participant S as Scheduler
    participant E as DetectionEngine
    participant R as DetectionRule
    participant AL as AuditLog (DB)
    participant AS as AlertService
    participant A as Alert (DB)

    S->>E: run(db, last_run, now)
    loop for each rule
        E->>R: evaluate(db, start, end)
        R->>AL: SELECT GROUP BY ip HAVING count >= threshold
        AL-->>R: rows
        R-->>E: DetectionFinding[]
    end
    E-->>S: all_findings[]
    alt findings not empty
        S->>AS: upsert_many(findings)
        AS->>A: INSERT or UPDATE by fingerprint
        AS->>A: record AlertEvent (created / updated)
    end
    S->>S: _last_run = now
```

## Alert lifecycle

```mermaid
stateDiagram-v2
    [*] --> open : DetectionEngine match
    open --> in_progress : acknowledge()
    open --> resolved : resolve()
    open --> false_positive : mark_false_positive()
    in_progress --> resolved : resolve()
    in_progress --> false_positive : mark_false_positive()
    resolved --> open : reopen()
    false_positive --> open : reopen()
```

## Module map

```mermaid
graph LR
    subgraph app/core
        CFG[config.py]
        SEC[security.py]
        LOG[logging.py]
    end
    subgraph app/api
        DEPS[deps.py]
        subgraph routes
            RA[auth.py]
            RB[alerts.py]
            RC[detection.py]
        end
    end
    subgraph app/services
        SA[auth_service.py]
        SB[audit_service.py]
        SC[alert_service.py]
        SD[alert_event_service.py]
    end
    subgraph app/detection
        EN[engine.py]
        BS[base.py]
        subgraph rules
            RU1[auth_bruteforce.py]
            RU2[suspicious_refresh.py]
        end
    end
    subgraph app/models
        MU[user.py]
        MR[refresh_token.py]
        MA[audit_log.py]
        ML[alert.py]
        ME[alert_event.py]
    end
    SCH[scheduler.py]

    DEPS --> SEC
    RA --> SA
    RB --> SC
    RC --> EN
    SA --> SB
    SA --> MU
    SA --> MR
    SB --> MA
    SC --> SD
    SC --> ML
    SD --> ME
    EN --> BS
    BS --> RU1
    BS --> RU2
    RU1 --> MA
    RU2 --> MA
    EN --> SC
    SCH --> EN
```
