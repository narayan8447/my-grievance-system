# ============================================
# Stage 1: Build dependencies
# ============================================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

# Install build-time system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a virtual environment
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip setuptools && \
    /opt/venv/bin/pip install -r requirements.txt

# ============================================
# Stage 2: Production runtime
# ============================================
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUTF8=1 \
    DEBIAN_FRONTEND=noninteractive \
    # Railway injects PORT dynamically; default to 8000 for local Docker
    PORT=8000

WORKDIR /app

# Install runtime-only system dependencies (no build-essential)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    libmagic1 \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-tel \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built Python packages from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source code
COPY app/ ./app/
COPY gradio_app.py .
COPY requirements.txt .
COPY .env.example .

# Expose default ports (informational only — Railway ignores EXPOSE)
EXPOSE 8000
EXPOSE 7863

# Default: start backend. Railway overrides this via service start command.
# Uses shell form to allow $PORT variable expansion at runtime.
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
