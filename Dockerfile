# Use stable slim image (smaller + secure)
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system deps (only what you need)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Create and switch to non-root user
RUN useradd -m appuser
WORKDIR /app
RUN chown appuser:appuser /app
USER appuser

# Install Python deps (cached layer)
COPY --chown=appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code (excludes files in .dockerignore)
COPY --chown=appuser . .

# Run with Gunicorn (production WSGI server)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "main:main"]