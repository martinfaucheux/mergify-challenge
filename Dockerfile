# Use official Python image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml uv.lock ./

# Install dependencies in container's .venv (excluded from volume mount)
RUN uv sync --frozen

# Copy application code
COPY *.py ./

# Expose FastAPI port
EXPOSE 8000

# TODO: create a specific dockerfile for production use
# Run FastAPI in development mode with auto-reload
CMD ["uv", "run", "fastapi", "dev", "--host", "0.0.0.0", "--port", "8000"]
