from decimal import Decimal

from django.db import transaction

from .models import EstoqueProdutoEmpresa, MovimentacaoEstoque, Produto


class EstoqueError(Exception):
    pass


@transaction.atomic
def movimentar_estoque(
    *,
    empresa,
    produto_id: int,
    tipo: str,
    quantidade: Decimal,
    usuario=None,
    observacao: str | None = None,
    origem: str = MovimentacaoEstoque.Origem.MANUAL,
    orcamento=None,
    status_orcamento=None,
):
    if quantidade is None:
        raise EstoqueError('Quantidade é obrigatória.')
    quantidade = Decimal(str(quantidade))
    if quantidade <= 0:
        raise EstoqueError('Quantidade deve ser maior que zero.')

    produto = Produto.objects.get(pk=produto_id)
    estoque, _ = EstoqueProdutoEmpresa.objects.select_for_update().get_or_create(
        empresa=empresa,
        produto=produto,
        defaults={'saldo': Decimal('0')},
    )
    saldo_anterior = Decimal(str(estoque.saldo))

    if tipo == MovimentacaoEstoque.Tipo.ENTRADA:
        delta = quantidade
    elif tipo == MovimentacaoEstoque.Tipo.SAIDA:
        delta = -quantidade
    elif tipo == MovimentacaoEstoque.Tipo.AJUSTE:
        delta = quantidade - saldo_anterior
    else:
        raise EstoqueError('Tipo de movimentação inválido.')

    saldo_posterior = saldo_anterior + delta
    if saldo_posterior < 0:
        raise EstoqueError(
            f'Estoque insuficiente para o produto #{produto.pk} ({produto.descricao}). '
            f'Saldo atual: {saldo_anterior}.'
        )

    estoque.saldo = saldo_posterior
    estoque.save(update_fields=['saldo', 'data_atualizacao'])

    mov = MovimentacaoEstoque.objects.create(
        produto=produto,
        empresa=empresa,
        tipo=tipo,
        origem=origem,
        quantidade=quantidade,
        saldo_anterior=saldo_anterior,
        saldo_posterior=Decimal(str(estoque.saldo)),
        observacao=(observacao or '').strip() or None,
        orcamento=orcamento,
        status_orcamento=status_orcamento,
        usuario=usuario,
    )
    return mov

