# Base image (Python 3.11 + Slim for reduced size)
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=main.py

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libopenblas-dev \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user and set workdir
RUN useradd -m appuser
WORKDIR /app

# Copy project files and set permissions
COPY . .
RUN chown -R appuser:appuser /app

# Install Python dependencies as root (so Gunicorn is in PATH)
RUN pip install --no-cache-dir -r requirements.txt

# Switch to non-root user
USER appuser

# Expose port (adjust if needed)
EXPOSE 5000

# Run with Gunicorn (production WSGI server)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "main:app"]