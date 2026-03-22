"""
Permissões por módulo (não-staff). Staff ignora e tem acesso total.
"""
from rest_framework.permissions import BasePermission

from autenticacao.models import PerfilUsuario


def _perfil(user):
    """Retorna o perfil ou None (inclui usuário sem linha em PerfilUsuario)."""
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    try:
        return user.perfil
    except PerfilUsuario.DoesNotExist:
        return None


def usuario_eh_staff(user) -> bool:
    return bool(user and user.is_authenticated and getattr(user, 'is_staff', False))


class ClienteModulePermission(BasePermission):
    """list/retrieve + consultar_cnpj: visualizar | create/update/delete: cadastrar"""

    message = 'Sem permissão para acessar o módulo de clientes.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if usuario_eh_staff(request.user):
            return True
        p = _perfil(request.user)
        if not p:
            return False
        action = getattr(view, 'action', None)
        if action in ('list', 'retrieve'):
            return p.clientes_pode_visualizar
        if action in ('create', 'update', 'partial_update', 'destroy'):
            return p.clientes_pode_cadastrar
        if action == 'consultar_cnpj':
            return p.clientes_pode_cadastrar
        if action == 'resumo_orcamentos':
            return p.clientes_pode_visualizar
        return False


class OrcamentoModulePermission(BasePermission):
    """list/retrieve/gerar_pdf: visualizar | demais mutações: cadastrar"""

    message = 'Sem permissão para acessar orçamentos.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if usuario_eh_staff(request.user):
            return True
        p = _perfil(request.user)
        if not p:
            return False
        action = getattr(view, 'action', None)
        if action in ('list', 'retrieve', 'gerar_pdf'):
            return p.orcamentos_pode_visualizar
        if action in (
            'create',
            'update',
            'partial_update',
            'destroy',
            'adicionar_item',
            'atualizar_status',
        ):
            return p.orcamentos_pode_cadastrar
        return False


class StatusOrcamentoPermission(BasePermission):
    """
    CRUD de status de orçamentos: mesmo critério de configurações
    (visualizar lista / configurar para criar-editar-excluir).
    """

    message = 'Sem permissão para gerenciar status de orçamentos.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if usuario_eh_staff(request.user):
            return True
        p = _perfil(request.user)
        if not p:
            return False
        action = getattr(view, 'action', None)
        if action in ('list', 'retrieve'):
            return p.configuracoes_pode_visualizar
        if action in ('create', 'update', 'partial_update', 'destroy'):
            return p.configuracoes_pode_configurar
        return False


class ConfiguracaoModulePermission(BasePermission):
    """list/retrieve/atual: visualizar | create/update/delete: configurar"""

    message = 'Sem permissão para configurações / empresas.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if usuario_eh_staff(request.user):
            return True
        p = _perfil(request.user)
        if not p:
            return False
        action = getattr(view, 'action', None)
        if action in ('list', 'retrieve', 'atual'):
            return p.configuracoes_pode_visualizar
        if action in ('create', 'update', 'partial_update', 'destroy'):
            return p.configuracoes_pode_configurar
        return False
