# OS-APOW Architecture

**Project:** workflow-orchestration-queue (OS-APOW)
**Generated:** 2026-03-20
**Source:** OS-APOW Architecture Guide v3.2

---

## Executive Summary

OS-APOW represents a paradigm shift from **Interactive AI Coding** to **Headless Agentic Orchestration**. Traditional AI developer tools require a human-in-the-loop to navigate files, provide context, and trigger executions. OS-APOW replaces this manual overhead with a persistent, event-driven infrastructure that transforms GitHub Issues into "Execution Orders" autonomously fulfilled by specialized AI agents.

The system is designed to be **Self-Bootstrapping** — once the initial deployment is seeded, the system uses its own orchestration capabilities to refine its components, allowing the AI to "build its own house" while residing within it.

---

## The 4-Pillar Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         OS-APOW System                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │   THE EAR   │───▶│  THE STATE  │◀───│  THE BRAIN  │             │
│  │  (Notifier) │    │   (Queue)   │    │  (Sentinel) │             │
│  │  FastAPI    │    │ GH Issues   │    │   Python    │             │
│  └─────────────┘    └──────┬──────┘    └──────┬──────┘             │
│                            │                   │                     │
│                            │                   ▼                     │
│                            │         ┌─────────────┐                │
│                            └────────▶│  THE HANDS  │                │
│                                      │   (Worker)  │                │
│                                      │  DevContain │                │
│                                      └─────────────┘                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1. The Ear (Work Event Notifier)

**Technology Stack:** Python 3.12, FastAPI, UV, Pydantic

**Role:** Primary gateway for external stimuli and asynchronous triggers

**Responsibilities:**
- **Secure Webhook Ingestion:** Hardened endpoint for GitHub events (issues, issue_comment, pull_request)
- **Cryptographic Verification:** HMAC SHA256 validation against `WEBHOOK_SECRET`
- **Intelligent Event Triage:** Parse issue bodies and labels into unified `WorkItem` objects
- **Queue Initialization:** Apply `agent:queued` label to signal the Sentinel

**Key Security:** Prevents "Prompt Injection via Webhook" by ensuring only verified GitHub events can trigger agent actions.

---

### 2. The State (Work Queue)

**Philosophy:** "Markdown as a Database"

**Implementation:** Distributed state management via GitHub Issues, Labels, and Milestones

**State Machine (Label Logic):**

| Label | State | Description |
|-------|-------|-------------|
| `agent:queued` | Queued | Task validated, awaiting Sentinel |
| `agent:in-progress` | In Progress | Sentinel has claimed the issue |
| `agent:reconciling` | Reconciling | Stale task recovery state |
| `agent:success` | Success | Terminal success state |
| `agent:error` | Error | Technical failure |
| `agent:infra-failure` | Infra Failure | Infrastructure-level failure |
| `agent:stalled-budget` | Stalled | Budget exceeded (future) |

**Concurrency Control:** GitHub "Assignees" act as a distributed lock using the **assign-then-verify pattern**:
1. Attempt to assign `SENTINEL_BOT_LOGIN` to the issue
2. Re-fetch the issue
3. Verify the bot appears in assignees
4. Only then update labels and post claim comment

---

### 3. The Brain (Sentinel Orchestrator)

**Technology Stack:** Python (Async), PowerShell Core, Docker CLI

**Role:** Persistent supervisor managing worker lifecycles

**Lifecycle Management:**

```
┌─────────────────────────────────────────────────────────────┐
│                    SENTINEL LIFECYCLE                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. POLLING DISCOVERY (every 60s)                           │
│     └── GET /repos/{owner}/{repo}/issues?labels=agent:queued│
│                                                             │
│  2. AUTH SYNCHRONIZATION                                    │
│     └── scripts/gh-auth.ps1 + common-auth.ps1               │
│                                                             │
│  3. SHELL-BRIDGE PROTOCOL                                   │
│     ├── devcontainer-opencode.sh up                         │
│     ├── devcontainer-opencode.sh start                      │
│     └── devcontainer-opencode.sh prompt "{instruction}"     │
│                                                             │
│  4. TELEMETRY                                               │
│     ├── Heartbeat comments (every 5 min)                    │
│     └── Status updates to GitHub                            │
│                                                             │
│  5. ENVIRONMENT RESET                                       │
│     └── devcontainer-opencode.sh stop                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Workflow Mapping:**

| Task Type | Workflow Module |
|-----------|-----------------|
| PLAN | create-app-plan.md |
| IMPLEMENT | perform-task.md |
| BUGFIX | recover-from-error.md |

**Graceful Shutdown:** Handles `SIGTERM` and `SIGINT`, finishes current task, closes connection pool, exits cleanly.

---

### 4. The Hands (Opencode Worker)

**Technology Stack:** opencode CLI, LLM (GLM-5 or Claude 3.5 Sonnet)

**Environment:** High-fidelity DevContainer built from template

**Worker Capabilities:**
- **Contextual Awareness:** Access to project structure and vector-indexed codebase
- **Instructional Logic:** Executes markdown workflow modules from `/local_ai_instruction_modules/`
- **Verification:** Runs local test suites before submitting PRs

---

## Key Architectural Decisions (ADRs)

### ADR 07: Standardized Shell-Bridge Execution

**Decision:** Orchestrator interacts with agentic environment *exclusively* via `./scripts/devcontainer-opencode.sh`

**Rationale:** Reusing shell scripts ensures environment parity between AI agent and human developers. Prevents "Configuration Drift."

**Consequence:** Python code stays lightweight (logic/state), shell scripts handle infra (Docker, volumes, networks).

---

### ADR 08: Polling-First Resiliency Model

**Decision:** Polling is primary discovery mechanism; Webhooks are "optimization"

**Rationale:** Webhooks are "Fire and Forget" — if server is down during event, event is lost. Polling ensures self-healing on restart.

**Implementation:** Jittered exponential backoff on rate limits (403/429), max 16 min backoff.

---

### ADR 09: Provider-Agnostic Interface Layer

**Decision:** Queue interactions abstracted behind `ITaskQueue` interface (Strategy Pattern)

**Rationale:** Enables future provider swapping (Linear, Jira, internal SQL) without rewriting orchestrator logic.

---

## Data Flow (The "Happy Path")

```
1. STIMULUS: User opens GitHub Issue with [Plan] template
                    │
                    ▼
2. NOTIFICATION: GitHub Webhook hits Notifier (FastAPI)
                    │
                    ▼
3. TRIAGE: Notifier verifies signature, applies agent:queued label
                    │
                    ▼
4. CLAIM: Sentinel detects label, assigns issue, updates to agent:in-progress
                    │
                    ▼
5. SYNC: Sentinel clones/pulls target repo to workspace volume
                    │
                    ▼
6. ENVIRONMENT: Sentinel executes devcontainer-opencode.sh up
                    │
                    ▼
7. DISPATCH: Sentinel sends prompt command with workflow instruction
                    │
                    ▼
8. EXECUTION: Worker (Opencode) reads issue, generates code, creates PRs
                    │
                    ▼
9. FINALIZE: Worker posts completion, Sentinel updates to agent:success
```

---

## Security, Authentication & Isolation

### Network Isolation
- Worker containers in dedicated Docker network
- No access to host network or internal subnets

### Credential Scoping
- GitHub App Installation Token passed via temporary env var
- Destroyed immediately when session ends

### Credential Scrubbing
All worker output passes through `scrub_secrets()` which strips:
- GitHub PATs (`ghp_*`, `ghs_*`, `gho_*`, `github_pat_*`)
- Bearer tokens
- API keys (`sk-*`)
- ZhipuAI keys

### Resource Constraints
- Worker containers: 2 CPUs, 4GB RAM hard cap
- Prevents DoS from rogue agents

---

## Self-Bootstrapping Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                    BOOTSTRAPPING PHASES                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. BOOTSTRAP: Developer manually clones template repo      │
│                                                             │
│  2. SEED: Add plan docs, run create-repo-from-plan-docs     │
│                                                             │
│  3. INIT: Run devcontainer-opencode.sh up                   │
│                                                             │
│  4. ORCHESTRATE: Run project-setup workflow                 │
│     └── Agent configures own env vars, indexes codebase     │
│                                                             │
│  5. AUTONOMOUS: Start Sentinel service                      │
│     └── From here, AI manages all further development       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Related Documents

- [Technology Stack](./tech-stack.md)
- [OS-APOW Development Plan v4.2](./OS-APOW%20Development%20Plan%20v4.2.md)
- [OS-APOW Implementation Specification v1.2](./OS-APOW%20Implementation%20Specification%20v1.2.md)
- [OS-APOW Plan Review](./OS-APOW%20Plan%20Review.md)
- [OS-APOW Simplification Report v1](./OS-APOW%20Simplification%20Report%20v1.md)
