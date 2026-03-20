# OS-APOW Application Dockerfile
# Multi-stage build for optimized production image

# Build stage
FROM python:3.12-slim AS builder

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml .

# Copy source code before install (required for editable install)
COPY src/ ./src/

# Install dependencies
RUN uv pip install --system --no-cache -e .

# Production stage
FROM python:3.12-slim AS production

# Create non-root user for security
RUN groupadd --gid 1000 osapow && \
    useradd --uid 1000 --gid osapow --shell /bin/bash --create-home osapow

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=osapow:osapow src/ ./src/
COPY --chown=osapow:osapow pyproject.toml .

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

# Switch to non-root user
USER osapow

# Expose port for notifier service
EXPOSE 8000

# Default command runs the notifier service
CMD ["uvicorn", "osapow.notifier.service:app", "--host", "0.0.0.0", "--port", "8000"]
