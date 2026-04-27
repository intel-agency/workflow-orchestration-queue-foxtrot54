# AGENTS.md

Guidance for AI coding agents working on the OS-APOW project.

## Project Overview

**OS-APOW** (Orchestration System for AI-Powered Operations Workflow) is a GitHub Actions-based AI orchestration system that transforms GitHub events (issues, PR comments, reviews) into autonomous work orders. It uses devcontainers and the opencode CLI to run AI agents.

### Purpose

- Transform GitHub Issues into "Execution Orders" autonomously fulfilled by specialized AI agents
- Event-driven infrastructure managing AI agent workflows through GitHub primitives
- Self-bootstrapping system that can refine its own components

### Key Technologies

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.12+ | OS-APOW service implementation |
| uv | 0.10.9 | Python package manager |
| FastAPI | 0.115+ | Web framework (notifier service) |
| Pydantic | 2.10+ | Data validation |
| opencode CLI | 1.2.24 | AI agent runtime |
| Node.js | 24.14.0 LTS | MCP server packages |
| .NET SDK | 10.0.102 | For .NET-based projects |
| Bun | 1.3.10 | Fast JS runtime/bundler |
| gh CLI | latest | GitHub API access |

### Architecture (4-Pillar)

1. **The Ear (Notifier)** - FastAPI webhook receiver for GitHub events
2. **The State (Queue)** - GitHub Issues as distributed state machine
3. **The Brain (Sentinel)** - Persistent supervisor managing worker lifecycles
4. **The Hands (Worker)** - Opencode CLI agent in devcontainer environment

## Setup Commands

### Install Dependencies

```bash
# Python/OS-APOW service development
uv sync                          # Install Python dependencies
uv sync --extra dev              # Install with dev tools (pytest, ruff, mypy)
```

### Run Services

```bash
# Start the webhook notifier
uv run uvicorn osapow.notifier.service:app --reload

# Start the sentinel orchestrator
uv run python -m osapow.sentinel.orchestrator

# Or use Docker Compose for all services
docker-compose up -d
```

### Linting

```bash
# Python linting and type checking
uv run ruff check src tests      # Lint Python code
uv run mypy src                  # Type check

# Shell scripts
shellcheck test/*.sh scripts/*.sh

# GitHub Actions workflows
actionlint

# Dockerfile
hadolint .github/.devcontainer/Dockerfile

# PowerShell scripts
pwsh -c "Invoke-ScriptAnalyzer -Path ./scripts/ -Recurse"
```

## Project Structure

```
src/osapow/                    # Python application (OS-APOW)
├── models/work_item.py        # Core data models + secret scrubbing
├── queue/github_queue.py      # GitHub-backed task queue (ITaskQueue)
├── sentinel/orchestrator.py   # Persistent supervisor
└── notifier/service.py        # FastAPI webhook receiver

tests/                         # Python unit tests (pytest)
├── conftest.py                # Shared fixtures
├── test_work_item.py          # Model tests
├── test_github_queue.py       # Queue tests
└── test_orchestrator.py       # Sentinel tests

.github/workflows/
├── orchestrator-agent.yml     # Main AI orchestration workflow
├── validate.yml               # CI: lint, test, devcontainer build
├── publish-docker.yml         # Build & push base Docker image
└── prebuild-devcontainer.yml  # Layer Features on base image

.devcontainer/                 # Consumer devcontainer (pulls GHCR image)
.github/.devcontainer/         # Build-time devcontainer (Dockerfile + Features)

.opencode/
├── agents/                    # Agent definitions (orchestrator, developer, etc.)
├── commands/                  # Reusable command prompts
└── opencode.json              # MCP server config, model selection

scripts/
├── devcontainer-opencode.sh   # Devcontainer orchestration
├── start-opencode-server.sh   # Opencode server lifecycle
├── assemble-orchestrator-prompt.sh  # Prompt assembly
└── *.ps1                      # PowerShell utilities (auth, labels, etc.)

test/                          # Shell-based tests
├── test-prompt-assembly.sh    # Prompt assembly validation
├── test-devcontainer-tools.sh # Tool availability smoke tests
├── test-image-tag-logic.sh    # Image tag resolution tests
└── fixtures/                  # Sample webhook payloads

local_ai_instruction_modules/  # Local instruction modules
plan_docs/                     # External-generated plan documents
```

## Testing Instructions

### Python Unit Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=osapow

# Run specific test file
uv run pytest tests/test_work_item.py -v

# Run tests matching a pattern
uv run pytest -k "test_name"
```

### Shell Tests

```bash
# All shell tests
bash test/test-prompt-assembly.sh
bash test/test-image-tag-logic.sh

# Dockerfile changes
bash test/test-devcontainer-tools.sh
```

### CI Pipeline

The `validate.yml` workflow runs on every push and PR:
- **lint**: actionlint, hadolint, shellcheck, PSScriptAnalyzer, JSON validation
- **scan**: gitleaks secret scanning
- **test-prompt-assembly**: Prompt assembly tests
- **test-image-tag-logic**: Image tag resolution tests
- **test-pester**: PowerShell tests (dry-run)
- **test-devcontainer-build**: Build devcontainer + smoke tests

## Code Style

### Python (ruff + mypy)

- Target: Python 3.12+
- Line length: 100 characters
- Strict mypy enabled
- Rules: pycodestyle (E/W), pyflakes (F), isort (I), bugbear (B), comprehensions (C4), pyupgrade (UP), unused-arguments (ARG), simplify (SIM)

### Shell Scripts

- Must pass `shellcheck --severity=warning`
- Use `set -euo pipefail`

### GitHub Actions Workflows

- Pin actions by SHA (not tag)
- Single `name:`, `on:`, `jobs:` per file

### General Conventions

- Keep changes minimal and targeted
- Never hardcode secrets/tokens
- Preserve the `{{__EVENT_DATA__}}` placeholder in prompt template
- Orchestrator delegates to specialists — never writes code directly
- Dockerfile lives at `.github/.devcontainer/Dockerfile`
- Consumer devcontainer uses `"image:"` — no local build

## Architecture Notes

### State Machine (Task Labels)

| Label | State | Terminal |
|-------|--------|----------|
| `agent:queued` | QUEUED | No |
| `agent:in-progress` | IN_PROGRESS | No |
| `agent:reconciling` | RECONCILING | No |
| `agent:success` | SUCCESS | Yes |
| `agent:error` | ERROR | Yes |
| `agent:infra-failure` | INFRA_FAILURE | Yes |
| `agent:stalled-budget` | STALLED_BUDGET | Yes |

### Concurrency Control

GitHub "Assignees" act as a distributed lock using the **assign-then-verify pattern**:
1. Attempt to assign `SENTINEL_BOT_LOGIN` to the issue
2. Re-fetch the issue
3. Verify the bot appears in assignees
4. Only then update labels and post claim comment

### Shell-Bridge Pattern

The orchestrator interacts with the agentic environment exclusively via `./scripts/devcontainer-opencode.sh`. This ensures environment parity between AI agents and human developers.

### MCP Servers

- `@modelcontextprotocol/server-sequential-thinking` — Step-by-step reasoning
- `@modelcontextprotocol/server-memory` — Knowledge graph persistence

## PR and Commit Guidelines

### Branch Naming

- Feature branches: `feature/<description>`
- Bug fixes: `fix/<description>`
- Workflow branches: `dynamic-workflow-<workflow-name>`

### Commit Messages

- Use clear, descriptive commit messages
- Reference issue numbers when applicable

### PR Requirements

- All CI checks must pass before merge
- Run `uv run pytest` and `uv run ruff check src tests` locally before pushing
- Monitor CI after push: `gh run list --limit 5`, `gh run watch <id>`

## Environment Variables

### Required (for OS-APOW services)

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub App installation token |
| `GITHUB_ORG` | Target organization |
| `GITHUB_REPO` | Target repository |
| `SENTINEL_BOT_LOGIN` | Bot account for locking |

### Required (for AI orchestration)

| Variable | Description |
|----------|-------------|
| `ZHIPU_API_KEY` | ZhipuAI model access |
| `KIMI_CODE_ORCHESTRATOR_AGENT_API_KEY` | Kimi model access (optional) |
| `GH_ORCHESTRATION_AGENT_TOKEN` | GitHub token for agent ops |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `WEBHOOK_SECRET` | - | HMAC verification |
| `LOG_LEVEL` | INFO | Logging verbosity |
| `SENTINEL_POLL_INTERVAL` | 60 | Polling seconds |

## Common Pitfalls

1. **Missing devcontainer image**: On fresh clones, run `publish-docker` then `prebuild-devcontainer` workflows first
2. **Python venv not active**: Use `uv run` prefix for all Python commands
3. **Missing secrets**: Set `ZHIPU_API_KEY` in repo Settings → Secrets
4. **Template placeholders**: Replace `workflow-orchestration-queue-foxtrot54` and `intel-agency` in cloned instances
5. **`.opencode/` directory**: Is checked out by `actions/checkout`; do not COPY it in the Dockerfile
6. **Credential scrubbing**: All worker output passes through `scrub_secrets()` which strips GitHub PATs, API keys, etc.

## Related Documentation

- [README.md](README.md) - Project overview and quick start
- [.ai-repository-summary.md](.ai-repository-summary.md) - Quick reference for AI coding agents
- [plan_docs/tech-stack.md](plan_docs/tech-stack.md) - Technology details
- [plan_docs/architecture.md](plan_docs/architecture.md) - Architecture details
