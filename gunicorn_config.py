import os

# Get port from Render's environment variable
port = int(os.environ.get('PORT', 10000))

# Bind to the port from environment variable
bind = f"0.0.0.0:{port}"  # Use f-string to insert port variable

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