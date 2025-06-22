# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend /app/backend/

# Create necessary directories
RUN mkdir -p /app/data /app/models /app/static

# Set environment variables
ENV PYTHONPATH=/app/backend
ENV PYTHONUNBUFFERED=1
ENV DB_HOST=192.168.10.14
ENV DB_PORT=5432
ENV DB_NAME=netmonitor_db
ENV DB_USER=netmonitor_user
ENV DB_PASSWORD=netmonitor_password
ENV DB_MIN_CONNECTIONS=5
ENV DB_MAX_CONNECTIONS=20
ENV DB_POOL_TIMEOUT=30
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379
ENV REDIS_DB=0
ENV REDIS_MAX_CONNECTIONS=10
ENV REDIS_SOCKET_TIMEOUT=5
ENV SERVICE_HOST=0.0.0.0
ENV SERVICE_PORT=5000
ENV LOG_LEVEL=info
ENV ANALYSIS_INTERVAL=300
ENV BATCH_SIZE=1000
ENV MAX_RETRIES=3
ENV RETRY_DELAY=5
ENV SQLITE_DB_PATH=/app/data/mcp_anomalies.db
ENV SQLITE_JOURNAL_MODE=WAL
ENV SQLITE_SYNCHRONOUS=NORMAL
ENV SQLITE_CACHE_SIZE=-2000
ENV SQLITE_TEMP_STORE=MEMORY
ENV SQLITE_MMAP_SIZE=30000000000

# Expose port
EXPOSE 5000

# Run the FastAPI application with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000", "--workers", "1", "--log-level", "info"]
