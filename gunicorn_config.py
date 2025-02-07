import os

# Get port from environment variable
port = int(os.environ.get('PORT', '10000'))

# Bind to 0.0.0.0 to make the server publicly accessible
bind = f"0.0.0.0:{port}"

# Worker configuration
workers = 4
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Reload
reload = False

# SSL
keyfile = None
certfile = None 