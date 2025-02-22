#!/bin/bash

# Set default port if not provided
export PORT="${PORT:-8000}"

# Start Gunicorn with the correct port
exec gunicorn app:app --bind "0.0.0.0:$PORT" -c gunicorn.conf.py 