from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from autenticacao.permissions_modulos import ConfiguracaoModulePermission
from autenticacao.views import get_empresa_atual
from .models import ConfiguracaoEmpresa
from .serializers import ConfiguracaoEmpresaSerializer


class ConfiguracaoEmpresaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar as configurações das empresas (multi-empresa).
    list: lista todas as empresas
    retrieve: detalhe de uma empresa
    create: cria nova empresa
    update/partial_update: atualiza uma empresa
    destroy: remove uma empresa (se não houver orçamentos vinculados)
    atual: GET retorna a configuração da empresa atual do usuário
    """
    permission_classes = [IsAuthenticated, ConfiguracaoModulePermission]
    serializer_class = ConfiguracaoEmpresaSerializer
    queryset = ConfiguracaoEmpresa.objects.all().order_by('razao_social')

    @action(detail=False, methods=['get'], url_path='atual')
    def atual(self, request):
        """Retorna a configuração da empresa atual do usuário (para a tela de configurações)."""
        empresa = get_empresa_atual(request)
        if not empresa:
            return Response(
                {'erro': 'Nenhuma empresa selecionada. Selecione uma empresa no menu.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(empresa, context={'request': request})
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        from ordens_servico.models import Orcamento
        instance = self.get_object()
        if Orcamento.objects.filter(empresa=instance).exists():
            return Response(
                {'erro': 'Não é possível excluir esta empresa pois existem orçamentos vinculados a ela.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

