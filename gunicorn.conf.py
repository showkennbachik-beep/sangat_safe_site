# gunicorn.conf.py  — production server configuration
import os

# Bind to PORT from environment (required by Google Cloud Run / App Engine)
bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"

# Workers: 1 per CPU core is the recommended baseline.
# Cloud Run uses threads-based concurrency per instance.
workers   = int(os.environ.get('GUNICORN_WORKERS', '2'))
threads   = int(os.environ.get('GUNICORN_THREADS', '4'))
worker_class = 'gthread'

# Generous timeout for PDF/image processing operations
timeout      = int(os.environ.get('GUNICORN_TIMEOUT', '300'))
keepalive    = 5
max_requests = 1000        # recycle workers periodically to prevent memory leaks
max_requests_jitter = 100

# Logging
accesslog  = '-'   # stdout (captured by Cloud Logging)
errorlog   = '-'   # stderr
loglevel   = os.environ.get('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s %(D)sµs'
