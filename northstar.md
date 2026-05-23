# SentinelLab North Star

SentinelLab is a defensive security backend for learning and demonstrating
real-world backend security concepts: authentication, audit logging, rule-based
detection, alert lifecycle management, and future AppSec analysis.

It acts as a small Security Event Processing Engine (SEPE): external systems
send security-relevant events, SentinelLab stores them as audit logs, detection
rules evaluate those logs, and alerts track investigation state over time.

## Current direction

The project is moving from a regular backend into a more professional layered
architecture. The current M5 scope closed the alert operational loop:

- make alert querying and lifecycle transitions consistent
- move raw SQLAlchemy reads out of services into repositories
- wire scheduled detection cleanly into application startup
- keep documentation synchronized with the code after each session

The next decision is whether to continue with M6 AppSec Lab or first harden the
planned external ingest endpoint.

## Documentation map

- [Architecture registry](docs/architecture-registry.md): current system state,
  modules, known gaps, and next concrete step.
- [Session log](docs/session-log.md): atomic record of project changes.

## Product boundary

SentinelLab owns internal security APIs, audit storage, detection, alerts, and
future reporting.

External apps such as Galeria Puerto own their own user-facing authentication
and send events into SentinelLab. SentinelLab should not become tightly coupled
to any one client application.
