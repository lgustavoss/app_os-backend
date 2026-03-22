from django.db.models import Prefetch
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from autenticacao.permissions_modulos import OrcamentoModulePermission, StatusOrcamentoPermission
from autenticacao.views import get_empresa_atual
from .models import HistoricoStatusOrcamento, Orcamento, ItemOrcamento, StatusOrcamento
from .serializers import (
    OrcamentoSerializer,
    OrcamentoCreateSerializer,
    ItemOrcamentoSerializer,
    StatusOrcamentoSerializer,
)
from .search import build_orcamento_search_q
from .services import gerar_pdf_orcamento


class OrcamentoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar Orçamentos (filtrados pela empresa atual do usuário).
    """
    permission_classes = [IsAuthenticated, OrcamentoModulePermission]
    queryset = Orcamento.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return OrcamentoCreateSerializer
        return OrcamentoSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['for_detail'] = self.action == 'retrieve'
        return ctx

    def get_queryset(self):
        """
        - list: por defeito só empresa atual; com cliente + todas_empresas, todos os orçamentos
          desse cliente (ex.: ecrã detalhe do cliente).
        - retrieve / gerar_pdf: qualquer orçamento (permissão = módulo); retrieve pré-carrega histórico
          de status; PDF não.
        - mutações na empresa atual: update/destroy sem filtro ativo; adicionar_item / atualizar_status
          só orçamentos ativos.
        """
        qs = Orcamento.objects.select_related('empresa', 'cliente', 'status')
        action = self.action
        empresa = get_empresa_atual(self.request)

        if action == 'retrieve':
            return qs.prefetch_related(
                Prefetch(
                    'itens',
                    queryset=ItemOrcamento.objects.select_related('produto'),
                ),
                Prefetch(
                    'historicos_status',
                    queryset=HistoricoStatusOrcamento.objects.select_related(
                        'usuario', 'status_anterior', 'status_novo'
                    ).order_by('data_registro', 'id'),
                ),
            )

        if action == 'gerar_pdf':
            return qs

        if action == 'list':
            cliente_param = self.request.query_params.get('cliente')
            todas_empresas = str(
                self.request.query_params.get('todas_empresas', '')
            ).lower() in ('1', 'true', 'yes')
            if todas_empresas and cliente_param is not None:
                try:
                    cid = int(cliente_param)
                except (TypeError, ValueError):
                    cid = None
                if cid is not None:
                    base = qs.filter(cliente_id=cid)
                    incluir_excluidos = self.request.query_params.get(
                        'incluir_excluidos', None
                    )
                    excluidos_apenas = self.request.query_params.get(
                        'excluidos_apenas', None
                    )
                    if excluidos_apenas == 'true':
                        base = base.filter(ativo=False)
                    elif incluir_excluidos == 'true':
                        pass
                    else:
                        base = base.filter(ativo=True)
                    status_filter = self.request.query_params.get('status', None)
                    if status_filter is not None and status_filter != '':
                        try:
                            base = base.filter(status_id=int(status_filter))
                        except (TypeError, ValueError):
                            base = base.none()
                    search = self.request.query_params.get('search', '').strip()
                    if search:
                        base = base.filter(build_orcamento_search_q(search)).distinct()
                    return base

        if not empresa:
            return Orcamento.objects.none()

        base = qs.filter(empresa=empresa)

        if action == 'list':
            base = base.filter(ativo=True)
            incluir_excluidos = self.request.query_params.get('incluir_excluidos', None)
            excluidos_apenas = self.request.query_params.get('excluidos_apenas', None)
            if excluidos_apenas == 'true':
                base = Orcamento.objects.filter(empresa=empresa, ativo=False)
            elif incluir_excluidos == 'true':
                base = Orcamento.objects.filter(empresa=empresa)
            status_filter = self.request.query_params.get('status', None)
            if status_filter is not None and status_filter != '':
                try:
                    base = base.filter(status_id=int(status_filter))
                except (TypeError, ValueError):
                    base = base.none()
            cliente_id = self.request.query_params.get('cliente', None)
            if cliente_id:
                base = base.filter(cliente_id=cliente_id)
            search = self.request.query_params.get('search', '').strip()
            if search:
                base = base.filter(build_orcamento_search_q(search)).distinct()
            return base

        if action in ('adicionar_item', 'atualizar_status'):
            return base.filter(ativo=True)

        return base

    def create(self, request, *args, **kwargs):
        """Cria orçamento na empresa atual do usuário."""
        empresa = get_empresa_atual(request)
        if not empresa:
            return Response(
                {'erro': 'Nenhuma empresa selecionada. Defina a empresa atual no perfil.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        orcamento = serializer.save(
            usuario_criacao=request.user,
            empresa=empresa,
        )
        HistoricoStatusOrcamento.objects.create(
            orcamento=orcamento,
            usuario=request.user,
            status_anterior=None,
            status_novo_id=orcamento.status_id,
            origem=HistoricoStatusOrcamento.Origem.CRIACAO,
        )
        ctx = super().get_serializer_context()
        ctx['for_detail'] = True
        output_serializer = OrcamentoSerializer(orcamento, context=ctx)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        """Atualiza orçamento, auditoria e recalcula valor total"""
        old_status_id = serializer.instance.status_id
        orcamento = serializer.save(usuario_ultima_alteracao=self.request.user)
        if orcamento.status_id != old_status_id:
            HistoricoStatusOrcamento.objects.create(
                orcamento=orcamento,
                usuario=self.request.user,
                status_anterior_id=old_status_id,
                status_novo_id=orcamento.status_id,
                origem=HistoricoStatusOrcamento.Origem.EDICAO,
            )
        orcamento.calcular_valor_total()

    def destroy(self, request, *args, **kwargs):
        """Soft delete: marca o orçamento como inativo ao invés de deletar"""
        instance = self.get_object()
        instance.ativo = False
        instance.usuario_ultima_alteracao = request.user
        instance.data_ultima_alteracao = timezone.now()
        instance.save(update_fields=['ativo', 'usuario_ultima_alteracao', 'data_ultima_alteracao'])
        return Response(
            {'mensagem': 'Orçamento marcado como excluído com sucesso'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def adicionar_item(self, request, pk=None):
        """Adiciona um item (peça ou serviço) ao orçamento"""
        orcamento = self.get_object()
        serializer = ItemOrcamentoSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(orcamento=orcamento)
            orcamento.usuario_ultima_alteracao = request.user
            orcamento.data_ultima_alteracao = timezone.now()
            orcamento.save(
                update_fields=['usuario_ultima_alteracao', 'data_ultima_alteracao']
            )
            orcamento.calcular_valor_total()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'])
    def atualizar_status(self, request, pk=None):
        """Atualiza o status de um orçamento"""
        orcamento = self.get_object()
        if 'status' not in request.data:
            return Response(
                {'erro': 'Informe o status do orçamento (id numérico).'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        raw = request.data.get('status')
        if raw is None:
            return Response(
                {'erro': 'O status do orçamento é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            status_id = int(raw)
        except (TypeError, ValueError):
            return Response(
                {'erro': 'Status inválido'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        st = StatusOrcamento.objects.filter(pk=status_id, ativo=True).first()
        if not st:
            return Response(
                {'erro': 'Status inválido ou inativo'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        old_status_id = orcamento.status_id
        if old_status_id == st.pk:
            serializer = self.get_serializer(orcamento)
            return Response(serializer.data)

        orcamento.status = st
        orcamento.usuario_ultima_alteracao = request.user
        orcamento.data_ultima_alteracao = timezone.now()
        orcamento.save(
            update_fields=['status_id', 'usuario_ultima_alteracao', 'data_ultima_alteracao']
        )
        HistoricoStatusOrcamento.objects.create(
            orcamento=orcamento,
            usuario=request.user,
            status_anterior_id=old_status_id,
            status_novo=st,
            origem=HistoricoStatusOrcamento.Origem.ATUALIZAR_STATUS,
        )

        serializer = self.get_serializer(orcamento)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def gerar_pdf(self, request, pk=None):
        """
        Gera um PDF do orçamento.
        
        Retorna um arquivo PDF com todas as informações do orçamento,
        incluindo dados do cliente, descrição dos serviços,
        itens (peças e serviços) e valor total.
        """
        orcamento = self.get_object()
        return gerar_pdf_orcamento(orcamento)


class StatusOrcamentoViewSet(viewsets.ModelViewSet):
    """Cadastro de status de orçamentos (configurações)."""

    permission_classes = [IsAuthenticated, StatusOrcamentoPermission]
    serializer_class = StatusOrcamentoSerializer
    queryset = StatusOrcamento.objects.all().order_by('ordem', 'id')
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        qs = super().get_queryset()
        ativo = self.request.query_params.get('ativo')
        if ativo is not None and str(ativo).lower() in ('1', 'true', 'yes'):
            qs = qs.filter(ativo=True)
        return qs

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if Orcamento.objects.filter(status=instance).exists():
            return Response(
                {
                    'erro': 'Não é possível excluir: existem orçamentos com este status. '
                    'Desative o status ou altere os orçamentos antes.'
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)


class ItemOrcamentoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar Itens de Orçamento (apenas da empresa atual).
    """
    permission_classes = [IsAuthenticated, OrcamentoModulePermission]
    serializer_class = ItemOrcamentoSerializer
    queryset = ItemOrcamento.objects.all()

    def get_queryset(self):
        empresa = get_empresa_atual(self.request)
        if not empresa:
            return ItemOrcamento.objects.none()
        return ItemOrcamento.objects.filter(orcamento__empresa=empresa).select_related(
            'orcamento', 'produto'
        )

    def _recalcular_orcamento(self, orcamento, user):
        """Recalcula o valor total e registra quem alterou o orçamento (via itens)."""
        orcamento.usuario_ultima_alteracao = user
        orcamento.data_ultima_alteracao = timezone.now()
        orcamento.save(
            update_fields=['usuario_ultima_alteracao', 'data_ultima_alteracao']
        )
        orcamento.calcular_valor_total()

    def perform_create(self, serializer):
        item = serializer.save()
        self._recalcular_orcamento(item.orcamento, self.request.user)

    def perform_update(self, serializer):
        item = serializer.save()
        self._recalcular_orcamento(item.orcamento, self.request.user)

    def perform_destroy(self, instance):
        orcamento = instance.orcamento
        user = self.request.user
        instance.delete()
        self._recalcular_orcamento(orcamento, user)
