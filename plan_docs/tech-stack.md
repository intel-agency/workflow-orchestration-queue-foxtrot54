# OS-APOW Technology Stack

**Project:** workflow-orchestration-queue (OS-APOW)
**Generated:** 2026-03-20
**Source:** OS-APOW Implementation Specification v1.2

---

## Primary Language

| Language | Version | Purpose |
|----------|---------|---------|
| Python | 3.12+ | Primary language for Orchestrator, API Webhook receiver, and all system logic |
| PowerShell Core (pwsh) | 7.x | Shell Bridge Scripts, Auth synchronization, cross-platform CLI |
| Bash | 5.x | Shell Bridge Scripts, container orchestration |

---

## Web Framework & Server

| Component | Technology | Purpose |
|-----------|------------|---------|
| Web Framework | FastAPI | High-performance async web framework for Webhook Notifier |
| ASGI Server | Uvicorn | Lightning-fast ASGI server for production deployment |
| API Documentation | Swagger/OpenAPI | Auto-generated from FastAPI endpoints |

---

## Data Validation & Settings

| Component | Technology | Purpose |
|-----------|------------|---------|
| Data Validation | Pydantic v2 | Strict data validation, settings management, schema definitions |
| Configuration | pydantic-settings | Environment variable parsing and validation |

---

## HTTP & Async

| Component | Technology | Purpose |
|-----------|------------|---------|
| HTTP Client | HTTPX | Fully asynchronous HTTP client for GitHub API calls |
| Async Runtime | asyncio | Native Python async/await for concurrent operations |

---

## Package Management

| Component | Technology | Purpose |
|-----------|------------|---------|
| Package Manager | uv | Rust-based Python package installer (orders of magnitude faster than pip) |
| Lock File | uv.lock | Deterministic lockfile for exact package versions |
| Project Config | pyproject.toml | Modern Python project configuration |

---

## Containerization

| Component | Technology | Purpose |
|-----------|------------|---------|
| Container Runtime | Docker | Worker environment sandboxing, lifecycle management |
| Orchestration | Docker Compose | Multi-container needs (web app + database scenarios) |
| Dev Environment | DevContainers | Reproducible development environment with VS Code |

---

## LLM Integration

| Component | Technology | Purpose |
|-----------|------------|---------|
| Agent Runtime | opencode CLI v1.2.24 | AI agent execution framework |
| LLM Provider | ZhipuAI GLM-5 | Primary language model |
| Secondary LLM | Claude 3.5 Sonnet | Alternative model option |

---

## MCP Servers

| Component | Technology | Purpose |
|-----------|------------|---------|
| Sequential Thinking | @modelcontextprotocol/server-sequential-thinking | Step-by-step reasoning |
| Memory | @modelcontextprotocol/server-memory | Knowledge graph persistence |

---

## GitHub Integration

| Component | Technology | Purpose |
|-----------|------------|---------|
| GitHub API | REST API v3 | Issue management, labels, comments |
| GitHub CLI | gh | Repository operations, project management |
| Authentication | GitHub App | Installation tokens for API access |
| Webhook Security | HMAC SHA256 | Payload signature verification |

---

## Security Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Secret Management | Environment Variables | Ephemeral credential injection |
| Credential Scrubbing | Regex-based sanitization | Remove secrets from public logs |
| Network Isolation | Docker bridge network | Worker container isolation |
| Resource Constraints | Docker cgroups | CPU/RAM limits (2 CPUs, 4GB RAM) |

---

## Logging & Observability

| Component | Technology | Purpose |
|-----------|------------|---------|
| Logging | Python logging (StreamHandler) | Structured console output |
| Container Logs | Docker logs | Captured by container runtime |
| Heartbeat System | GitHub Issue Comments | Public task status updates |

---

## Testing

| Component | Technology | Purpose |
|-----------|------------|---------|
| Test Framework | pytest | Unit and integration tests |
| Async Testing | pytest-asyncio | Async test support |
| HTTP Mocking | pytest-httpx or respx | API response mocking |
| Coverage | pytest-cov | Test coverage reporting |

---

## Documentation

| Component | Technology | Purpose |
|-----------|------------|---------|
| Inline Docs | Sphinx/Google docstrings | Code documentation |
| API Docs | Auto-generated Swagger | FastAPI endpoint documentation |
| Instruction Modules | Markdown | LLM behavior configuration |

---

## Key Constraints

1. **No .NET/global.json** - This is a pure Python ecosystem project
2. **Shell-Bridge Pattern** - All container interactions via `devcontainer-opencode.sh`
3. **uv-only** - No pip, poetry, or conda; use `uv` exclusively
4. **Async-first** - All I/O operations should be async

---

## Environment Variables

### Required (3 vars only per Simplification Report S-3)

| Variable | Purpose |
|----------|---------|
| `GITHUB_TOKEN` | GitHub App installation token |
| `GITHUB_ORG` | Target organization name |
| `SENTINEL_BOT_LOGIN` | Bot account login for assign-then-verify locking |

### Optional

| Variable | Default | Purpose |
|----------|---------|---------|
| `WEBHOOK_SECRET` | - | HMAC secret for webhook verification |
| `GITHUB_REPO` | - | Target repository (single-repo mode) |

---

## Related Documents

- [OS-APOW Architecture Guide v3.2](./OS-APOW%20Architecture%20Guide%20v3.2.md)
- [OS-APOW Development Plan v4.2](./OS-APOW%20Development%20Plan%20v4.2.md)
- [OS-APOW Implementation Specification v1.2](./OS-APOW%20Implementation%20Specification%20v1.2.md)
- [OS-APOW Simplification Report v1](./OS-APOW%20Simplification%20Report%20v1.md)
