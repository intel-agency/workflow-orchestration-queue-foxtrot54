# Workflow Execution Plan: project-setup

**Repository:** `intel-agency/workflow-orchestration-queue-foxtrot54`
**Workflow:** project-setup (dynamic workflow)
**Date:** 2026-04-20
**Status:** ✅ Approved (self-approved by orchestrator)
**Approved By:** Orchestrator Agent (automated self-approval)

---

## 1. Overview

### Project

**workflow-orchestration-queue** (OS-APOW — Opencode-Server Agent Workflow Orchestration) is a headless agentic orchestration platform that transforms GitHub Issues into autonomous Execution Orders fulfilled by AI agents inside reproducible DevContainers. The system follows a 4-pillar architecture: The Ear (FastAPI webhook receiver), The State (GitHub Issues as database), The Brain (Sentinel polling orchestrator), and The Hands (opencode worker in DevContainer).

### Tech Stack

- **Language:** Python 3.12+
- **Web Framework:** FastAPI + Uvicorn
- **Data Validation:** Pydantic
- **HTTP Client:** HTTPX (async)
- **Package Manager:** uv (Rust-based)
- **Containerization:** Docker / DevContainers / Docker Compose
- **Shell Scripts:** Bash + PowerShell Core (pwsh)
- **Agent Runtime:** opencode CLI
- **State Management:** GitHub Issues + Labels (Markdown-as-a-Database)

### Workflow Summary

The `project-setup` dynamic workflow executes **6 main assignments** sequentially, with validation and progress reporting after each. It concludes by applying the `orchestration:plan-approved` label to the application plan issue, triggering the next orchestration phase.

| # | Assignment | Goal |
|---|-----------|------|
| 1 | `init-existing-repository` | Initialize repo settings (branch protection, GH Project, labels, file renames, PR) |
| 2 | `create-app-plan` | Analyze plan_docs and create a comprehensive application plan as a GitHub Issue |
| 3 | `create-project-structure` | Scaffold the actual project structure (pyproject.toml, src/, Dockerfile, CI, docs) |
| 4 | `create-agents-md-file` | Create AGENTS.md with validated build/test/lint commands |
| 5 | `debrief-and-document` | Produce a comprehensive debrief report capturing all learnings |
| 6 | `pr-approval-and-merge` | Execute full PR review, CI verification, and merge |

**Total assignments:** 6 main + 2 event assignments per step (validate + report) = ~18 total execution units.

---

## 2. Project Context Summary

Key facts from `plan_docs/` that directly affect execution:

### Source Documents

| Document | Key Takeaway |
|----------|-------------|
| Development Plan v4.2 | 4-phase roadmap; Phase 0 (Seeding) is current; Phase 1 (Sentinel MVP) is next; defines user stories with acceptance criteria |
| Architecture Guide v3.2 | 4-pillar architecture (Ear/State/Brain/Hands); Shell-Bridge decision (ADR 07); Polling-First resiliency (ADR 08); Provider-Agnostic interface (ADR 09) |
| Implementation Spec v1.2 | Detailed requirements, test cases (TC-01 through TC-04), project structure, tech stack, deliverables; Phase 3 features moved to Future Work appendix |
| Plan Review | 10 issues (I-1 to I-10) and 9 recommendations (R-1 to R-9) identified by code review; race conditions, missing heartbeat, connection pooling, credential scrubbing |
| Simplification Report | 11 simplifications (S-1 to S-11); items S-3 through S-11 IMPLEMENTED; S-1 (ITaskQueue ABC) KEPT for future provider swapping; S-2 (doc duplication) KEPT for agent reinforcement |

### Reference Implementations (in plan_docs/)

- `orchestrator_sentinel.py` — 292-line Sentinel background service with polling, heartbeat, shell bridge, graceful shutdown
- `notifier_service.py` — 110-line FastAPI webhook receiver with HMAC validation, signature verification, triage logic
- `src/models/work_item.py` — Unified `WorkItem`, `TaskType`, `WorkItemStatus` Pydantic models + `scrub_secrets()` credential scrubber
- `src/queue/github_queue.py` — 249-line `ITaskQueue` ABC + `GitHubQueue` with connection pooling, assign-then-verify locking, heartbeat posting
- `interactive-report.html` — React-based presentation dashboard

### Applied Simplifications

These decisions from the Simplification Report constrain the project structure:

- **S-3:** Only 3 required env vars: `GITHUB_TOKEN`, `GITHUB_ORG`, `GITHUB_REPO`. All others hardcoded with sensible defaults.
- **S-4:** Environment reset mode hardcoded to `"stop"`. No branching logic.
- **S-5:** Single-repo polling only. Cross-repo Search API deferred to future phase.
- **S-6:** Queue consolidated into `src/queue/github_queue.py`. Both sentinel and notifier import from there.
- **S-7:** IPv4 pattern removed from `scrub_secrets()`. Only token/key patterns remain.
- **S-8:** "Encrypted" log prose removed. Plain local log files.
- **S-9:** Phase 3 features moved to Future Work appendix.
- **S-10:** Sentinel logs to stdout only (no FileHandler). Docker captures.
- **S-11:** `raw_payload` field removed from `WorkItem`.

### Key Directives

- All GitHub Actions in any created/modified workflows **MUST** be pinned to commit SHA (not version tags).
- No `global.json` — this is a Python/Shell ecosystem.
- Dependencies managed via `pyproject.toml` + `uv.lock`.
- The `plan_docs/` directory is excluded from strict linting (external-generated documents).

---

## 3. Assignment Execution Plan

### Assignment 1: `init-existing-repository`

**Goal:** Initialize the repository with branch protection, GitHub Project, labels, and file renames; create the setup PR.

**Key Acceptance Criteria:**
- New branch `dynamic-workflow-project-setup` created (all work commits here)
- Branch protection ruleset imported from `.github/protected-branches_ruleset.json`
- GitHub Project created for issue tracking with columns: Not Started, In Progress, In Review, Done
- Labels imported from `.github/.labels.json` via `scripts/import-labels.ps1`
- `.devcontainer/devcontainer.json` `name` property renamed to `<repo-name>-devcontainer`
- `ai-new-app-template.code-workspace` renamed to `<repo-name>.code-workspace`
- PR created from `dynamic-workflow-project-setup` to `main`

**Project-Specific Notes:**
- Repository name: `workflow-orchestration-queue-foxtrot54`
- Branch protection import requires `GH_ORCHESTRATION_AGENT_TOKEN` (PAT with `administration: write` scope), not `GITHUB_TOKEN`
- The PR created here will be used by assignment 6 (`pr-approval-and-merge`)
- PR number must be captured as output for downstream use

**Prerequisites:**
- GitHub authentication with scopes: `repo`, `project`, `read:project`, `read:user`, `user:email`
- `administration: write` scope for branch protection ruleset import
- `scripts/import-labels.ps1` and `scripts/test-github-permissions.ps1` available

**Dependencies:** None (first assignment)

**Risks/Challenges:**
- Branch protection import may fail if `GH_ORCHESTRATION_AGENT_TOKEN` lacks `administration: write` scope — must stop and report
- PR creation requires at least one commit pushed to the branch first
- GitHub Project creation may require `project` scope that isn't available with default `GITHUB_TOKEN`

**Events:**
- `post-assignment-complete` → `validate-assignment-completion` + `report-progress`

---

### Assignment 2: `create-app-plan`

**Goal:** Analyze plan_docs and create a comprehensive application plan documented as a GitHub Issue, with milestones and project linking.

**Key Acceptance Criteria:**
- Application template thoroughly analyzed and understood
- `plan_docs/tech-stack.md` created documenting languages, frameworks, tools, packages
- `plan_docs/architecture.md` created documenting high-level architecture and design decisions
- Application plan issue created using `.github/ISSUE_TEMPLATE/application-plan.md` template
- Milestones created based on plan phases and linked to the issue
- Issue added to GitHub Project for tracking
- Issue assigned to appropriate milestone (typically "Phase 1: Foundation")
- Labels applied (typically `planning`, `documentation`)
- **NO implementation code written** — planning only

**Project-Specific Notes:**
- The plan_docs/ directory already contains rich, detailed specifications — the agent must synthesize these, not start from scratch
- Key phases to plan: Phase 1 (Sentinel MVP), Phase 2 (Ear/Webhook), Phase 3 (Deep Orchestration)
- Phase 0 (Seeding) is effectively complete (this workflow is part of it)
- Reference implementations in plan_docs/ should be analyzed as the starting codebase
- The plan issue will receive `orchestration:plan-approved` label in the `post-script-complete` event
- Do NOT apply any orchestration trigger labels from this assignment

**Prerequisites:**
- Assignment 1 completed (repo initialized, labels available, project created)

**Dependencies:** `init-existing-repository` (labels, project, milestones infrastructure)

**Risks/Challenges:**
- The plan_docs are extensive — risk of the agent producing a plan that's too detailed or duplicates existing docs rather than creating an actionable plan
- Must distinguish between what's already defined (architecture, specs) and what needs planning (implementation phases, milestones)
- The application-plan issue template may not exist yet at `.github/ISSUE_TEMPLATE/application-plan.md` — if missing, the agent should create the plan using the inline template from the assignment's Appendix A

**Events:**
- `post-assignment-complete` → `validate-assignment-completion` + `report-progress`

---

### Assignment 3: `create-project-structure`

**Goal:** Create the actual project scaffolding — solution structure, project files, Dockerfile, docker-compose, CI/CD, documentation, and repository summary.

**Key Acceptance Criteria:**
- `pyproject.toml` created with all dependencies (fastapi, uvicorn, pydantic, httpx, etc.)
- `uv.lock` generated
- `src/` directory structure created following the Implementation Spec layout
- Reference implementations from `plan_docs/` promoted to actual `src/` code
- Dockerfile(s) created for each service
- `docker-compose.yml` created for local development
- Test project structure initialized
- CI/CD workflow(s) created with all actions pinned to commit SHA
- Documentation structure (README.md, docs/) created
- `.ai-repository-summary.md` created per `create-repository-summary.md` instructions
- Solution builds successfully
- All actions in CI workflows pinned to specific commit SHA

**Project-Specific Notes:**
- Target structure (from Implementation Spec):
  ```
  workflow-orchestration-queue/
  ├── pyproject.toml
  ├── uv.lock
  ├── src/
  │   ├── orchestrator_sentinel.py
  │   ├── notifier_service.py
  │   ├── models/
  │   │   ├── __init__.py
  │   │   └── work_item.py
  │   └── queue/
  │       ├── __init__.py
  │       └── github_queue.py
  ├── tests/
  ├── scripts/          (already exists)
  ├── Dockerfile
  ├── docker-compose.yml
  ├── README.md
  ├── docs/
  └── .ai-repository-summary.md
  ```
- The reference implementations in `plan_docs/` should be the starting point for `src/` code
- Docker healthchecks must use Python stdlib (`python -c "import urllib.request; ..."`), NOT `curl`
- When using `uv pip install -e .`, ensure `COPY src/ ./src/` appears BEFORE the install command in the Dockerfile
- No `global.json` — this is a Python project

**Prerequisites:**
- Application plan exists (assignment 2)
- Plan documents fully analyzed

**Dependencies:** `create-app-plan` (needs the plan to guide structure)

**Risks/Challenges:**
- The reference code in plan_docs/ has known issues (I-1 through I-10 from Plan Review) — the agent should incorporate fixes when promoting code
- `pyproject.toml` dependency versions must be compatible — risk of version conflicts
- Docker build must succeed — base image must include Python 3.12+, uv
- CI workflow creation requires knowing the latest release commit SHA for each action
- The existing `scripts/` directory should be preserved, not overwritten

**Events:**
- `post-assignment-complete` → `validate-assignment-completion` + `report-progress`

---

### Assignment 4: `create-agents-md-file`

**Goal:** Create a comprehensive `AGENTS.md` at the repository root providing AI coding agents with context, commands, and conventions.

**Key Acceptance Criteria:**
- `AGENTS.md` exists at repository root
- Contains project overview (purpose + tech stack)
- Contains validated setup/build/test commands
- Contains code style and conventions
- Contains project structure / directory layout
- Contains testing instructions
- Contains PR/commit guidelines
- All listed commands have been verified by running them
- File committed and pushed to working branch

**Project-Specific Notes:**
- Commands to validate: `uv sync`, `uv run pytest`, `uv run ruff check .`, `uv run mypy src/`, `docker compose build`
- Must complement (not duplicate) README.md and `.ai-repository-summary.md`
- Should reference plan_docs/ architecture decisions
- Should note the known issues from Plan Review as "Common Pitfalls"

**Prerequisites:**
- Assignments 1-3 completed (project structure exists, builds successfully)

**Dependencies:** `create-project-structure` (needs actual project structure and working commands)

**Risks/Challenges:**
- Commands may not all work on first try — the agent must fix issues and validate
- AGENTS.md must be kept concise — agents perform best with focused, actionable content

**Events:**
- `post-assignment-complete` → `validate-assignment-completion` + `report-progress`

---

### Assignment 5: `debrief-and-document`

**Goal:** Produce a comprehensive debrief report capturing all learnings, deviations, errors, and recommendations from the entire project-setup workflow.

**Key Acceptance Criteria:**
- Debrief report created with all 12 required sections
- Execution trace saved as `debrief-and-document/trace.md`
- All deviations from assignments documented
- Plan-impacting findings flagged as ACTION ITEMS
- Report reviewed and approved
- Committed and pushed to repo

**Project-Specific Notes:**
- Must document all deviations from the 6 assignments
- Must capture which Plan Review issues (I-1 to I-10) were addressed during project setup
- Must capture which Simplification Report items were already applied vs. need future work
- Should flag the deferred features (cost guardrails, cross-repo polling, reconciliation loop) as ACTION ITEMS

**Prerequisites:**
- All prior assignments completed

**Dependencies:** `create-agents-md-file` (all implementation work done)

**Risks/Challenges:**
- The agent may not have complete context on all prior steps — the execution trace is critical
- Must be thorough — future improvement depends on honest assessment

**Events:**
- `post-assignment-complete` → `validate-assignment-completion` + `report-progress`

---

### Assignment 6: `pr-approval-and-merge`

**Goal:** Complete the full PR approval and merge process for the setup PR created in assignment 1.

**Key Acceptance Criteria:**
- CI verification: all status checks pass (up to 3 remediation attempts)
- Code review delegated to `code-reviewer` subagent (NOT self-review)
- All review comments resolved following `ai-pr-comment-protocol.md`
- GraphQL verification: `pr-unresolved-threads.json` is empty
- Stakeholder/Delegating Agent approval obtained
- PR merged successfully
- Source branch deleted
- Related issues closed

**Project-Specific Notes:**
- PR number comes from assignment 1 output (`#initiate-new-repository.init-existing-repository`)
- This is an automated setup PR — self-approval by orchestrator is acceptable per the workflow spec
- CI remediation loop (Phase 0.5) MUST still execute — if CI fails, attempt up to 3 fix cycles
- Must follow `ai-pr-comment-protocol.md` for comment resolution
- Must follow `pr-review-comments.md` for thread resolution

**Prerequisites:**
- All prior assignments completed and committed to the PR branch
- PR exists and has commits ahead of main

**Dependencies:** `debrief-and-document` (all work committed to PR branch)

**Risks/Challenges:**
- CI may fail due to missing dependencies, Docker build issues, or lint violations
- Branch protection may require specific review approvals that need configuration
- Merge conflicts if main has changed since branch creation (unlikely in fresh repo)

**Events:**
- `post-assignment-complete` → `validate-assignment-completion` + `report-progress`

---

## 4. Sequencing Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│ pre-script-begin                                                     │
│ ┌─────────────────────────┐                                          │
│ │ create-workflow-plan     │ ← THIS ASSIGNMENT                      │
│ └────────────┬────────────┘                                          │
└──────────────┼──────────────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────────────┐
│ initiate-new-repository (main assignments loop)                     │
│                                                                     │
│  ┌───────────────────────────────┐                                  │
│  │ 1. init-existing-repository   │──────────────────────┐          │
│  └───────────────┬───────────────┘                      │          │
│                  │                                      │          │
│  ┌───────────────▼─────────────────────────────────┐    │          │
│  │ post-assignment-complete                        │    │          │
│  │  ├─ validate-assignment-completion              │    │          │
│  │  └─ report-progress                             │    │          │
│  └───────────────┬─────────────────────────────────┘    │          │
│                  │                                      │          │
│  ┌───────────────▼───────────────┐                      │          │
│  │ 2. create-app-plan            │──────────────────────┤          │
│  └───────────────┬───────────────┘                      │          │
│                  │                                      │          │
│  ┌───────────────▼─────────────────────────────────┐    │          │
│  │ post-assignment-complete                        │    │          │
│  │  ├─ validate-assignment-completion              │    │          │
│  │  └─ report-progress                             │    │          │
│  └───────────────┬─────────────────────────────────┘    │          │
│                  │                                      │          │
│  ┌───────────────▼───────────────────┐                  │          │
│  │ 3. create-project-structure       │──────────────────┤          │
│  └───────────────┬───────────────────┘                  │          │
│                  │                                      │          │
│  ┌───────────────▼─────────────────────────────────┐    │          │
│  │ post-assignment-complete                        │    │          │
│  │  ├─ validate-assignment-completion              │    │          │
│  │  └─ report-progress                             │    │          │
│  └───────────────┬─────────────────────────────────┘    │          │
│                  │                                      │          │
│  ┌───────────────▼───────────────┐                      │          │
│  │ 4. create-agents-md-file      │──────────────────────┤          │
│  └───────────────┬───────────────┘                      │          │
│                  │                                      │          │
│  ┌───────────────▼─────────────────────────────────┐    │          │
│  │ post-assignment-complete                        │    │          │
│  │  ├─ validate-assignment-completion              │    │          │
│  │  └─ report-progress                             │    │          │
│  └───────────────┬─────────────────────────────────┘    │          │
│                  │                                      │          │
│  ┌───────────────▼───────────────────┐                  │          │
│  │ 5. debrief-and-document           │──────────────────┤          │
│  └───────────────┬───────────────────┘                  │          │
│                  │                                      │          │
│  ┌───────────────▼─────────────────────────────────┐    │          │
│  │ post-assignment-complete                        │    │          │
│  │  ├─ validate-assignment-completion              │    │          │
│  │  └─ report-progress                             │    │          │
│  └───────────────┬─────────────────────────────────┘    │          │
│                  │                                      │          │
│  ┌───────────────▼───────────────────┐                  │          │
│  │ 6. pr-approval-and-merge          │──────────────────┘          │
│  │    (receives $pr_num from #1)     │                             │
│  └───────────────┬───────────────────┘                             │
│                  │                                                 │
│  ┌───────────────▼─────────────────────────────────┐               │
│  │ post-assignment-complete                        │               │
│  │  ├─ validate-assignment-completion              │               │
│  │  └─ report-progress                             │               │
│  └───────────────┬─────────────────────────────────┘               │
└──────────────────┼─────────────────────────────────────────────────┘
                   │
┌──────────────────▼─────────────────────────────────────────────────┐
│ post-script-complete                                                │
│ ┌────────────────────────────────────────────┐                     │
│ │ Apply orchestration:plan-approved label    │                     │
│ │ to the application plan issue from #2      │                     │
│ └────────────────────────────────────────────┘                     │
└────────────────────────────────────────────────────────────────────┘
```

**Data flow:**
- Assignment 1 outputs `pr_num` → consumed by Assignment 6
- Assignment 2 outputs `plan_issue_number` → consumed by `post-script-complete`
- Each assignment's `post-assignment-complete` event runs `validate-assignment-completion` (independent QA agent) then `report-progress` (state checkpoint + issue filing)

---

## 5. Open Questions

### Q1: Branch Protection PAT Scope
The `init-existing-repository` assignment requires importing a branch protection ruleset via `GH_ORCHESTRATOR_AGENT_TOKEN` (a PAT with `administration: write`). If this token is not available or lacks the scope, should the assignment skip this step or halt?
**Recommendation:** Halt and report — branch protection is a security gate.

### Q2: GitHub Project Creation Permissions
Creating a GitHub Project and linking it to the repository requires `project` and `read:project` scopes. The default `GITHUB_TOKEN` in Actions may not have these scopes. If project creation fails, should the workflow continue without it?
**Recommendation:** Attempt creation; if it fails due to permissions, log a warning and continue. The project board is a convenience, not a blocker.

### Q3: Application Plan Issue Template
The `create-app-plan` assignment references `.github/ISSUE_TEMPLATE/application-plan.md` as the template. This file may not exist in a freshly cloned template repo. Should the agent create it or use the inline template from the assignment's Appendix A?
**Recommendation:** Use the inline template from the assignment if the file doesn't exist.

### Q4: Reference Code Promotion Strategy
The plan_docs/ directory contains reference implementations with known issues (from Plan Review). When `create-project-structure` promotes code to `src/`, should it fix the known issues or copy as-is?
**Recommendation:** Promote with fixes applied. The Plan Review issues (I-1 through I-10) are well-documented and should be resolved during promotion.

### Q5: Test Framework Selection
The Implementation Spec doesn't specify a Python test framework. Should the project use `pytest`, `unittest`, or another framework?
**Recommendation:** Use `pytest` — it's the Python ecosystem standard, works well with `uv`, and supports async testing needed for the async Sentinel and Notifier code.

### Q6: Linting/Formatting Tools
The project needs linting and formatting tools for CI. Should it use `ruff`, `flake8`, `black`, or another toolset?
**Recommendation:** Use `ruff` — it's an extremely fast Python linter and formatter that replaces both `flake8` and `black`. It's well-suited for CI pipelines.

---

## 6. Self-Approval

This workflow execution plan is **self-approved** by the orchestrator agent. This is acceptable because:

1. This is an automated orchestrator-driven workflow execution plan — not a code change requiring human review.
2. The plan synthesizes information from existing, already-reviewed plan documents.
3. The `project-setup` workflow specification explicitly allows orchestrator self-approval for the setup PR.
4. Open questions are documented above for stakeholder awareness.
5. The plan will be validated through the `validate-assignment-completion` event after each assignment.

**Approved:** 2026-04-20
**Approver:** Orchestrator Agent (automated)

---

## 7. Appendix: Event Assignment Summary

### `validate-assignment-completion`
- **Goal:** Validate that a completed assignment met all acceptance criteria using an independent QA agent
- **Key Steps:** Identify assignment → read acceptance criteria → verify file outputs → run verification commands → create validation report → determine pass/fail
- **Output:** Validation report at `docs/validation/VALIDATION_REPORT_<assignment>_<timestamp>.md`
- **Blocking:** If validation fails, workflow halts — does NOT proceed to next assignment

### `report-progress`
- **Goal:** Generate progress report, capture outputs, checkpoint state, and file action items after each step
- **Key Steps:** Generate structured progress report → capture step outputs → validate acceptance criteria → create checkpoint state → file GitHub issues for action items → optional user notification
- **Output:** Progress report logged, action items filed as GitHub issues
- **Note:** Any deviation, finding, or plan-impacting discovery MUST be filed as a GitHub issue

### `post-script-complete` (final event)
- **Action:** Apply `orchestration:plan-approved` label to the application plan issue created during `create-app-plan`
- **Purpose:** Signal that the plan is ready for epic creation, triggering the next phase of the orchestration pipeline
