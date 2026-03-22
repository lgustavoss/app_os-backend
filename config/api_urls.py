"""
Rotas versionadas da API REST (v1). Incluídas também em /api/ para compatibilidade.
"""
from django.urls import include, path

urlpatterns = [
    path('', include('autenticacao.urls')),
    path('', include('dashboard.urls')),
    path('', include('configuracoes.urls')),
    path('', include('clientes.urls')),
    path('', include('ordens_servico.urls')),
]
