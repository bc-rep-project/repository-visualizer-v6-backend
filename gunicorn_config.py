import os

# Worker configuration
workers = int(os.environ.get("GUNICORN_WORKERS", "3"))
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 2

# Logging configuration
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# SSL configuration
keyfile = None
certfile = None

# Reload
reload = False

# SSL
keyfile = None
certfile = None

# Update bind address to use PORT environment variable with 8000 as fallback
bind = "0.0.0.0:" + os.environ.get("PORT", "8000") 