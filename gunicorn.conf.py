"""Gunicorn configuration for production deployment."""
import multiprocessing

# Bind to localhost, nginx will proxy
bind = "127.0.0.1:8000"

# Workers - 2-4 x CPU cores is recommended
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class
worker_class = "sync"

# Timeout for workers
timeout = 120

# Keep-alive
keepalive = 5

# Logging
accesslog = "/var/log/solio/access.log"
errorlog = "/var/log/solio/error.log"
loglevel = "info"

# Process naming
proc_name = "solio"

# Reload on code changes (only for development)
reload = False

# Preload app for performance
preload_app = True

# Max requests per worker before restart (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 100
