"""
Configuração do Gunicorn (WSGI).
Variáveis opcionais: WEB_CONCURRENCY, GUNICORN_TIMEOUT, GUNICORN_BIND, etc.
"""
import multiprocessing
import os

bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")
default_workers = min(max((multiprocessing.cpu_count() or 1) * 2 + 1, 2), 8)
workers = int(os.environ.get("WEB_CONCURRENCY", str(default_workers)))
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "sync")
# sync ignora threads; gthread usa pool de threads por worker (bom para I/O, ex. API + ORM)
_default_threads = "4" if worker_class == "gthread" else "1"
threads = int(os.environ.get("GUNICORN_THREADS", _default_threads))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", "5"))
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", "50"))
accesslog = "-"
errorlog = "-"
capture_output = True
