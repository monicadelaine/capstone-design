import os

bind = "0.0.0.0:8000"

workers = int(os.getenv("GUNICORN_WORKERS", "2"))
worker_class = "sync"

timeout = 60
graceful_timeout = 30
keepalive = 5

max_requests = 1000
max_requests_jitter = 100

accesslog = "-"
errorlog = "-"
loglevel = "info"

proc_name = "capstone-backend"
preload_app = True
