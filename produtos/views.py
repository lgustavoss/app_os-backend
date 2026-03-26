from django.db.models import Q
from django.db.models.deletion import ProtectedError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from autenticacao.permissions_modulos import ProdutoModulePermission
from autenticacao.views import get_empresa_atual
from .models import EstoqueProdutoEmpresa, MovimentacaoEstoque, Produto
from .serializers import (
    MovimentacaoEstoqueInputSerializer,
    MovimentacaoEstoqueSerializer,
    ProdutoSerializer,
)
from .services import EstoqueError, movimentar_estoque


class ProdutoViewSet(viewsets.ModelViewSet):
    """CRUD de produtos do catálogo global."""

    permission_classes = [IsAuthenticated, ProdutoModulePermission]
    serializer_class = ProdutoSerializer
    queryset = Produto.objects.all().order_by('codigo')
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['empresa_atual'] = get_empresa_atual(self.request)
        return ctx

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {
                    'erro': 'Não é possível excluir: existem itens de orçamento vinculados a este produto.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def get_queryset(self):
        qs = super().get_queryset()
        q = (self.request.query_params.get('search') or '').strip()
        if q:
            if q.isdigit():
                cod = int(q)
                qs = qs.filter(Q(descricao__icontains=q) | Q(codigo=cod))
            else:
                qs = qs.filter(descricao__icontains=q)
        return qs

    def perform_update(self, serializer):
        empresa = get_empresa_atual(self.request)
        if not empresa:
            from rest_framework import serializers as drf_serializers
            raise drf_serializers.ValidationError({'erro': 'Nenhuma empresa ativa selecionada.'})

        instance = serializer.instance
        saldo_novo = serializer.validated_data.pop('saldo_estoque', None)
        saldo_antigo = (
            EstoqueProdutoEmpresa.objects.filter(empresa=empresa, produto=instance)
            .values_list('saldo', flat=True)
            .first()
        )
        if saldo_antigo is None:
            saldo_antigo = 0
        produto = serializer.save()
        if saldo_novo is not None:
            if saldo_novo != saldo_antigo:
                movimentar_estoque(
                    empresa=empresa,
                    produto_id=produto.pk,
                    tipo=MovimentacaoEstoque.Tipo.AJUSTE,
                    quantidade=saldo_novo,
                    usuario=self.request.user,
                    observacao='Ajuste direto no cadastro do produto.',
                    origem=MovimentacaoEstoque.Origem.MANUAL,
                )

    def perform_create(self, serializer):
        empresa = get_empresa_atual(self.request)
        if not empresa:
            from rest_framework import serializers as drf_serializers
            raise drf_serializers.ValidationError({'erro': 'Nenhuma empresa ativa selecionada.'})
        saldo_inicial = serializer.validated_data.pop('saldo_estoque', 0)
        produto = serializer.save()
        if saldo_inicial and saldo_inicial > 0:
            movimentar_estoque(
                empresa=empresa,
                produto_id=produto.pk,
                tipo=MovimentacaoEstoque.Tipo.AJUSTE,
                quantidade=saldo_inicial,
                usuario=self.request.user,
                observacao='Saldo inicial definido no cadastro do produto.',
                origem=MovimentacaoEstoque.Origem.MANUAL,
            )

    @action(detail=True, methods=['post'])
    def movimentar_estoque(self, request, pk=None):
        empresa = get_empresa_atual(request)
        if not empresa:
            return Response({'erro': 'Nenhuma empresa ativa selecionada.'}, status=status.HTTP_400_BAD_REQUEST)
        produto = self.get_object()
        serializer = MovimentacaoEstoqueInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            mov = movimentar_estoque(
                empresa=empresa,
                produto_id=produto.pk,
                tipo=data['tipo'],
                quantidade=data['quantidade'],
                usuario=request.user,
                observacao=data.get('observacao'),
                origem=MovimentacaoEstoque.Origem.MANUAL,
            )
        except EstoqueError as e:
            return Response({'erro': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(MovimentacaoEstoqueSerializer(mov).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def movimentacoes(self, request, pk=None):
        empresa = get_empresa_atual(request)
        if not empresa:
            return Response([])
        produto = self.get_object()
        qs = produto.movimentacoes_estoque.select_related(
            'orcamento', 'usuario', 'status_orcamento'
        ).filter(empresa=empresa)
        return Response(MovimentacaoEstoqueSerializer(qs, many=True).data)
