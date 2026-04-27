# OS-APOW Documentation

This directory contains additional documentation for the OS-APOW project.

## Contents

- [README.md](./README.md) - This index file

## Architecture Documentation

For detailed architecture information, see the plan documents:

- [Technology Stack](../plan_docs/tech-stack.md) - Complete technology stack details
- [Architecture Guide](../plan_docs/architecture.md) - 4-Pillar architecture overview

## API Documentation

The FastAPI application provides auto-generated API documentation:

- **Swagger UI**: Available at `/docs` when running the notifier service
- **ReDoc**: Available at `/redoc` when running the notifier service

## Development Guides

### Running Locally

1. Set up environment variables (copy `.env.example` to `.env`)
2. Install dependencies: `uv sync`
3. Run services as needed (see main README.md)

### Testing

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage report
uv run pytest --cov=osapow --cov-report=html
```

### Code Quality

```bash
# Run linter
uv run ruff check src tests

# Run type checker
uv run mypy src
```

## Related Documents

- [AGENTS.md](../AGENTS.md) - Agent instructions for AI development
- [plan_docs/](../plan_docs/) - Planning and specification documents
