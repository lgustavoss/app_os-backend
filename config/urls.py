"""
URL configuration for app_os project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path
from django.views.static import serve
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from config.api_urls import urlpatterns as api_v1_urlpatterns
from config.health_views import HealthLiveView, HealthReadyView

urlpatterns = [
    path('health/', HealthLiveView.as_view(), name='health-live'),
    path('health/ready/', HealthReadyView.as_view(), name='health-ready'),
]

# OpenAPI / Swagger — só em DEBUG ou com API_DOCS_ENABLED=True.
if settings.DEBUG or getattr(settings, 'API_DOCS_ENABLED', False):
    urlpatterns += [
        path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
        path(
            'api/v1/docs/',
            SpectacularSwaggerView.as_view(url_name='schema'),
            name='swagger-ui',
        ),
        path(
            'api/v1/redoc/',
            SpectacularRedocView.as_view(url_name='schema'),
            name='redoc',
        ),
    ]

urlpatterns += [
    path('api/v1/', include(api_v1_urlpatterns)),
    # Legado: mantém o mesmo conjunto de rotas em /api/ para clientes antigos.
    path('api/', include(api_v1_urlpatterns)),
]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif getattr(settings, 'SERVE_MEDIA_VIA_DJANGO', False):
    urlpatterns += [
        re_path(
            r'^media/(?P<path>.*)$',
            serve,
            {'document_root': settings.MEDIA_ROOT},
        ),
    ]
