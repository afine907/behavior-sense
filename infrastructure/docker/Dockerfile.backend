# BehaviorSense Dockerfile - Monorepo with uv
# Usage: docker build -f infrastructure/docker/Dockerfile --build-arg SERVICE=insight .

ARG PYTHON_VERSION=3.11

# ============================================
# Stage 1: Builder
# ============================================
FROM python:${PYTHON_VERSION}-slim AS builder
ARG SERVICE

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy workspace files
COPY pyproject.toml uv.lock* ./
COPY libs/core libs/core
COPY packages/${SERVICE} packages/${SERVICE}

# Install dependencies using uv
RUN uv sync --frozen --no-dev --package behavior-${SERVICE}

# ============================================
# Stage 2: Production image
# ============================================
FROM python:${PYTHON_VERSION}-slim AS runtime
ARG SERVICE

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY libs/core/src libs/core/src
COPY packages/${SERVICE}/src packages/${SERVICE}/src

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/libs/core/src:/app/packages/${SERVICE}/src"

# Set working directory
WORKDIR /app/packages/${SERVICE}/src

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Default command
CMD ["uvicorn", "behavior_${SERVICE}.main:app", "--host", "0.0.0.0", "--port", "8000"]
