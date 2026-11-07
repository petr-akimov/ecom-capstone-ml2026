#!/bin/sh
set -e

echo "Starting FastAPI backend on port 32000..."
python -m scripts.main &

echo "Starting Nginx frontend on port 8080..."
exec nginx -g "daemon off;"