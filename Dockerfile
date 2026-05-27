# ============================================================
# SANGAT Tools — Dockerfile (targets Google Cloud Run)
# Build:   docker build -t sangat-safe-site .
# Run:     docker run -p 8080:8080 -e SECRET_KEY=change-me sangat-safe-site
# Deploy:  gcloud run deploy sangat-safe-site --source .
# ============================================================
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system-level dependencies
# - tesseract-ocr: required by pytesseract (OCR tool)
# - libgl1: required by PyMuPDF/OpenCV on slim base images
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (cached layer — only rebuilds when requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Create required directories (not tracked in git)
RUN mkdir -p static/uploads outputs

# Non-root user for security
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

# Environment defaults (override via Cloud Run environment variables or --env-vars)
ENV PORT=8080
ENV FLASK_ENV=production
ENV GUNICORN_WORKERS=1
ENV GUNICORN_THREADS=8
ENV GUNICORN_TIMEOUT=300

EXPOSE 8080

# Health check (Cloud Run uses /healthz defined in app.py)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/healthz')"

CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
