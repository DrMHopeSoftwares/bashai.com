#!/bin/bash
echo "Starting bhashai.com on port $PORT"
echo "Using full app with JS fixes and debug route..."

python3 -m gunicorn main:app --bind 0.0.0.0:$PORT --timeout 120 --log-level info --workers 1
