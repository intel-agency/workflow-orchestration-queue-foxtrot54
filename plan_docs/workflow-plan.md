# Workflow Execution Plan: project-setup

**Generated:** 2026-03-20  
**Workflow:** project-setup  
**Repository:** intel-agency/workflow-orchestration-queue-foxtrot54

---

## 1. Overview

**Workflow Name:** project-setup  
**Workflow File:** `ai_instruction_modules/ai-workflow-assignments/dynamic-workflows/project-setup.md`  
**Total Assignments:** 6 main + 1 pre-script + 2 post-assignment events

**Project:** workflow-orchestration-queue  
**Description:** A headless agentic orchestration platform that transforms GitHub Issues into automated Execution Orders, enabling AI agents to autonomously implement features, fix bugs, and manage development workflows without human-in-the-loop intervention.

**High-Level Summary:** This workflow initializes a fresh template clone repository for the workflow-orchestration-queue project, setting up GitHub project management, creating the application plan, scaffolding the project structure, and generating comprehensive documentation.

---

## 2. Project Context Summary

### Key Facts

| Aspect | Details |
|--------|---------|
| **Project Name** | workflow-orchestration-queue |
| **Repository** | intel-agency/workflow-orchestration-queue-foxtrot54 |
| **Language** | Python 3.12+ |
| **Primary Framework** | FastAPI |
| **Package Manager** | uv |
| **Containerization** | Docker, DevContainers |
| **Shell Scripts** | PowerShell Core, Bash |
| **Architecture** | 4-Pillar: Ear (Notifier), State (Queue), Brain (Sentinel), Hands (Worker) |

### Technology Stack

- **Runtime:** Python 3.12+
- **Web Framework:** FastAPI with Uvicorn
- **Validation:** Pydantic
- **HTTP Client:** HTTPX (async)
- **Package Manager:** uv (Rust-based, fast)
- **Containerization:** Docker, Docker Compose, DevContainers
- **Shell Scripts:** PowerShell Core (pwsh), Bash
- **LLM Integration:** opencode CLI, ZhipuAI GLM models

### Key Constraints

1. **No .NET/global.json** - This is a Python ecosystem project
2. **Shell-Bridge Pattern** - All container interactions via devcontainer-opencode.sh
3. **Markdown-as-Database** - GitHub Issues as primary state management
4. **Self-Bootstrapping** - System designed to build itself

### Known Risks

1. **Long-running subagent delegations** - Can appear as hangs (mitigated by heartbeat system)
2. **GitHub API Rate Limiting** - Use GitHub App tokens (5,000 req/hr)
3. **Concurrency Collisions** - Use assign-then-verify pattern
4. **State Bleed** - Environment reset between tasks

---

## 3. Assignment Execution Plan

### Pre-script-begin Event

| Field | Content |
|-------|---------|
| **Assignment** | `create-workflow-plan`: Create Workflow Plan |
| **Goal** | Create comprehensive workflow execution plan before any assignments begin |
| **Key Acceptance Criteria** | - Dynamic workflow read and understood<br>- All assignments traced<br>- All plan_docs/ read<br>- Workflow plan produced and approved<br>- Committed to plan_docs/workflow-plan.md |
| **Project-Specific Notes** | This is a Python ecosystem project, not .NET. Plan docs are comprehensive and well-structured. |
| **Prerequisites** | Dynamic workflow file accessible, plan_docs/ directory exists |
| **Dependencies** | None (first step) |
| **Risks / Challenges** | None identified |
| **Events** | None |

---

### Assignment 1: init-existing-repository

| Field | Content |
|-------|---------|
| **Assignment** | `init-existing-repository`: Initiate Existing Repository |
| **Goal** | Initialize GitHub project, labels, milestones from plan docs |
| **Key Acceptance Criteria** | - PR and new branch created<br>- Git Project created for issue tracking<br>- Git Project linked to repository<br>- Project columns created (Not Started, In Progress, In Review, Done)<br>- Labels imported<br>- Filenames changed to match project name |
| **Project-Specific Notes** | Repository is fresh template clone. Need to create GitHub Project for workflow-orchestration-queue. Labels file (.labels.json) does not exist yet - will need to create standard labels. |
| **Prerequisites** | GitHub authentication with repo, project scopes |
| **Dependencies** | None |
| **Risks / Challenges** | .labels.json not present - need to create standard labels |
| **Events** | post-assignment-complete: validate-assignment-completion, report-progress |

---

### Assignment 2: create-app-plan

| Field | Content |
|-------|---------|
| **Assignment** | `create-app-plan`: Create Application Plan |
| **Goal** | Parse plan docs, create application architecture plan documented in an issue |
| **Key Acceptance Criteria** | - Application template analyzed<br>- Plan documented in issue using template<br>- Milestones created and linked<br>- Issue added to GitHub Project<br>- Appropriate labels applied<br>- implementation:ready label applied |
| **Project-Specific Notes** | Plan docs are comprehensive: Implementation Spec v1.2, Development Plan v4.2, Architecture Guide v3.2. This is a Python project, not .NET. The app plan should follow the phased approach (Phase 0-3) documented in the plan docs. |
| **Prerequisites** | init-existing-repository complete, GitHub Project exists |
| **Dependencies** | GitHub Project from Assignment 1 |
| **Risks / Challenges** | Plan docs are extensive - need to synthesize into actionable plan |
| **Events** | pre-assignment-begin: gather-context<br>on-assignment-failure: recover-from-error<br>post-assignment-complete: report-progress |

---

### Assignment 3: create-project-structure

| Field | Content |
|-------|---------|
| **Assignment** | `create-project-structure`: Create Project Structure |
| **Goal** | Set up solution/project scaffolding for Python project |
| **Key Acceptance Criteria** | - Solution structure created<br>- All required project files and directories established<br>- Initial configuration files created<br>- Basic CI/CD pipeline structure established<br>- Documentation structure created<br>- Development environment validated<br>- Initial commit made<br>- Repository summary document created |
| **Project-Specific Notes** | This is a Python project using uv, not .NET. Structure should follow the project structure from Implementation Spec:
```
workflow-orchestration-queue/
├── pyproject.toml
├── uv.lock
├── src/
│   ├── notifier_service.py
│   ├── orchestrator_sentinel.py
│   ├── models/
│   │   ├── work_item.py
│   │   └── github_events.py
│   └── queue/
│       └── github_queue.py
├── scripts/
│   ├── devcontainer-opencode.sh
│   └── ...
├── local_ai_instruction_modules/
└── docs/
``` |
| **Prerequisites** | Application plan documented |
| **Dependencies** | Application plan from Assignment 2 |
| **Risks / Challenges** | Existing src/ directory in plan_docs may conflict - need to handle appropriately |
| **Events** | post-assignment-complete: validate-assignment-completion, report-progress |

---

### Assignment 4: create-repository-summary

| Field | Content |
|-------|---------|
| **Assignment** | `create-repository-summary`: Create Repository Summary |
| **Goal** | Create .ai-repository-summary.md file for AI agent onboarding |
| **Key Acceptance Criteria** | - .ai-repository-summary.md exists at repository root<br>- Contains project overview, tech stack<br>- Contains build/test commands (validated)<br>- Contains code style and conventions<br>- Contains project structure/layout<br>- File committed and pushed |
| **Project-Specific Notes** | Python project with uv package manager. Build commands: `uv sync`, `uv run`. Test commands: `uv run pytest`. Key scripts in scripts/ directory. |
| **Prerequisites** | Project structure created |
| **Dependencies** | Project structure from Assignment 3 |
| **Risks / Challenges** | Need to validate all commands work correctly |
| **Events** | post-assignment-complete: validate-assignment-completion, report-progress |

---

### Assignment 5: create-agents-md-file

| Field | Content |
|-------|---------|
| **Assignment** | `create-agents-md-file`: Create AGENTS.md File |
| **Goal** | Create AGENTS.md file following open specification for AI coding agents |
| **Key Acceptance Criteria** | - AGENTS.md exists at repository root<br>- Contains project overview, tech stack<br>- Contains setup/build/test commands (validated)<br>- Contains code style and conventions<br>- Contains project structure section<br>- Contains testing instructions<br>- Committed and pushed<br>- Stakeholder approval obtained |
| **Project-Specific Notes** | Complements README.md and .ai-repository-summary.md. Targets AI coding agents specifically. Should include Python/uv specific instructions. |
| **Prerequisites** | Project structure created, repository summary exists |
| **Dependencies** | Assignments 3 and 4 |
| **Risks / Challenges** | Need to ensure consistency with other documentation |
| **Events** | post-assignment-complete: validate-assignment-completion, report-progress |

---

### Assignment 6: debrief-and-document

| Field | Content |
|-------|---------|
| **Assignment** | `debrief-and-document`: Debrief and Document Learnings |
| **Goal** | Final summary, handoff documentation, lessons learned |
| **Key Acceptance Criteria** | - Detailed report created using template<br>- Report in .md format<br>- All required sections complete<br>- All deviations documented<br>- Report reviewed and approved<br>- Report committed and pushed<br>- Execution trace saved |
| **Project-Specific Notes** | Should capture all work done across the 6 assignments. Include execution trace of all commands run and files created/modified. |
| **Prerequisites** | All previous assignments complete |
| **Dependencies** | All previous assignments |
| **Risks / Challenges** | Need comprehensive documentation of all actions |
| **Events** | post-assignment-complete: validate-assignment-completion, report-progress |

---

## 4. Sequencing Diagram

```
pre-script-begin
└── create-workflow-plan ✓

initiate-new-repository (main step)
├── init-existing-repository
│   └── post-assignment-complete
│       ├── validate-assignment-completion
│       └── report-progress
├── create-app-plan
│   └── post-assignment-complete
│       ├── validate-assignment-completion
│       └── report-progress
├── create-project-structure
│   └── post-assignment-complete
│       ├── validate-assignment-completion
│       └── report-progress
├── create-repository-summary
│   └── post-assignment-complete
│       ├── validate-assignment-completion
│       └── report-progress
├── create-agents-md-file
│   └── post-assignment-complete
│       ├── validate-assignment-completion
│       └── report-progress
└── debrief-and-document
    └── post-assignment-complete
        ├── validate-assignment-completion
        └── report-progress
```

---

## 5. Open Questions

1. **Labels File:** The .labels.json file does not exist in the template. Should we create standard labels or use a specific label set for this project?

2. **Existing src/ in plan_docs:** The plan_docs/ directory contains a src/ subdirectory with Python files (notifier_service.py, orchestrator_sentinel.py). Should these be moved to the main src/ directory during project structure creation, or kept as reference implementations?

3. **GitHub Project Naming:** Should the GitHub Project be named exactly "workflow-orchestration-queue-foxtrot54" (matching repo) or just "workflow-orchestration-queue"?

---

## 6. Stakeholder Approval

**Plan Status:** Ready for Review

**Approval Required From:** Orchestrator/Stakeholder

> Does this workflow execution plan look correct? Are there any changes needed, or do you approve it?
