from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConfiguracaoEmpresaViewSet

router = DefaultRouter()
router.register(r'configuracoes-empresa', ConfiguracaoEmpresaViewSet, basename='configuracoes-empresa')

urlpatterns = [
    path('', include(router.urls)),
]

