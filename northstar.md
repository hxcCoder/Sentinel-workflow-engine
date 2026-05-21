# 🌐 NORTH STAR — SentinelLab

## 🎯 Propósito

SentinelLab es un sistema de **seguridad, auditoría y detección de eventos** diseñado para centralizar logs, detectar comportamientos anómalos y generar alertas a partir de múltiples aplicaciones externas.

Actúa como un **Security Event Processing Engine (SEPE)** independiente.

---

# 🧱 Estado actual del sistema

## ✔ M1 — Fundamentos
- Configuración centralizada
- Logging estructurado (JSON)
- PostgreSQL operativo
- Health checks básicos

---

## ✔ M2 — Autenticación y seguridad
- JWT Access Tokens
- Refresh Token rotation
- bcrypt password hashing
- RBAC (roles: admin, analyst, viewer)

---

## ✔ M3 — Auditoría (Audit Layer)
- AuditLog model implementado
- AuditService integrado en auth flows
- Registro de acciones críticas del sistema

---

## ✔ M4 — Motor de detección (Detection Engine)
- Rule-based detection system
- AlertService con upsert logic
- Persistencia en tabla alerts
- Evaluación de eventos en tiempo real

---

## ✔ M5 — Ciclo de vida de alertas
- AlertEvent timeline tracking
- Estados de alertas:
  - open
  - acknowledged
  - resolved
  - reopened
- Historial completo de cambios por alerta

---

# ⏳ Roadmap (siguiente evolución)

## ⏳ M5 — Cierre de ciclo operacional
- Endpoints completos de lifecycle
- Scheduler automático de evaluación de reglas
- Re-evaluación periódica de eventos

---

## ⏳ M6 — AppSec Lab
- Simulación OWASP Top 10
- generación de eventos de seguridad controlados
- testing de detección

---

## ⏳ M7 — File Analyzer
- análisis de archivos subidos
- detección de patrones maliciosos
- integración con audit logs

---

## ⏳ M8 — MITRE ATT&CK Mapping
- enriquecimiento de alertas
- mapeo de técnicas TTP
- contexto de amenazas

---

## ⏳ M9 — Reporting + AI Copilot
- generación de reportes PDF
- dashboards avanzados
- asistente IA para análisis de seguridad

---

# 🔗 Integración externa — Galería Puerto

Galería Puerto es una aplicación independiente con su propio sistema de autenticación (Google OAuth).

SentinelLab no maneja login de usuarios finales de Galería Puerto.

---

## 🔄 Flujo de integración

```text
Galería Puerto
    ↓
POST /api/v1/ingest/events
    ↓
AuditService
    ↓
DetectionEngine (scheduler + real-time rules)
    ↓
AlertService.upsert_many()
    ↓
alerts + alert_events tables
    ↓
Dashboard de seguridad

📡 Contrato de eventos (base)

Eventos enviados desde aplicaciones externas deben contener:

event_type
timestamp
actor_id (opcional)
metadata (JSON)
source_app (ej: galeria-puerto)
🧠 Arquitectura conceptual
SentinelLab = Security backend independiente
No depende de UI externa
Recibe eventos de múltiples sistemas
Procesa, detecta y genera alertas
Mantiene auditoría completa e inmutable
🔐 Separación de autenticación
Galería Puerto
Google OAuth
Usuarios finales
No interactúa con auth de SentinelLab
SentinelLab
JWT + refresh tokens
Usuarios técnicos internos
Control de acceso a APIs y dashboards
🧩 Filosofía del sistema
Event-driven security architecture
Centralización de observabilidad
Separación estricta entre apps cliente y motor de seguridad
Extensible a múltiples sistemas externos
🚀 Estado global

✔ Backend estable
✔ Migraciones consistentes
✔ Auditoría funcional
✔ Detección operativa
✔ Base lista para integración externa

🧭 Dirección futura

El sistema evoluciona hacia:

“Security Intelligence Platform con análisis automatizado de comportamiento”


---
