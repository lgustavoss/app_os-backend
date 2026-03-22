"""Helpers para testes com multi-empresa e orçamentos."""
from configuracoes.models import ConfiguracaoEmpresa
from autenticacao.models import PerfilUsuario
from ordens_servico.models import StatusOrcamento


def criar_empresa(**kwargs):
    data = {
        'razao_social': 'Empresa Teste Ltda',
        'cnpj': '11222333000181',
        'endereco': 'Rua Teste 1',
        'cidade': 'São Paulo',
        'estado': 'SP',
        'cep': '01001000',
    }
    data.update(kwargs)
    return ConfiguracaoEmpresa.objects.create(**data)


def definir_empresa_atual(usuario, empresa):
    perfil, _ = PerfilUsuario.objects.get_or_create(user=usuario)
    perfil.empresa_atual = empresa
    perfil.save(update_fields=['empresa_atual'])
    usuario.__dict__.pop('perfil', None)


def criar_status(nome='Em análise', ordem=0, ativo=True):
    return StatusOrcamento.objects.create(nome=nome, ordem=ordem, ativo=ativo)
