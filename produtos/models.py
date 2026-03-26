from django.db import models
from django.db.models import Max
from django.contrib.auth.models import User


class Produto(models.Model):
    """Catálogo global de produtos (mesmo código para todas as empresas)."""

    codigo = models.PositiveIntegerField(
        primary_key=True,
        editable=False,
        verbose_name='Código',
    )
    descricao = models.CharField(max_length=255, verbose_name='Descrição')
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Valor',
    )

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['codigo']

    def __str__(self):
        return f'{self.codigo} — {self.descricao}'

    @classmethod
    def proximo_codigo(cls) -> int:
        ultimo = cls.objects.aggregate(m=Max('codigo'))['m']
        return (ultimo or 0) + 1


class MovimentacaoEstoque(models.Model):
    class Tipo(models.TextChoices):
        ENTRADA = 'entrada', 'Entrada'
        SAIDA = 'saida', 'Saída'
        AJUSTE = 'ajuste', 'Ajuste'

    class Origem(models.TextChoices):
        MANUAL = 'manual', 'Manual'
        STATUS_ORCAMENTO = 'status_orcamento', 'Status de orçamento'

    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name='movimentacoes_estoque',
        verbose_name='Produto',
    )
    empresa = models.ForeignKey(
        'configuracoes.ConfiguracaoEmpresa',
        on_delete=models.PROTECT,
        related_name='movimentacoes_estoque_produtos',
        null=True,
        blank=True,
        verbose_name='Empresa',
    )
    tipo = models.CharField(max_length=20, choices=Tipo.choices, verbose_name='Tipo')
    origem = models.CharField(
        max_length=30,
        choices=Origem.choices,
        default=Origem.MANUAL,
        verbose_name='Origem',
    )
    quantidade = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='Quantidade')
    saldo_anterior = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='Saldo anterior')
    saldo_posterior = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='Saldo posterior')
    observacao = models.CharField(max_length=255, blank=True, null=True, verbose_name='Observação')
    orcamento = models.ForeignKey(
        'ordens_servico.Orcamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes_estoque',
        verbose_name='Orçamento vinculado',
    )
    status_orcamento = models.ForeignKey(
        'ordens_servico.StatusOrcamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes_estoque',
        verbose_name='Status que gerou a movimentação',
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes_estoque',
        verbose_name='Usuário',
    )
    data_registro = models.DateTimeField(auto_now_add=True, verbose_name='Data do registro')

    class Meta:
        verbose_name = 'Movimentação de estoque'
        verbose_name_plural = 'Movimentações de estoque'
        ordering = ['-data_registro', '-id']
        indexes = [
            models.Index(fields=['empresa', 'produto', 'data_registro']),
        ]

    def __str__(self):
        return f'{self.get_tipo_display()} {self.quantidade} | Empresa {self.empresa_id} Produto {self.produto_id}'


class EstoqueProdutoEmpresa(models.Model):
    empresa = models.ForeignKey(
        'configuracoes.ConfiguracaoEmpresa',
        on_delete=models.CASCADE,
        related_name='estoques_produtos',
        verbose_name='Empresa',
    )
    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name='saldos_por_empresa',
        verbose_name='Produto',
    )
    saldo = models.DecimalField(max_digits=12, decimal_places=3, default=0, verbose_name='Saldo')
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Data da atualização')

    class Meta:
        verbose_name = 'Estoque do produto por empresa'
        verbose_name_plural = 'Estoques dos produtos por empresa'
        constraints = [
            models.UniqueConstraint(
                fields=['empresa', 'produto'],
                name='produtos_estoque_empresa_produto_uniq',
            )
        ]

    def __str__(self):
        return f'Empresa {self.empresa_id} | Produto {self.produto_id} | Saldo {self.saldo}'
