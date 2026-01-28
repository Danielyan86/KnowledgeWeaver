# Multi-stage build for KnowledgeWeaver API
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Set PATH to include pip installed packages
ENV PATH=/root/.local/bin:$PATH

# Create necessary directories
RUN mkdir -p data/storage/vector_db data/checkpoints data/progress data/inputs/__enqueued__ logs

# Expose port
EXPOSE 9621

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
  CMD curl -f http://localhost:9621/health || exit 1

# Run the application
CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "9621"]
