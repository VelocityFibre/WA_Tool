FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python requirements
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py ./
COPY *.json ./ 

# Create directories for logs and data
RUN mkdir -p /app/logs

# Volume for logs
VOLUME ["/app/logs"]

# Health check (checks if WhatsApp Bridge is accessible)
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://whatsapp-bridge:8080 || exit 1

# Default command (can be overridden in docker-compose)
CMD ["python", "realtime_drop_monitor.py", "--interval", "15"]