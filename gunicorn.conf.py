# Gunicorn configuration file
import multiprocessing
import os

# Worker processes - limit to a reasonable number
workers = min(multiprocessing.cpu_count(), 4)  # Max 4 workers
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'debug'  # Temporarily increase log level for debugging

# Process naming
proc_name = 'repository-visualizer'

# SSL config
keyfile = None
certfile = None

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Avoid thundering herd
preload_app = True

# Error handling
capture_output = True
enable_stdio_inheritance = True

# Max requests per worker before reload
max_requests = 1000
max_requests_jitter = 50 