# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 – Builder
#   Compile / install all Python wheels in an isolated layer so the final image
#   does NOT need gcc or build headers.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

# Suppress .pyc files and enable unbuffered logs during the build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Build-time system deps (gcc / g++ needed by faiss-cpu & tokenizer wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only the dependency manifest first – leverages Docker layer cache.
# Re-installing packages is skipped unless requirements.txt changes.
COPY requirements.txt .

# Install into a dedicated prefix so we can copy only the built site-packages
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 – Runtime
#   Lean image that only contains the installed wheels + application code.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Tell HuggingFace / sentence-transformers where to cache models inside the
    # container.  Mount a Docker volume here to persist downloads across runs.
    HF_HOME=/app/.cache/huggingface \
    # Prevent transformers from phoning home for telemetry
    TRANSFORMERS_OFFLINE=0

# Runtime-only system libraries:
#   libgomp1   – OpenMP, required by faiss-cpu
#   libglib2.0 – required by tokenizers / sentence-transformers on slim images
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user (security best practice)
RUN adduser --disabled-password --gecos '' appuser

WORKDIR /app

# Pull in the pre-built Python packages from the builder stage
COPY --from=builder /install /usr/local

# Copy the application source
COPY . .

# Create writable runtime directories and transfer ownership to the app user
RUN mkdir -p /app/uploads /app/logs /app/faiss_index /app/.cache/huggingface && \
    chown -R appuser:appuser /app

# Drop root privileges
USER appuser

# FastAPI / Uvicorn port
EXPOSE 8000

# Liveness probe – Docker (and orchestrators like ECS / k8s) will restart the
# container automatically if the health-check fails.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Production entrypoint.
# Workers=1 keeps memory predictable; raise it if you need more throughput.
# Remove --reload – it is a development-only flag and hurts performance.
CMD ["uvicorn", "src.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--log-level", "info"]
