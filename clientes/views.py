from decimal import Decimal

from django.db.models import CharField, Count, F, Func, Q, Sum
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from autenticacao.permissions_modulos import (
    ClienteModulePermission,
    _perfil,
    usuario_eh_staff,
)
from configuracoes.models import ConfiguracaoEmpresa
from ordens_servico.models import Orcamento, StatusOrcamento

from .models import Cliente
from .serializers import ClienteCreateSerializer, ClienteSerializer
from .services import consultar_cnpj_sefaz


def _empresa_nome_curto(empresa: ConfiguracaoEmpresa | None) -> str:
    if not empresa:
        return '—'
    menu = (empresa.nome_exibicao_menu or '').strip()
    if menu:
        return menu
    nf = (empresa.nome_fantasia or '').strip()
    if nf:
        return nf
    return (empresa.razao_social or '').strip() or '—'


def _decimal_str(v) -> str:
    if v is None:
        return '0.00'
    return f"{Decimal(str(v)):.2f}"


class ClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar Clientes.
    
    list: Lista todos os clientes
    retrieve: Retorna detalhes de um cliente
    create: Cria um novo cliente
    update: Atualiza um cliente
    partial_update: Atualiza parcialmente um cliente
    destroy: Remove um cliente
    """
    permission_classes = [IsAuthenticated, ClienteModulePermission]
    queryset = Cliente.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ClienteCreateSerializer
        return ClienteSerializer
    
    def create(self, request, *args, **kwargs):
        """Cria cliente e retorna serializer completo"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Retornar serializer completo após criação
        output_serializer = ClienteSerializer(serializer.instance, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    def perform_create(self, serializer):
        """Salva o cliente com o usuário de cadastro"""
        serializer.save(usuario_cadastro=self.request.user)
    
    def perform_update(self, serializer):
        """Atualiza o cliente com o usuário da última alteração"""
        serializer.save(usuario_ultima_alteracao=self.request.user)
    
    def get_queryset(self):
        """Retorna apenas clientes ativos por padrão"""
        queryset = Cliente.objects.filter(ativo=True)
        search = self.request.query_params.get('search', '').strip()
        cnpj_cpf = self.request.query_params.get('cnpj_cpf', None)
        razao_social = self.request.query_params.get('razao_social', None)
        incluir_inativos = self.request.query_params.get('incluir_inativos', None)
        
        # Se solicitado, incluir clientes inativos
        if incluir_inativos == 'true':
            queryset = Cliente.objects.all()
        
        if search:
            # Busca por razão social OU CNPJ/CPF (apenas dígitos do termo para CNPJ/CPF)
            digitos = ''.join(c for c in search if c.isdigit())
            if digitos:
                # CNPJ/CPF pode estar armazenado com ou sem formatação; busca pelos dígitos
                queryset = queryset.annotate(
                    cnpj_cpf_apenas_digitos=Func(
                        F('cnpj_cpf'),
                        template="regexp_replace(%(expressions)s, '[^0-9]', '', 'g')",
                        output_field=CharField(),
                    )
                )
                queryset = queryset.filter(
                    Q(razao_social__icontains=search)
                    | Q(cnpj_cpf_apenas_digitos__icontains=digitos)
                )
            else:
                queryset = queryset.filter(razao_social__icontains=search)
        else:
            if cnpj_cpf:
                queryset = queryset.filter(cnpj_cpf__icontains=cnpj_cpf)
            if razao_social:
                queryset = queryset.filter(razao_social__icontains=razao_social)
        
        return queryset
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete: marca o cliente como inativo ao invés de deletar"""
        instance = self.get_object()
        instance.ativo = False
        instance.usuario_ultima_alteracao = request.user
        instance.save()
        return Response(
            {'mensagem': 'Cliente marcado como inativo com sucesso'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def consultar_cnpj(self, request):
        """
        Consulta dados de CNPJ na SEFAZ e retorna os dados para preenchimento.
        
        Parâmetros:
        - cnpj: CNPJ a ser consultado (apenas números)
        
        Retorna os dados da empresa encontrados na SEFAZ.
        """
        cnpj = request.query_params.get('cnpj', None)
        
        if not cnpj:
            return Response(
                {'erro': 'Parâmetro CNPJ é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove caracteres não numéricos
        cnpj = ''.join(filter(str.isdigit, cnpj))
        
        if len(cnpj) != 14:
            return Response(
                {'erro': 'CNPJ deve conter 14 dígitos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            dados = consultar_cnpj_sefaz(cnpj)
            return Response(dados, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'erro': f'Erro ao consultar CNPJ: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='resumo-orcamentos')
    def resumo_orcamentos(self, request, pk=None):
        """
        Agregados de orçamentos do cliente (todas as empresas), para o ecrã de detalhe.
        Exige permissão de visualizar orçamentos (alinhado à listagem na mesma página).
        """
        cliente = self.get_object()
        user = request.user
        if not usuario_eh_staff(user):
            perfil = _perfil(user)
            if not perfil or not perfil.orcamentos_pode_visualizar:
                return Response(
                    {'detail': 'Sem permissão para visualizar resumo de orçamentos.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        base = Orcamento.objects.filter(cliente_id=cliente.pk)

        totais = base.aggregate(
            quantidade=Count('id'),
            valor=Sum('valor_total'),
        )
        ativos = base.filter(ativo=True).aggregate(
            quantidade=Count('id'),
            valor=Sum('valor_total'),
        )
        excl = base.filter(ativo=False).aggregate(
            quantidade=Count('id'),
            valor=Sum('valor_total'),
        )

        agg_emp = (
            base.values('empresa_id')
            .annotate(quantidade=Count('id'), valor_total=Sum('valor_total'))
            .order_by('-valor_total', 'empresa_id')
        )
        emp_ids = [r['empresa_id'] for r in agg_emp if r['empresa_id']]
        empresas = {
            e.id: e
            for e in ConfiguracaoEmpresa.objects.filter(pk__in=emp_ids)
        }
        por_empresa = []
        for row in agg_emp:
            eid = row['empresa_id']
            emp = empresas.get(eid)
            por_empresa.append(
                {
                    'empresa_id': eid,
                    'empresa_nome': _empresa_nome_curto(emp),
                    'quantidade': row['quantidade'],
                    'valor_total': _decimal_str(row['valor_total']),
                }
            )

        agg_st = base.values('status_id').annotate(
            quantidade=Count('id'), valor_total=Sum('valor_total')
        )
        status_rows = list(
            StatusOrcamento.objects.order_by('ordem', 'id').values('id', 'nome')
        )
        ordem = [r['id'] for r in status_rows]
        labels = {r['id']: r['nome'] for r in status_rows}

        def _ord_status(sid):
            if sid is None:
                return len(ordem) + 1
            try:
                return ordem.index(sid)
            except ValueError:
                return len(ordem)

        por_status = sorted(agg_st, key=lambda r: _ord_status(r['status_id']))
        por_status_out = [
            {
                'status': r['status_id'],
                'status_label': (
                    labels.get(r['status_id'], '—')
                    if r['status_id'] is not None
                    else '—'
                ),
                'quantidade': r['quantidade'],
                'valor_total': _decimal_str(r['valor_total']),
            }
            for r in por_status
        ]

        return Response(
            {
                'total_quantidade': totais['quantidade'] or 0,
                'valor_total_geral': _decimal_str(totais['valor']),
                'ativos': {
                    'quantidade': ativos['quantidade'] or 0,
                    'valor_total': _decimal_str(ativos['valor']),
                },
                'excluidos': {
                    'quantidade': excl['quantidade'] or 0,
                    'valor_total': _decimal_str(excl['valor']),
                },
                'por_empresa': por_empresa,
                'por_status': por_status_out,
            }
        )

