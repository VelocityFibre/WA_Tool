FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Clone WhatsApp MCP repository
RUN git clone https://github.com/lharries/whatsapp-mcp.git /app/whatsapp-mcp

# Install WhatsApp MCP dependencies
WORKDIR /app/whatsapp-mcp
RUN npm install

# Install backend dependencies
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install frontend dependencies and build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# Copy backend code
WORKDIR /app/backend
COPY backend/ .

# Copy startup script
WORKDIR /app
COPY docker/start.sh .
RUN chmod +x start.sh

# Expose ports
EXPOSE 8080 3000

# Start the application
CMD ["./start.sh"]
