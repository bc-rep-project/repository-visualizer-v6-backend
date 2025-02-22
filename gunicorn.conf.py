# Gunicorn configuration file
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# Worker configuration
workers = 4
worker_class = 'sync'
timeout = 120

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Application configuration
wsgi_app = 'app:app'
chdir = '/' 