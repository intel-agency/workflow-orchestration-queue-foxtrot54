# OS-APOW

**Orchestration System for AI-Powered Operations Workflow**

A paradigm shift from Interactive AI Coding to Headless Agentic Orchestration. OS-APOW transforms GitHub Issues into "Execution Orders" autonomously fulfilled by specialized AI agents.

## Overview

OS-APOW represents a self-bootstrapping, event-driven infrastructure that manages AI agent workflows through GitHub's native primitives (Issues, Labels, Comments). The system is designed to be autonomous once seeded, using its own orchestration capabilities to refine its components.

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

### Components

1. **The Ear (Notifier)** - FastAPI webhook receiver for GitHub events
2. **The State (Queue)** - GitHub Issues as distributed state machine
3. **The Brain (Sentinel)** - Persistent supervisor managing worker lifecycles
4. **The Hands (Worker)** - Opencode CLI agent in devcontainer environment

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker (optional, for containerized deployment)

### Installation

```bash
# Clone the repository
git clone https://github.com/intel-agency/workflow-orchestration-queue-foxtrot54.git
cd workflow-orchestration-queue-foxtrot54

# Install dependencies with uv
uv sync

# Copy environment configuration
cp .env.example .env
# Edit .env with your values
```

### Running Services

```bash
# Start the webhook notifier
uv run uvicorn osapow.notifier.service:app --reload

# Or start the sentinel orchestrator
uv run python -m osapow.sentinel.orchestrator

# Or use Docker Compose for all services
docker-compose up -d
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=osapow

# Run specific test file
uv run pytest tests/test_work_item.py -v
```

## Project Structure

```
src/osapow/
├── __init__.py           # Package exports
├── __main__.py           # Entry point for python -m osapow
├── models/               # Data models (WorkItem, TaskType, Status)
│   ├── __init__.py
│   └── work_item.py
├── queue/                # GitHub-backed task queue
│   ├── __init__.py
│   └── github_queue.py
├── sentinel/             # Orchestrator service
│   ├── __init__.py
│   └── orchestrator.py
└── notifier/             # Webhook receiver service
    ├── __init__.py
    └── service.py

tests/                    # Test suite
├── conftest.py
├── test_work_item.py
├── test_github_queue.py
└── test_orchestrator.py
```

## Task State Machine

| Label | State | Description |
|-------|-------|-------------|
| `agent:queued` | Queued | Task validated, awaiting Sentinel |
| `agent:in-progress` | In Progress | Sentinel has claimed the issue |
| `agent:reconciling` | Reconciling | Stale task recovery state |
| `agent:success` | Success | Terminal success state |
| `agent:error` | Error | Technical failure |
| `agent:infra-failure` | Infra Failure | Infrastructure-level failure |

## Environment Variables

### Required

| Variable | Purpose |
|----------|---------|
| `GITHUB_TOKEN` | GitHub App installation token |
| `GITHUB_ORG` | Target organization name |
| `GITHUB_REPO` | Target repository name |
| `SENTINEL_BOT_LOGIN` | Bot account login for assign-then-verify |

### Optional

| Variable | Default | Purpose |
|----------|---------|---------|
| `WEBHOOK_SECRET` | - | HMAC secret for webhook verification |
| `LOG_LEVEL` | INFO | Logging level |
| `SENTINEL_POLL_INTERVAL` | 60 | Polling interval in seconds |

## Technology Stack

- **Language**: Python 3.12+
- **Web Framework**: FastAPI with Uvicorn
- **HTTP Client**: HTTPX (async)
- **Data Validation**: Pydantic v2
- **Package Manager**: uv
- **Containerization**: Docker / Docker Compose
- **Testing**: pytest, pytest-asyncio, pytest-cov

## Security

- HMAC SHA256 webhook signature verification
- Credential scrubbing for all public outputs
- Non-root container user
- Network isolation via Docker bridge

## Documentation

- [Technology Stack](plan_docs/tech-stack.md)
- [Architecture Guide](plan_docs/architecture.md)

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

This is an AI-orchestrated project. Issues are processed by the OS-APOW system itself. To contribute:

1. Open an issue with the appropriate template
2. The system will triage and process it automatically
3. Monitor progress via issue comments and labels
