import os

# Get port from environment variable
port = os.environ.get('PORT', '8000')

# Bind to 0.0.0.0 to listen on all interfaces
bind = f"0.0.0.0:{port}"

# Worker configuration
workers = 4
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info' 