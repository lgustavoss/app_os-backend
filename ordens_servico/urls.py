from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrcamentoViewSet, ItemOrcamentoViewSet, StatusOrcamentoViewSet

router = DefaultRouter()
router.register(r'orcamentos', OrcamentoViewSet, basename='orcamento')
router.register(r'itens-orcamento', ItemOrcamentoViewSet, basename='item-orcamento')
router.register(r'status-orcamentos', StatusOrcamentoViewSet, basename='status-orcamento')

urlpatterns = router.urls
