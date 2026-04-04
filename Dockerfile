FROM python:3.12-slim AS builder

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

WORKDIR /app

# Install dependencies first (cached layer)
COPY pyproject.toml ./
RUN uv pip install --system --no-cache .

# --- Runtime stage ---
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/gunicorn

# Copy application code
COPY agent/ agent/
COPY shared/ shared/
COPY web/ web/
COPY conventions/ conventions/

ENV PORT=8080
ENV STORAGE_BACKEND=firestore

EXPOSE ${PORT}

CMD exec gunicorn --bind :${PORT} --workers 2 --timeout 120 "web.app:create_app()"
