# CapstonePilot — Iteration 1: System Architecture

**Status:** Approved
**Decisions locked in:** Monorepo · LLM via OpenRouter · FastAPI BackgroundTasks + DB polling for async jobs · JWT auth with roles (`team_leader`, `member`)

---

## 1. Why this architecture

CapstonePilot's core claim is that it behaves like a **Living Project Manager**, not a CRUD app with a chatbot bolted on. That claim has three concrete architectural consequences:

1. **The Plan is versioned data, not a UI state.** Every planning/replanning cycle produces a new `Plan` version with a lifecycle (`draft → proposed → approved → superseded`). If the plan were just rows in a `tasks` table with no versioning, "continuously adapts it" and "human-in-the-loop approval" would have nothing to attach to.
2. **Orchestration must be a first-class backend concern, not a prompt.** "One Orchestrator calling specialized agents, combining outputs, requesting approval, executing actions" is a state machine with branching (health-triggered replanning, approval gates). That belongs in code (CrewAI **Flows**), not in a single mega-prompt.
3. **Decisions are hybrid (rules + LLM) by requirement.** So the Decision Engine has to be a real module the Orchestrator calls — not something implicit inside an LLM call.

Everything below exists to serve those three points, kept as simple as it can be while still satisfying them — no Celery, no microservices, no premature multi-tenancy.

---

## 2. System Context

```mermaid
C4Context
title CapstonePilot — System Context
Person(leader, "Team Leader", "Creates projects, uploads docs, approves plans/replans")
Person(member, "Team Member", "Views project, updates own task status")
System(cp, "CapstonePilot", "AI Project Manager: orchestrates planning, monitoring, risk, replanning")
System_Ext(llm, "OpenRouter", "LLM gateway — model-agnostic completion API")
System_Ext(db, "PostgreSQL", "System of record: projects, plans, tasks, documents, decisions")

Rel(leader, cp, "Creates project, uploads docs, approves")
Rel(member, cp, "Updates task progress")
Rel(cp, llm, "Agent reasoning calls")
Rel(cp, db, "Reads/writes state")
```

---

## 3. Container View (Monorepo)

```
capstonepilot/
├── frontend/     React + Vite SPA
├── backend/      FastAPI + CrewAI service
└── docs/         Architecture, ADRs
```

```mermaid
C4Container
title CapstonePilot — Containers
Person(leader, "Team Leader")
Person(member, "Team Member")

Container(spa, "Frontend SPA", "React + Vite", "Dashboard, project mgmt, plan review/approval UI, bilingual (AR/EN, RTL/LTR)")
Container(api, "Backend API", "FastAPI", "REST API, auth, orchestration trigger, job status")
Container(orch, "Orchestrator + Agents", "CrewAI Flow", "Planner, Progress Monitor, Risk, Recommendation, Doc Analysis, Reporting agents")
Container(rules, "Decision Engine", "Python module", "Deterministic rules: deadlines, workload, risk thresholds")
ContainerDb(pg, "PostgreSQL", "Database", "Projects, Plans (versioned), Tasks, Documents, AgentRuns, Approvals")
Container(files, "File Storage", "Local disk / object storage adapter", "Uploaded project documents")
System_Ext(openrouter, "OpenRouter", "LLM Gateway")

Rel(leader, spa, "Uses")
Rel(member, spa, "Uses")
Rel(spa, api, "HTTPS/JSON, Axios")
Rel(api, orch, "Invokes via BackgroundTasks")
Rel(orch, rules, "Calls for objective signals")
Rel(orch, openrouter, "LLM completions (LiteLLM model string)")
Rel(api, pg, "SQLAlchemy repositories")
Rel(orch, pg, "Reads context, writes AgentRun/Plan/Risk state")
Rel(api, files, "Store/retrieve uploads")
```

---

## 4. Backend: Clean Architecture layers

```
backend/
├── api/              FastAPI routers + Pydantic request/response schemas.
│                      No business logic. Depends on application/.
├── application/       Use cases / services: ProjectService, PlanningService,
│                      OrchestratorService, DecisionEngine, JobRunner.
│                      Depends only on domain/ (interfaces).
├── domain/            Entities (Project, Plan, Task, Milestone, RiskReport,
│                      Recommendation, AgentRun, ApprovalDecision, User) +
│                      repository interfaces (ports). Zero framework imports.
├── infrastructure/    SQLAlchemy models + repository implementations,
│                      CrewAI agent/crew/flow implementations, OpenRouter
│                      LLM client config, file storage adapter, JWT/security.
└── core/              Config (env), DI wiring, app startup.
```

**Why this shape:** the requirement explicitly asks for SOLID + Clean Architecture + repository pattern. The concrete payoff: `application/` never imports `sqlalchemy` or `crewai` directly — it depends on interfaces defined in `domain/`. That means we can unit-test `PlanningService` with fake repositories, and we can swap CrewAI for something else later without touching API routes.

**Orchestrator placement:** `OrchestratorService` lives in `application/`, but the actual CrewAI `Flow` it drives lives in `infrastructure/agents/`. The service depends on an `OrchestratorPort` interface — so the API layer talks to "the orchestrator," never to CrewAI specifics.

---

## 5. Orchestration Design: CrewAI Flow, not a hand-rolled loop

CrewAI ships a primitive for exactly this shape of problem: **Flows** (`@start`, `@listen`, `@router`, typed state). Rather than reinventing an orchestrator loop, the Orchestrator Agent is implemented as one Flow that:

- Holds **Flow state** = the project's live orchestration context (project id, current plan version, latest health signals).
- Coordinates six **single-purpose Crews**, one per specialized agent: Planner, Progress Monitor, Risk Analysis, Recommendation, Documentation Analysis, Reporting.
- Uses `@router` steps for branching: e.g. after Progress Monitor runs, route to Risk Analysis only if the Decision Engine flags a threshold breach.
- Persists state transitions to the `agent_runs` table so every orchestration cycle is auditable.

```mermaid
flowchart TD
    A[Trigger: new project / task update / schedule tick] --> B[Orchestrator Flow starts]
    B --> C[Documentation Analysis Crew\n(only on new/updated docs)]
    C --> D[Planner Crew\ndrafts Plan v_n]
    D --> E{Team Leader review}
    E -->|Edit/Reject| D
    E -->|Approve| F[Plan v_n: approved\nOrchestrator executes\ntasks/milestones]
    F --> G[Progress Monitoring Crew\n(continuous)]
    G --> H[Decision Engine:\nrule-based health check]
    H -->|Healthy| G
    H -->|Risk threshold breached| I[Risk Analysis Crew]
    I --> J[Recommendation Crew]
    J --> K[Orchestrator assembles\nReplan Proposal = Plan v_n+1 draft]
    K --> L{Team Leader approves replan?}
    L -->|No| G
    L -->|Yes| F
```

**Why Flows over a custom orchestrator class:** we get typed state, conditional routing, and resumability for free, and it keeps the "temporary dynamic agents" future requirement cheap — a new Crew is just a new node the Flow can route to, without changing the Flow's control structure.

**Isolation:** the Flow and its Crews live entirely in `infrastructure/agents/`. `OrchestratorService.run(project_id, trigger)` is the only entry point the rest of the backend calls.

---

## 6. Decision Engine — hybrid rules + LLM

A plain Python module (`application/decision_engine/`), called by the Flow at specific points, not an agent itself:

| Signal | Computed by | Example rule |
|---|---|---|
| Schedule variance | Rule | `(days_elapsed / planned_days) - (tasks_done / tasks_total) > 0.15` → flag |
| Workload imbalance | Rule | stddev of open-task-count across members > threshold |
| Overdue ratio | Rule | `overdue_tasks / total_tasks > 0.2` → flag |
| Interpretation of *why* + proposed fix | LLM (Risk / Recommendation crews) | given the rule-flagged facts + project context, explain risk and propose 2–3 concrete adjustments |

The Flow always computes rule-based facts first and injects them as structured context into the LLM crew's task input — the LLM never has to guess numbers it can be given, and objective thresholds stay deterministic and testable without hitting the LLM at all.

---

## 7. Core Domain Model

```mermaid
erDiagram
    USER ||--o{ PROJECT : owns
    USER ||--o{ TASK : "assigned to"
    PROJECT ||--o{ DOCUMENT : has
    PROJECT ||--o{ PLAN : "has versions of"
    PLAN ||--o{ MILESTONE : contains
    MILESTONE ||--o{ TASK : contains
    PROJECT ||--o{ AGENT_RUN : logs
    PROJECT ||--o{ RISK_REPORT : has
    RISK_REPORT ||--o{ RECOMMENDATION : yields
    PLAN ||--o{ APPROVAL_DECISION : "gated by"
    RECOMMENDATION ||--o{ APPROVAL_DECISION : "gated by"

    USER {
        uuid id
        string name
        string email
        string role "team_leader | member"
        string preferred_language "ar | en"
    }
    PROJECT {
        uuid id
        string name
        string description
        string status
        uuid owner_id
    }
    DOCUMENT {
        uuid id
        uuid project_id
        string filename
        string storage_path
        string detected_language
        text extracted_text
    }
    PLAN {
        uuid id
        uuid project_id
        int version
        string status "draft|proposed|approved|superseded"
        json rationale
    }
    MILESTONE {
        uuid id
        uuid plan_id
        string title
        date due_date
    }
    TASK {
        uuid id
        uuid milestone_id
        string title
        string status
        uuid assignee_id
        date due_date
    }
    AGENT_RUN {
        uuid id
        uuid project_id
        string agent_type
        string status
        json input_ref
        json output_ref
    }
    RISK_REPORT {
        uuid id
        uuid project_id
        int plan_version
        string severity
        text description
    }
    RECOMMENDATION {
        uuid id
        uuid risk_report_id
        text description
        json proposed_changes
        string status "pending|approved|rejected"
    }
    APPROVAL_DECISION {
        uuid id
        string entity_type
        uuid entity_id
        uuid decided_by
        string decision
        timestamp decided_at
    }
```

`AGENT_RUN` doubles as the **async job record**: every backend-triggered orchestration cycle creates one row, `status` moves `queued → running → succeeded/failed`, and the frontend polls it.

---

## 8. Async Execution (BackgroundTasks + polling)

- `POST /projects/{id}/plan/generate` → creates an `agent_runs` row (`status=queued`) → `BackgroundTasks.add_task(orchestrator_service.run, ...)` → returns `202 { job_id }` immediately.
- Orchestrator Flow updates the same row as it progresses through steps (`running`, then `succeeded`/`failed`, with `output_ref` pointing at the resulting Plan/Report).
- Frontend polls `GET /jobs/{job_id}` every ~2s and renders a "Project Manager is working..." state — this is also the seam for the Iteration-6 dashboard's live activity feed.
- **Explicit trade-off:** single-process concurrency (no distributed workers, no retries-on-crash). Acceptable at capstone scale. The contract (`JobRunnerPort.enqueue(job)`) is the swap point if this ever needs to become Celery/RQ later — nothing above that interface changes.

---

## 9. Auth & RBAC

- FastAPI `OAuth2PasswordBearer` + JWT (access token; refresh token deferred unless requested).
- Passwords hashed with bcrypt (`passlib`).
- Two roles: `team_leader`, `member`. Enforced via a `require_role(...)` FastAPI dependency, not scattered `if` checks in handlers.
- **Team Leader–only:** approve/reject Plan versions and Replan proposals, upload strategic documents, invite members, edit approved plan structure.
- **Member:** view project/plan/tasks, update status of tasks assigned to them.
- Every approval (`ApprovalDecision`) is stored, not just applied — this is the audit trail the "human in the loop" requirement implies.

---

## 10. Frontend Architecture (feature-based)

```
frontend/src/
├── app/            Router, layout shell, providers (QueryClient, Auth, i18n)
├── features/
│   ├── auth/
│   ├── projects/
│   ├── documents/
│   ├── planning/       plan review/approval UI, timeline, milestones
│   ├── dashboard/      health, activity feed, charts (Recharts)
│   ├── risks/
│   └── reports/
│   each feature: api/ (axios calls + React Query hooks), components/, pages/
└── shared/
    ├── components/     shadcn/ui-based primitives, no inline styles
    ├── hooks/
    ├── lib/            axios instance, query client
    └── i18n/           en.json, ar.json, language context
```

- **Server state:** React Query (cache, polling for job status, invalidation on mutations) — not hand-rolled `useEffect` fetching.
- **i18n:** `react-i18next` + `i18next-browser-languagedetector`; `<html dir="rtl|ltr">` toggled on language change; preference persisted to `localStorage` and to `User.preferred_language` once authenticated. Tailwind uses logical properties (`ps-`, `pe-` / `rtl:` variants) instead of hardcoded `left`/`right`.
- **Language independence:** UI language (interface) and document language (content understanding) are separate fields — `User.preferred_language` drives what language the LLM responds in; `Document.detected_language` is independent metadata used only for extraction/analysis quality, never for translation of the UI.

---

## 11. LLM Integration (OpenRouter)

CrewAI's `LLM` class is LiteLLM-backed, so OpenRouter is addressed as a model string, not a separate SDK:

```python
LLM(model="openrouter/anthropic/claude-...", api_key=settings.OPENROUTER_API_KEY)
```

This lets us pick a **different model per agent role** through one config block — e.g. a cheaper/faster model for Documentation Analysis (extraction-heavy) vs a stronger reasoning model for Planner/Risk — all billed through a single OpenRouter key. Model choice becomes a config change, not a code change.

---

## 12. Key Trade-offs (explicit)

| Decision | Upside | Cost | Mitigation |
|---|---|---|---|
| BackgroundTasks over Celery | Zero extra infra to run/deploy | No retries across process crashes, single-node only | `JobRunnerPort` interface isolates the swap |
| CrewAI Flows over custom orchestrator | Built-in state + branching, less code to maintain | Framework coupling | Confined entirely to `infrastructure/agents/` |
| Repository pattern | Testable, DB-agnostic domain/application layers | More files/indirection than direct ORM calls | Required by the stated SOLID/Clean Architecture goal |
| Plan versioning (not in-place edits) | Replanning, audit trail, "living plan" narrative all fall out of this for free | Slightly more complex queries ("get current approved plan") | One repository method: `get_current(project_id)` |

---

## 13. What Iteration 1 explicitly defers

- Exact Postgres schema/migrations → Iteration 9 (Backend APIs) / Alembic setup.
- CrewAI agent prompts/tools in detail → Iteration 10–11.
- Deployment topology (Docker, hosting) → Iteration 15.
- Dynamic/temporary agent creation mechanism → will hang off the same Flow-routing design in §5, detailed once the fixed agents exist.

---

## Iteration 2: Folder Structure — Approved

The monorepo skeleton (empty directories, no dependencies/code yet) was scaffolded per this architecture:

```
capstonepilot/
├── docs/architecture.md
├── backend/
│   ├── app/
│   │   ├── api/{v1/routers, schemas}
│   │   ├── application/{services, decision_engine, ports}
│   │   ├── domain/entities
│   │   ├── infrastructure/{db/{models,repositories,migrations}, agents/{flows,crews,tools}, jobs, storage, security}
│   │   └── core
│   └── tests/{unit, integration}
└── frontend/
    └── src/
        ├── app/{layout, providers}
        ├── features/{auth,projects,documents,planning,dashboard,risks,reports}/{api,components,pages,hooks}
        └── shared/{components/{ui,common}, hooks, lib, i18n/locales}
```

Project tooling (`package.json`, `pyproject.toml`, Vite/Tailwind config, dependency installs) is deferred to **Iteration 3: Project Setup**.
