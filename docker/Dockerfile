# Base Dockerfile for WhatsApp Group Monitoring Services
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1001 waservice && \
    chown -R waservice:waservice /app

# Switch to non-root user
USER waservice

# Expose the port (will be overridden by specific services)
EXPOSE 8080

# Default command (will be overridden by specific services)
CMD ["python", "app.py"]