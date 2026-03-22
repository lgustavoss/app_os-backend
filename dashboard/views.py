from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from autenticacao.views import get_empresa_atual
from clientes.models import Cliente
from ordens_servico.models import Orcamento
from ordens_servico.serializers import OrcamentoSerializer


class DashboardResumoView(APIView):
    """
    Retorna os dados do Dashboard filtrados pela empresa atual do usuário.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        empresa = get_empresa_atual(request)
        if not empresa:
            return Response({
                'total_orcamentos': 0,
                'total_clientes': 0,
                'orcamentos_recentes': [],
            })
        orcamentos_ativos = Orcamento.objects.filter(empresa=empresa, ativo=True)
        total_orcamentos = orcamentos_ativos.count()
        total_clientes = Cliente.objects.filter(ativo=True).count()
        orcamentos_recentes = (
            orcamentos_ativos.select_related('cliente', 'empresa', 'status')[:10]
        )

        serializer = OrcamentoSerializer(
            orcamentos_recentes,
            many=True,
            context={'request': request}
        )

        return Response({
            'total_orcamentos': total_orcamentos,
            'total_clientes': total_clientes,
            'orcamentos_recentes': serializer.data,
        })
