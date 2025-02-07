import os

# Worker configuration
workers = 4
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