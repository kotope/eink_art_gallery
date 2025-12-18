#!/bin/bash

set -e

# Get port from environment variable or use default
PORT=${PORT:-8112}

# Log startup
echo "Starting E-Ink Gallery Service on port $PORT"

# Export port for Python app
export PORT

# Run the Python application
cd /app/app && python3 /app/app/app.py
