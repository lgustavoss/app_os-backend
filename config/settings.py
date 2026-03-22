"""
Django settings for app_os project.
"""

import os
import warnings
from pathlib import Path
from dotenv import load_dotenv

from config.logging_config import build_logging_dict

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

USE_TLS = os.getenv('USE_TLS', 'False') == 'True'


def _csv_env(name: str) -> list[str]:
    raw = os.getenv(name, '').strip()
    if not raw:
        return []
    return [x.strip() for x in raw.split(',') if x.strip()]


def _validate_secret_key_for_production(key: str) -> None:
    """Alinha-se ao security.W009 do check --deploy."""
    from django.core.exceptions import ImproperlyConfigured

    if len(key) < 50 or len(set(key)) < 5 or key.startswith('django-insecure-'):
        raise ImproperlyConfigured(
            'Com DEBUG=False, defina SECRET_KEY forte (50+ caracteres, boa entropia, sem prefixo '
            'django-insecure-). Gere com: python -c "from django.core.management.utils import '
            'get_random_secret_key; print(get_random_secret_key())"'
        )


if not DEBUG:
    _validate_secret_key_for_production(SECRET_KEY)

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if h.strip()
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'drf_spectacular',
    'corsheaders',
    
    # Local apps
    'autenticacao',
    'configuracoes',
    'clientes',
    'ordens_servico',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'config.middleware.request_id.RequestIdMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'app_os'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Cache: django-ratelimit no login. LocMem não é compartilhado entre workers Gunicorn;
# em produção com vários workers use CACHE_URL=redis://...
_cache_url = os.getenv('CACHE_URL', '').strip()
if _cache_url.startswith('redis://'):
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': _cache_url,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'app-os-cache',
        }
    }

# Sessão e escala horizontal
# - `db` (padrão): tabela django_session no Postgres — todas as réplicas/backend partilham a mesma BD,
#   logo não precisa de sticky sessions (só mais leituras/escritas na BD).
# - `cache`: só Redis (rápido; se o Redis falhar ou expulsar chaves, sessões podem perder-se).
# - `cached_db`: Redis + Postgres — leituras rápidas, persistência na BD (recomendado com Redis).
_session_store = os.getenv('SESSION_STORE', 'db').strip().lower()
if _session_store not in ('db', 'cache', 'cached_db'):
    _session_store = 'db'

if _session_store == 'db':
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'
elif _session_store == 'cache':
    if not _cache_url.startswith('redis://'):
        from django.core.exceptions import ImproperlyConfigured

        raise ImproperlyConfigured(
            'SESSION_STORE=cache exige CACHE_URL apontando para Redis (ex.: redis://redis:6379/1). '
            'LocMem não é partilhado entre workers/réplicas.'
        )
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
else:
    if not _cache_url.startswith('redis://'):
        from django.core.exceptions import ImproperlyConfigured

        raise ImproperlyConfigured(
            'SESSION_STORE=cached_db exige CACHE_URL com Redis (cache partilhado entre réplicas).'
        )
    SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
    SESSION_CACHE_ALIAS = 'default'

RATELIMIT_USE_CACHE = 'default'
LOGIN_RATE_LIMIT = os.getenv('LOGIN_RATE_LIMIT', '20/m')


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

# Política do sistema: só tamanho mínimo; letras, números e símbolos permitidos
# (sem exigir mistura nem lista de senhas comuns).
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'common.password_validators.SenhaSistemaPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'config.pagination.ApiPageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'App OS API',
    'DESCRIPTION': 'Orçamentos, clientes e multi-empresa. Autenticação por sessão (cookie + CSRF).',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# CORS / CSRF: se CORS_ALLOWED_ORIGINS (ou CSRF_TRUSTED_ORIGINS) estiver definido no .env,
# usa essa lista + extras; senão mantém defaults de desenvolvimento + *_EXTRA.
_DEFAULT_CORS = [
    'http://localhost',
    'http://localhost:3000',
    'http://localhost:8000',
    'http://127.0.0.1',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:8000',
]
_cors_main = _csv_env('CORS_ALLOWED_ORIGINS')
_cors_extra = _csv_env('CORS_ALLOWED_ORIGINS_EXTRA')
CORS_ALLOWED_ORIGINS = (_cors_main + _cors_extra) if _cors_main else (_DEFAULT_CORS + _cors_extra)

CORS_ALLOW_CREDENTIALS = True

_csrf_main = _csv_env('CSRF_TRUSTED_ORIGINS')
_csrf_extra = _csv_env('CSRF_TRUSTED_ORIGINS_EXTRA')
CSRF_TRUSTED_ORIGINS = (_csrf_main + _csrf_extra) if _csrf_main else (_DEFAULT_CORS + _csrf_extra)

# Cookies de sessão (login por sessão). SameSite=None exige Secure — ver USE_TLS.
SESSION_COOKIE_HTTPONLY = True
_samesite = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax').strip()
if _samesite not in ('Lax', 'Strict', 'None'):
    _samesite = 'Lax'
SESSION_COOKIE_SAMESITE = _samesite
_csrf_samesite_raw = os.getenv('CSRF_COOKIE_SAMESITE', '').strip()
CSRF_COOKIE_SAMESITE = (
    _csrf_samesite_raw
    if _csrf_samesite_raw in ('Lax', 'Strict', 'None')
    else SESSION_COOKIE_SAMESITE
)

if not DEBUG and SESSION_COOKIE_SAMESITE == 'None' and not USE_TLS:
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured(
        'SESSION_COOKIE_SAMESITE=None exige USE_TLS=True (cookies Secure) em produção.'
    )

# Detrás de Nginx / load balancer que envia X-Forwarded-Proto (recomendado em produção)
if os.getenv('BEHIND_REVERSE_PROXY', 'False') == 'True':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Hardening HTTPS: ative só quando a API é servida **só** por HTTPS (USE_TLS=True)
if not DEBUG and USE_TLS:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'
    X_FRAME_OPTIONS = 'DENY'

# Logs: texto com request_id ou JSON (LOG_JSON=True) para agregadores / cloud
LOG_JSON = os.getenv('LOG_JSON', 'False') == 'True'
LOGGING = build_logging_dict(use_json=LOG_JSON)

# Opcional: erros em tempo real — `pip install sentry-sdk` quando usar SENTRY_DSN
_SENTRY_DSN = os.getenv('SENTRY_DSN', '').strip()
if _SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration

        sentry_sdk.init(
            dsn=_SENTRY_DSN,
            integrations=[DjangoIntegration()],
            traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0')),
            send_default_pii=False,
        )
    except ImportError:
        warnings.warn(
            'SENTRY_DSN definido mas sentry-sdk não está instalado (pip install sentry-sdk).',
            ImportWarning,
            stacklevel=1,
        )

