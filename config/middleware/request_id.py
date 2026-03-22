"""
Gera ou propaga X-Request-ID para correlação em logs e suporte.
"""
import contextvars
import re
import uuid

_REQUEST_ID_CTX: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    'request_id', default=None
)

# Aceita UUID ou string curta alfanumérica (ex.: de API gateways)
_REQUEST_ID_RE = re.compile(r'^[a-zA-Z0-9-]{8,128}$')


def get_request_id() -> str | None:
    return _REQUEST_ID_CTX.get()


class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        raw = request.META.get('HTTP_X_REQUEST_ID', '').strip()
        if raw and _REQUEST_ID_RE.match(raw):
            rid = raw
        else:
            rid = str(uuid.uuid4())
        request.request_id = rid
        token = _REQUEST_ID_CTX.set(rid)
        try:
            response = self.get_response(request)
        finally:
            _REQUEST_ID_CTX.reset(token)
        response['X-Request-ID'] = rid
        return response
