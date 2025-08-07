# Multi-stage build for optimized production image
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
RUN pip install --no-cache-dir uv

# Copy requirements and install dependencies
COPY pyproject.toml ./
RUN uv pip install --system -r pyproject.toml

# Production stage
FROM python:3.11-slim

# Set environment variables for production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=5000
ENV WEBHOOK_MODE=true

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app

# Create app directory and set ownership
WORKDIR /app
RUN chown app:app /app

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libjpeg62-turbo \
    zlib1g \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy application code with proper ownership
COPY --chown=app:app . .

# Create necessary directories with proper permissions
RUN mkdir -p uploads processed static/css static/js templates \
    && chown -R app:app uploads processed \
    && chmod -R 755 /app

# Switch to non-root user
USER app

# Expose port
EXPOSE $PORT

# Health check with webhook support
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Production start command with webhook support
CMD ["sh", "-c", "if [ \"$WEBHOOK_MODE\" = \"true\" ]; then python webhook_server.py; else gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --keepalive 5 --max-requests 1000 --preload main:app; fi"]