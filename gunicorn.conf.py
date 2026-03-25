import multiprocessing
import os

bind = "0.0.0.0:8000"
worker_class = "uvicorn.workers.UvicornWorker"
workers = int(os.environ.get("WEB_CONCURRENCY", min(multiprocessing.cpu_count() * 2 + 1, 9)))
threads = 1

timeout = 60
graceful_timeout = 30
keepalive = 5

max_requests = 2000
max_requests_jitter = 200

preload_app = True

accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info").lower()

forwarded_allow_ips = "*"
proxy_protocol = False
proxy_allow_from = "*"
