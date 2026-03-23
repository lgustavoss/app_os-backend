"""
URL configuration for app_os project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.http import Http404
from django.urls import include, path, re_path
from django.views.static import serve
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from config.api_urls import urlpatterns as api_v1_urlpatterns
from config.health_views import HealthLiveView, HealthReadyView


def _api_docs_allowed() -> bool:
    return settings.DEBUG or getattr(settings, 'API_DOCS_ENABLED', False)


class _DocsGateMixin:
    """404 em produção sem API_DOCS_ENABLED — avaliado em tempo de pedido (tests com override_settings)."""

    def dispatch(self, request, *args, **kwargs):
        if not _api_docs_allowed():
            raise Http404()
        return super().dispatch(request, *args, **kwargs)


class SpectacularAPIViewGated(_DocsGateMixin, SpectacularAPIView):
    pass


class SpectacularSwaggerViewGated(_DocsGateMixin, SpectacularSwaggerView):
    pass


class SpectacularRedocViewGated(_DocsGateMixin, SpectacularRedocView):
    pass


urlpatterns = [
    path('health/', HealthLiveView.as_view(), name='health-live'),
    path('health/ready/', HealthReadyView.as_view(), name='health-ready'),
    path('api/v1/schema/', SpectacularAPIViewGated.as_view(), name='schema'),
    path(
        'api/v1/docs/',
        SpectacularSwaggerViewGated.as_view(url_name='schema'),
        name='swagger-ui',
    ),
    path(
        'api/v1/redoc/',
        SpectacularRedocViewGated.as_view(url_name='schema'),
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
