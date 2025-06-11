# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_service/ mcp_service/
COPY README.md .

# Create necessary directories
RUN mkdir -p /app/data /app/models

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Initialize SQLite database
RUN python -m mcp_service.init_local_db

# Expose port
EXPOSE 5555

# Run the service
CMD ["python", "-m", "mcp_service.mcp_service"]
