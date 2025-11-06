FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    # Use a different venv location to avoid conflicts with mounted volumes
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies to /opt/venv instead of .venv
RUN uv sync --frozen --no-cache

# Copy application code
COPY . .

EXPOSE 8000

# Use PORT environment variable (Cloud Run sets this to 8080)
CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
