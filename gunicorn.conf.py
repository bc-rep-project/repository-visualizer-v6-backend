# Gunicorn configuration file
import multiprocessing

# Worker processes
workers = 4  # Fixed number of workers
worker_class = 'sync'
timeout = 120
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process naming
proc_name = 'repository-visualizer'

# Server mechanics
daemon = False
preload_app = True

# Error handling
capture_output = True
enable_stdio_inheritance = True 