# Development stage for dev containers
FROM python:3.11-slim as dev_containers_target_stage

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -u 1000 -s /sbin/nologin appuser

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app ./

# Create data directory and set proper ownership
RUN mkdir -p /data/eink_art/images && \
    chown -R appuser:appuser /data/eink_art && \
    chown -R appuser:appuser /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8112

# Expose port
EXPOSE 8112

# Switch to non-root user
USER appuser

# Run application (for production)
CMD ["python3", "app.py"]
