FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies and Trivy
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin \
    && rm -rf /var/lib/apt/lists/*

# Pre-download the Trivy vulnerability DB at build time so the first scan is fast
ENV TRIVY_CACHE_DIR=/var/cache/trivy
RUN mkdir -p /var/cache/trivy \
    && trivy image --download-db-only --cache-dir /var/cache/trivy

# Install backend dependencies (worker needs the FastAPI/Celery app package)
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/backend/requirements.txt

# Install scanner dependencies
COPY scanner/requirements.txt /app/scanner/requirements.txt
RUN pip install --no-cache-dir -r /app/scanner/requirements.txt

# Copy backend app and scanner package per the runtime layout in the shared contract
COPY backend/app /app/app
COPY scanner /app/scanner

ENV PYTHONPATH=/app
ENV SCANNER_MODE=real

# Non-root user, owning the Trivy cache so it can read/write it at runtime
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /var/cache/trivy /app
USER appuser

EXPOSE 8001

CMD ["celery", "-A", "app.worker", "worker", "--loglevel=info", "--pool=threads", "--concurrency=4"]
