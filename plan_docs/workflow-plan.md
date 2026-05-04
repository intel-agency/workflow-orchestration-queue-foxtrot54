# Workflow Execution Plan: project-setup

**Generated:** 2026-05-04
**Dynamic Workflow:** `project-setup`
**Workflow File:** `ai_instruction_modules/ai-workflow-assignments/dynamic-workflows/project-setup.md`
**Repository:** `intel-agency/workflow-orchestration-queue-foxtrot54`
**Branch:** `dynamic-workflow-project-setup`

---

## 1. Overview

| Field | Value |
|-------|-------|
| **Workflow Name** | `project-setup` |
| **Project Name** | OS-APOW (workflow-orchestration-queue) |
| **Project Description** | Headless agentic orchestration platform that transforms GitHub Issues into autonomous AI-executed work orders via a Sentinel Orchestrator, webhook Notifier, and isolated DevContainer workers. |
| **Total Main Assignments** | 6 |
| **Total Event Assignments** | 3 unique (`create-workflow-plan`, `validate-assignment-completion`, `report-progress`) |
| **High-Level Purpose** | Initialize the repository, create an application plan, scaffold the project structure, produce AGENTS.md, debrief, and merge the setup PR — transitioning from a template clone to a ready-to-develop project. |

### Assignment Execution Order

1. **pre-script-begin:** `create-workflow-plan` *(this document)*
2. **init-existing-repository:** `init-existing-repository`
3. **create-app-plan:** `create-app-plan`
4. **create-project-structure:** `create-project-structure`
5. **create-agents-md-file:** `create-agents-md-file`
6. **debrief-and-document:** `debrief-and-document`
7. **pr-approval-and-merge:** `pr-approval-and-merge`
8. **post-script-complete:** Apply `orchestration:plan-approved` label

After each main assignment (steps 2–7), the **post-assignment-complete** event fires:
- `validate-assignment-completion`
- `report-progress`

---

## 2. Project Context Summary

### Key Facts from plan_docs/

| Fact | Detail |
|------|--------|
| **Application Name** | workflow-orchestration-queue (OS-APOW) |
| **Tagline** | Headless Agentic Orchestration Platform |
| **Primary Language** | Python 3.12+ |
| **Key Frameworks** | FastAPI, Pydantic, HTTPX, Uvicorn, uv |
| **Infrastructure** | Docker DevContainers, GitHub Issues (state), Shell Bridge scripts |
| **Repository Type** | Template repo clone (`workflow-orchestration-queue-foxtrot54`) |
| **Branch Strategy** | `main` (stable), `develop` (integration) |
| **Phases** | Phase 0: Seeding → Phase 1: Sentinel MVP → Phase 2: Webhook Automation → Phase 3: Deep Orchestration |
| **Reference Code** | `plan_docs/notifier_service.py`, `plan_docs/orchestrator_sentinel.py`, `plan_docs/src/models/work_item.py`, `plan_docs/src/queue/github_queue.py` |
| **Key Docs** | Architecture Guide v3.2, Development Plan v4.2, Implementation Spec v1.2, Plan Review, Simplification Report v1 |
| **Architecture** | 4-pillar: Ear (Notifier), State (Queue/Labels), Brain (Sentinel), Hands (Worker) |

### Technology Stack

- **Runtime:** Python 3.12+
- **Web Framework:** FastAPI + Uvicorn (ASGI)
- **Data Validation:** Pydantic v2
- **HTTP Client:** HTTPX (async)
- **Package Manager:** uv (Rust-based, replaces pip/poetry)
- **Containerization:** Docker + DevContainers
- **Shell Bridge:** PowerShell Core (pwsh) / Bash via `devcontainer-opencode.sh`
- **State Management:** GitHub Issues + Labels (agent:queued, agent:in-progress, agent:success, agent:error)
- **Security:** HMAC SHA256 webhook verification, credential scrubbing, network isolation

### Existing Repository State

The repository is a template clone that already contains:
- `.github/workflows/` — CI/CD workflows (validate, publish-docker, prebuild-devcontainer, orchestrator-agent)
- `.devcontainer/` — Consumer and build-time devcontainer configs
- `.github/.devcontainer/` — Dockerfile and build devcontainer config
- `scripts/` — Shell bridge, auth helpers, label import, etc.
- `local_ai_instruction_modules/` — Agent instruction modules
- `.opencode/` — Agent definitions and commands
- `AGENTS.md` — Already exists at root (targets template repo context)
- `test/` — Shell-based test suite
- `global.json` — .NET SDK versioning (not needed for Python project — to be addressed during structure creation)
- `plan_docs/` — Application planning documents (seeded externally)

### Key Constraints

1. **Action SHA Pinning:** All GitHub Actions workflows created or modified MUST pin actions to specific commit SHAs.
2. **No .NET:** The project is Python/Shell. `global.json` is unnecessary. The template's .NET tooling is inherited but irrelevant.
3. **Simplification Report Decisions:** Several changes have been IMPLEMENTED or KEPT per user feedback (env vars reduced to 3, env-reset hardcoded to "stop", cross-repo polling deferred, ITaskQueue ABC kept for future provider swapping, doc duplication kept intentionally).
4. **Self-Bootstrapping:** This project is designed to build itself. After project-setup completes, Phase 2 and 3 features are intended to be built by the system's own agentic workflows.

---

## 3. Assignment Execution Plan

### 3.1 `create-workflow-plan` (pre-script-begin)

| Field | Content |
|-------|---------|
| **Short ID** | `create-workflow-plan` |
| **Goal** | Create this workflow execution plan document before any other assignment begins. |
| **Key Acceptance Criteria** | Dynamic workflow fully read; all assignments traced; all plan_docs/ read; plan produced, approved, and committed as `plan_docs/workflow-plan.md`. |
| **Project-Specific Notes** | This is the current assignment. The plan_docs/ directory contains 7 documents plus reference code and an interactive HTML report. The project is a Python/FastAPI agentic orchestration system. |
| **Prerequisites** | Dynamic workflow file accessible; plan_docs/ populated. |
| **Dependencies** | None (first assignment). |
| **Risks/Challenges** | plan_docs/ is extensive (Architecture Guide, Dev Plan, Impl Spec, Plan Review, Simplification Report, reference code). Thorough reading required to produce accurate project-specific notes. |
| **Events** | None. |

### 3.2 `init-existing-repository`

| Field | Content |
|-------|---------|
| **Short ID** | `init-existing-repository` |
| **Goal** | Initialize the existing repository with administrative structure: branch, branch protection, project board, labels, file renames, and a setup PR. |
| **Key Acceptance Criteria** | New branch created (`dynamic-workflow-project-setup`); branch protection ruleset imported from `.github/protected-branches_ruleset.json`; GitHub Project created with Board columns (Not Started, In Progress, In Review, Done); labels imported from `.github/.labels.json`; workspace/devcontainer files renamed; PR opened to `main`. |
| **Project-Specific Notes** | The repo already has labels in `.github/.labels.json` and branch protection config. The workspace file is `workflow-orchestration-queue-foxtrot54.code-workspace` — rename to `workflow-orchestration-queue.code-workspace`. The devcontainer name in `.devcontainer/devcontainer.json` should become `workflow-orchestration-queue-devcontainer`. The existing `AGENTS.md` will be updated later by the `create-agents-md-file` assignment. |
| **Prerequisites** | GitHub auth with scopes: `repo`, `project`, `read:project`, `read:user`, `user:email`, `administration: write`. `gh` CLI installed and authenticated. |
| **Dependencies** | None (first main assignment). |
| **Risks/Challenges** | (1) `GH_ORCHESTRATION_AGENT_TOKEN` must have `administration: write` scope for branch protection import. (2) GitHub Projects v2 API can be finicky — project creation and repo linking may require GraphQL mutations. (3) The branch `dynamic-workflow-project-setup` may already exist if this workflow plan was committed to it. (4) Labels file is inside `.github/` directory, not repo root. |
| **Events** | **post-assignment-complete:** `validate-assignment-completion`, `report-progress` |

### 3.3 `create-app-plan`

| Field | Content |
|-------|---------|
| **Short ID** | `create-app-plan` |
| **Goal** | Analyze the application template and supporting documents to create a comprehensive application plan documented as a GitHub Issue using the `application-plan.md` issue template. |
| **Key Acceptance Criteria** | Application template analyzed; plan documented using Appendix A template (from `.github/ISSUE_TEMPLATE/application-plan.md`); plan covers all phases, components, dependencies, risks, and mitigations; milestones created and linked; issue added to GitHub Project; issue assigned to milestone; labels applied (`planning`, `documentation`). **No code written** — planning only. |
| **Project-Specific Notes** | The `plan_docs/` directory already contains a fully detailed Architecture Guide v3.2, Development Plan v4.2, and Implementation Spec v1.2. These contain the comprehensive breakdown already. The task is to synthesize them into the `application-plan.md` issue template format. Key phases: Phase 0 (Seeding — done), Phase 1 (Sentinel MVP — core), Phase 2 (Ear — webhook automation), Phase 3 (Deep Orchestration). Milestones should mirror these phases. The Plan Review and Simplification Report provide additional quality context (resolved issues I-1 through I-10, implemented simplifications S-3 through S-11). |
| **Prerequisites** | `init-existing-repository` completed (labels, project, milestones available). |
| **Dependencies** | Outputs from `init-existing-repository`: GitHub Project ID, label set, branch name. |
| **Risks/Challenges** | (1) The three plan docs contain overlapping/duplicate information (noted in Simplification Report S-2 as intentional). The agent must synthesize without losing critical details. (2) The `application-plan.md` issue template must be located at `.github/ISSUE_TEMPLATE/application-plan.md`. (3) Must NOT apply `orchestration:plan-approved` label — that is handled by the post-script-complete event. |
| **Events** | **pre-assignment-begin:** `gather-context` (fetches additional context). **on-assignment-failure:** `recover-from-error`. **post-assignment-complete:** `validate-assignment-completion`, `report-progress` |

### 3.4 `create-project-structure`

| Field | Content |
|-------|---------|
| **Short ID** | `create-project-structure` |
| **Goal** | Create the actual project scaffolding: solution structure, configuration files, Docker/Compose, CI/CD, documentation structure, and development environment. |
| **Key Acceptance Criteria** | Solution/project structure created following tech stack (Python/uv); all project files and directories established; Dockerfile + docker-compose.yml created; basic CI/CD pipeline established; documentation structure created (README, docs/); dev environment validated; initial commit made; stakeholder approval obtained; repository summary created (`.ai-repository-summary.md`); all GitHub Actions pinned to commit SHAs. |
| **Project-Specific Notes** | This is a Python project using `uv`. Target structure from Impl Spec: `pyproject.toml`, `uv.lock`, `src/notifier_service.py`, `src/orchestrator_sentinel.py`, `src/models/work_item.py`, `src/queue/github_queue.py`, `scripts/` (shell bridge, auth), `tests/`. Reference code in `plan_docs/` provides the implementation to scaffold around. Key implementation details: (1) `COPY src/ ./src/` must appear before `uv pip install -e .` in Dockerfile. (2) Healthcheck must NOT use `curl` — use Python stdlib instead. (3) `global.json` (.NET) is irrelevant — either remove or note as template artifact. (4) The existing `scripts/` directory contains the shell bridge and auth scripts — these should be preserved. |
| **Prerequisites** | `create-app-plan` completed (plan issue provides structure guidance). |
| **Dependencies** | Application plan issue (from `create-app-plan`). Tech stack decisions documented in `plan_docs/tech-stack.md` and `plan_docs/architecture.md` (if created by create-app-plan). |
| **Risks/Challenges** | (1) The repo already has a `scripts/` directory, `.github/workflows/`, and `test/` — the agent must integrate with existing structure, not overwrite. (2) The Dockerfile at `.github/.devcontainer/Dockerfile` is for the devcontainer, not the application. A separate `Dockerfile` for the Python application is needed. (3) CI/CD workflow must pin all actions to SHAs. (4) The repo currently has `.NET` tooling in the devcontainer that's not needed for this Python project. |
| **Events** | **post-assignment-complete:** `validate-assignment-completion`, `report-progress` |

### 3.5 `create-agents-md-file`

| Field | Content |
|-------|---------|
| **Short ID** | `create-agents-md-file` |
| **Goal** | Create/update the `AGENTS.md` file at the repository root with project-specific context for AI coding agents. |
| **Key Acceptance Criteria** | `AGENTS.md` exists at root; contains project overview, setup/build/test commands (verified), code style conventions, project structure, testing instructions, PR/commit guidelines; written in standard Markdown; commands validated; committed and pushed; stakeholder approval obtained. |
| **Project-Specific Notes** | An `AGENTS.md` already exists targeting the template repo context. It needs to be rewritten for the OS-APOW project specifically. Key content: Python 3.12+ with uv, FastAPI app (`notifier_service.py`), Sentinel daemon (`orchestrator_sentinel.py`), shared models (`src/models/work_item.py`), consolidated queue (`src/queue/github_queue.py`). Build: `uv sync`. Test: `uv run pytest`. Lint: `uv run ruff check .`. The existing AGENTS.md already has substantial structure — update it to reflect the Python project rather than the template repo context. |
| **Prerequisites** | `create-project-structure` completed (build/test commands must work before being documented). |
| **Dependencies** | Project structure (from `create-project-structure`); application plan (from `create-app-plan`). |
| **Risks/Challenges** | (1) All documented commands MUST be validated by running them — if the project structure hasn't been fully set up, commands may fail. (2) Must cross-reference with `.ai-repository-summary.md` and `README.md` to avoid duplication. (3) The existing AGENTS.md is quite detailed — careful rewrite needed to preserve format while changing content. |
| **Events** | **post-assignment-complete:** `validate-assignment-completion`, `report-progress` |

### 3.6 `debrief-and-document`

| Field | Content |
|-------|---------|
| **Short ID** | `debrief-and-document` |
| **Goal** | Capture key learnings, insights, deviations, and areas for improvement in a structured debrief report. |
| **Key Acceptance Criteria** | Detailed report created following the 12-section template; all deviations documented; report reviewed and approved; committed and pushed; execution trace saved at `debrief-and-document/trace.md`. |
| **Project-Specific Notes** | The debrief should capture: (1) How the template-to-project transition went. (2) Any issues with the Python scaffolding in a repo originally designed for .NET. (3) Whether the existing plan_docs/ were sufficient for autonomous implementation. (4) Any AGENTS.md revision challenges. (5) Plan adjustment mandate: flag any findings that affect Phase 1 implementation (the Sentinel MVP). |
| **Prerequisites** | All prior main assignments completed. |
| **Dependencies** | Full execution history of assignments 1–5. |
| **Risks/Challenges** | (1) The 12-section template is extensive — the agent must fill all sections meaningfully. (2) Deviations must be explicitly listed — the assignment is strict about this. |
| **Events** | **post-assignment-complete:** `validate-assignment-completion`, `report-progress` |

### 3.7 `pr-approval-and-merge`

| Field | Content |
|-------|---------|
| **Short ID** | `pr-approval-and-merge` |
| **Goal** | Complete the full PR approval and merge process for the setup PR, including CI remediation, code review, comment resolution, merge, and cleanup. |
| **Key Acceptance Criteria** | CI verification passed (with remediation loop up to 3 attempts); code review delegated to `code-reviewer` subagent (NOT self-review); review comments resolved per `ai-pr-comment-protocol.md`; stakeholder approval obtained; merge performed; source branch deleted; related issues closed. |
| **Project-Specific Notes** | **Special handling:** Per the dynamic workflow, `$pr_num` is extracted from `#initiate-new-repository.init-existing-repository` output. This is an automated setup PR — self-approval by the orchestrator is acceptable (no human stakeholder approval required). The CI remediation loop (Phase 0.5) MUST still be executed. On successful merge: delete `dynamic-workflow-project-setup` branch and close any related setup issues. |
| **Prerequisites** | `debrief-and-document` completed. All prior assignment outputs committed. |
| **Dependencies** | PR number from `init-existing-repository`. All assignment work on the PR branch. |
| **Risks/Challenges** | (1) CI workflows (`validate`, `publish-docker`, `prebuild-devcontainer`) will run on the PR — these may fail if the new Python project structure conflicts with existing .NET-based CI expectations. (2) The PR comment protocol requires GraphQL mutations — ensure `gh` CLI supports this. (3) Branch protection rules may require specific checks to pass before merge. |
| **Events** | **post-assignment-complete:** `validate-assignment-completion`, `report-progress` |

### 3.8 post-script-complete: Apply `orchestration:plan-approved` Label

| Field | Content |
|-------|---------|
| **Short ID** | (event) |
| **Goal** | Apply the `orchestration:plan-approved` label to the application plan issue to signal readiness for epic creation. |
| **Key Acceptance Criteria** | Locate the application plan issue (from `#initiate-new-repository.create-app-plan`); apply `orchestration:plan-approved` label; record output. |
| **Project-Specific Notes** | This label triggers the next orchestration pipeline phase. The plan issue was created during `create-app-plan`. |
| **Prerequisites** | All main assignments and post-assignment events completed successfully. |
| **Dependencies** | Plan issue number from `create-app-plan`. |
| **Risks/Challenges** | If the label `orchestration:plan-approved` doesn't exist in the repository's label set, it must be created first. |
| **Events** | None (terminal event). |

---

## 4. Sequencing Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PRE-SCRIPT-BEGIN EVENT                               │
│  ┌─────────────────────┐                                                │
│  │ create-workflow-plan │ ──► plan approved, committed                   │
│  └─────────────────────┘                                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                 INITIATE-NEW-REPOSITORY (Sequential)                     │
│                                                                         │
│  ┌──────────────────────────┐                                           │
│  │ 1. init-existing-repo    │──► branch, project, labels, PR             │
│  └──────────┬───────────────┘                                           │
│             │ post-assignment-complete:                                  │
│             │   ├─ validate-assignment-completion                        │
│             │   └─ report-progress                                       │
│             ▼                                                            │
│  ┌──────────────────────────┐                                           │
│  │ 2. create-app-plan       │──► plan issue, milestones                  │
│  └──────────┬───────────────┘                                           │
│             │ pre-assignment-begin: gather-context                       │
│             │ post-assignment-complete:                                  │
│             │   ├─ validate-assignment-completion                        │
│             │   └─ report-progress                                       │
│             ▼                                                            │
│  ┌──────────────────────────┐                                           │
│  │ 3. create-project-struct │──► pyproject.toml, src/, Dockerfile, CI    │
│  └──────────┬───────────────┘                                           │
│             │ post-assignment-complete:                                  │
│             │   ├─ validate-assignment-completion                        │
│             │   └─ report-progress                                       │
│             ▼                                                            │
│  ┌──────────────────────────┐                                           │
│  │ 4. create-agents-md-file │──► AGENTS.md (project-specific)            │
│  └──────────┬───────────────┘                                           │
│             │ post-assignment-complete:                                  │
│             │   ├─ validate-assignment-completion                        │
│             │   └─ report-progress                                       │
│             ▼                                                            │
│  ┌──────────────────────────┐                                           │
│  │ 5. debrief-and-document  │──► debrief report, execution trace         │
│  └──────────┬───────────────┘                                           │
│             │ post-assignment-complete:                                  │
│             │   ├─ validate-assignment-completion                        │
│             │   └─ report-progress                                       │
│             ▼                                                            │
│  ┌──────────────────────────┐                                           │
│  │ 6. pr-approval-and-merge │──► CI green, review, merge, branch delete  │
│  └──────────┬───────────────┘                                           │
│             │ post-assignment-complete:                                  │
│             │   ├─ validate-assignment-completion                        │
│             │   └─ report-progress                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    POST-SCRIPT-COMPLETE EVENT                            │
│                                                                         │
│  Apply `orchestration:plan-approved` label to the plan issue             │
│  (created during create-app-plan) → triggers next orchestration phase    │
└─────────────────────────────────────────────────────────────────────────┘
```

**Total steps:**
- 1 pre-script event
- 6 main assignments
- 12 post-assignment events (2 per main assignment × 6)
- 1 post-script event
- **Grand total: 20 discrete steps**

---

## 5. Open Questions

1. **Branch Name Collision:** The branch `dynamic-workflow-project-setup` may already exist if this workflow plan was committed to it. Should `init-existing-repository` handle this gracefully (reuse vs. recreate)?

2. **Existing CI Workflows vs. Python Project:** The existing `.github/workflows/` are designed for a .NET/DevContainer template repo (validate, publish-docker, prebuild-devcontainer, orchestrator-agent). The Python project will need different CI (lint, test, build). Should the existing workflows be modified in-place, or should new Python-specific workflows be added alongside?

3. **`global.json` Disposition:** The repo contains `global.json` for .NET SDK versioning. Since this is a Python project, should this file be removed, or kept as a template artifact?

4. **Reference Code in plan_docs/:** The `plan_docs/` directory contains working reference implementations (`notifier_service.py`, `orchestrator_sentinel.py`, `src/models/work_item.py`, `src/queue/github_queue.py`). Should `create-project-structure` copy these into the actual `src/` directory, or scaffold empty stubs? The reference code has been reviewed and refined per the Plan Review findings.

5. **Label `orchestration:plan-approved`:** This label must exist in the repository for the post-script-complete event. It may not be in the default `.github/.labels.json`. Should it be created during `init-existing-repository` or at the point of application?

6. **GitHub Project Creation:** The `init-existing-repository` assignment requires creating a GitHub Project (Board template) and linking it to the repository. This requires specific OAuth scopes (`project`, `read:project`) and may require GraphQL API calls. Is the authenticated token guaranteed to have these scopes?

7. **`GH_ORCHESTRATION_AGENT_TOKEN` for Branch Protection:** Importing the branch protection ruleset requires `administration: write` scope. The standard `GITHUB_TOKEN` from Actions may not have this. Should a PAT with elevated permissions be used?

8. **Application Plan Issue Template:** The `create-app-plan` assignment references a template at `.github/ISSUE_TEMPLATE/application-plan.md`. Does this file exist in the repository, or does it need to be created?
