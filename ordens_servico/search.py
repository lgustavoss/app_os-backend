"""Filtro OR para listagem de orçamentos (número, cliente, status, texto livre, itens)."""
from django.db.models import Q

from ordens_servico.models import StatusOrcamento


def build_orcamento_search_q(raw: str) -> Q:
    q = (raw or '').strip()
    if not q:
        return Q(pk__in=[])

    ql = q.lower()
    status_q = Q()
    for st in StatusOrcamento.objects.all():
        lab = (st.nome or '').lower()
        sid = str(st.pk)
        if ql == sid or ql in lab or lab.startswith(ql) or sid.startswith(ql):
            status_q |= Q(status_id=st.pk)

    client_q = (
        Q(cliente__razao_social__icontains=q)
        | Q(cliente__nome_fantasia__icontains=q)
        | Q(cliente__cnpj_cpf__icontains=q)
    )
    empresa_q = (
        Q(empresa__razao_social__icontains=q)
        | Q(empresa__nome_fantasia__icontains=q)
        | Q(empresa__nome_exibicao_menu__icontains=q)
        | Q(empresa__cnpj__icontains=q)
    )
    # Só cruza com CNPJ/CPF quando há sequência numérica longa o suficiente (evita
    # "001" extraído de "ORC-001" bater em documentos com esses dígitos).
    digits = ''.join(c for c in q if c.isdigit())
    if len(digits) >= 8:
        client_q |= Q(cliente__cnpj_cpf__icontains=digits)

    return (
        Q(numero__icontains=q)
        | Q(descricao__icontains=q)
        | Q(observacoes__icontains=q)
        | Q(condicoes_pagamento__icontains=q)
        | Q(prazo_entrega__icontains=q)
        | Q(itens__descricao__icontains=q)
        | client_q
        | empresa_q
        | status_q
    )
