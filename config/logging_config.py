"""
Formato JSON opcional (LOG_JSON=True) e request_id em todos os records.
"""
import json
import logging
from datetime import datetime, timezone

from config.middleware.request_id import get_request_id


class RequestIdFilter(logging.Filter):
    """Garante record.request_id para formatters (fora de request: '-')."""

    def filter(self, record):
        if not hasattr(record, 'request_id'):
            record.request_id = get_request_id() or '-'
        return True


class JsonLogFormatter(logging.Formatter):
    """Uma linha JSON por evento (agregadores / Loki / CloudWatch)."""

    def format(self, record):
        payload = {
            'ts': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'request_id': getattr(record, 'request_id', None) or '-',
        }
        if record.exc_info:
            payload['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def build_logging_dict(*, use_json: bool) -> dict:
    if use_json:
        formatter = 'json'
        fmt = None
    else:
        formatter = 'standard'
        fmt = '%(levelname)s %(request_id)s %(name)s %(message)s'

    return {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'request_id': {
                '()': 'config.logging_config.RequestIdFilter',
            },
        },
        'formatters': {
            'json': {
                '()': 'config.logging_config.JsonLogFormatter',
            },
            'standard': {
                'format': fmt,
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'filters': ['request_id'],
                'formatter': formatter,
            },
        },
        'root': {
            'handlers': ['console'],
            'level': os_level(),
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.server': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.request': {
                'handlers': ['console'],
                'level': 'WARNING',
                'propagate': False,
            },
        },
    }


def os_level() -> str:
    import os

    return os.getenv('LOG_LEVEL', 'INFO').upper()
