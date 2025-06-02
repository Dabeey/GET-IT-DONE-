# Base image (Python 3.11 + Slim for reduced size)
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app/main.py \
    FLASK_ENV=production

# Install system dependencies (including AI/ML tools)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libopenblas-dev && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m appuser
WORKDIR /app
RUN chown appuser:appuser /app
USER appuser

# Install Python dependencies (cached layer)
COPY --chown=appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser . .

# Expose port (adjust if needed)
EXPOSE 5000

# Run with Gunicorn (production WSGI server)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app.main:app"]