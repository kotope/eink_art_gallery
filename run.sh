#!/bin/bash

# Exit on any error
set -e

# Get port from environment variable or use default
PORT=${PORT:-8112}

# Log startup
echo "Starting E-Ink Gallery Service on port $PORT"

# Export port for Python app
export PORT

# Forward signals to the Python process
trap 'kill -TERM $PID' TERM INT

# Run the Python application in the foreground
cd /app && python3 /app/app.py &
PID=$!

# Wait for the process to finish
wait $PID
