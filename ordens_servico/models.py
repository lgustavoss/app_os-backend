from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Max


class StatusOrcamento(models.Model):
    """Status configuráveis para acompanhamento manual do andamento do orçamento."""

    nome = models.CharField(max_length=100, verbose_name='Nome exibido')
    ordem = models.PositiveSmallIntegerField(default=0, db_index=True)
    ativo = models.BooleanField(default=True, verbose_name='Ativo na seleção')
    movimenta_estoque_saida = models.BooleanField(
        default=False,
        verbose_name='Movimenta estoque (saída)',
        help_text='Quando marcado, ao selecionar este status o sistema registra saída de estoque dos itens de produto.',
    )

    class Meta:
        verbose_name = 'Status de orçamento'
        verbose_name_plural = 'Status de orçamentos'
        ordering = ['ordem', 'id']

    def __str__(self):
        return self.nome


class Orcamento(models.Model):
    """Modelo para representar um Orçamento"""

    TIPO_VALOR_CHOICES = [
        ('valor', 'Valor Fixo'),
        ('percentual', 'Percentual'),
    ]
    
    numero = models.CharField(max_length=20, verbose_name='Número do Orçamento', editable=False)
    empresa = models.ForeignKey(
        'configuracoes.ConfiguracaoEmpresa',
        on_delete=models.PROTECT,
        related_name='orcamentos',
        verbose_name='Empresa'
    )
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        related_name='orcamentos',
        verbose_name='Cliente'
    )
    descricao = models.TextField(
        verbose_name='Descrição dos Serviços',
        blank=True,
        null=True,
        help_text='Opcional - os itens já descrevem o orçamento'
    )
    status = models.ForeignKey(
        StatusOrcamento,
        on_delete=models.PROTECT,
        related_name='orcamentos',
        verbose_name='Status',
    )
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    data_validade = models.DateField(verbose_name='Data de Validade', null=True, blank=True)
    desconto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Desconto',
        help_text='Valor ou percentual conforme desconto_tipo'
    )
    desconto_tipo = models.CharField(
        max_length=10,
        choices=TIPO_VALOR_CHOICES,
        default='valor',
        verbose_name='Tipo de Desconto'
    )
    acrescimo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Acréscimo',
        help_text='Valor ou percentual conforme acrescimo_tipo'
    )
    acrescimo_tipo = models.CharField(
        max_length=10,
        choices=TIPO_VALOR_CHOICES,
        default='valor',
        verbose_name='Tipo de Acréscimo'
    )
    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name='Valor Total'
    )
    condicoes_pagamento = models.TextField(
        blank=True, 
        null=True, 
        verbose_name='Condições de Pagamento',
        help_text='Ex: À vista, parcelado, etc.'
    )
    prazo_entrega = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Prazo de Entrega/Execução',
        help_text='Ex: 15 dias, 1 mês, etc.'
    )
    observacoes = models.TextField(blank=True, null=True, verbose_name='Observações')
    usuario_criacao = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='orcamentos_criados',
        verbose_name='Usuário de Criação'
    )
    data_ultima_alteracao = models.DateTimeField(
        auto_now=True,
        verbose_name='Data da última alteração',
    )
    usuario_ultima_alteracao = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orcamentos_alterados',
        verbose_name='Último usuário a alterar',
    )
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        verbose_name = 'Orçamento'
        verbose_name_plural = 'Orçamentos'
        ordering = ['-data_criacao']
        constraints = [
            models.UniqueConstraint(
                fields=['empresa', 'numero'],
                name='ordens_servico_orcamento_empresa_numero_uniq'
            ),
        ]
    
    def __str__(self):
        return f"Orçamento {self.numero} - {self.cliente.razao_social if self.cliente else 'Sem Cliente'}"

    def get_subtotal(self):
        """Retorna a soma dos itens (antes de desconto/acréscimo)"""
        return sum((item.valor_total for item in self.itens.all()), Decimal('0'))

    def get_valor_desconto_calculado(self, subtotal=None):
        """Retorna o valor do desconto em moeda, conforme o tipo"""
        if subtotal is None:
            subtotal = self.get_subtotal()
        subtotal = Decimal(str(subtotal))
        desconto = Decimal(str(self.desconto))
        if self.desconto_tipo == 'percentual':
            return subtotal * (desconto / Decimal('100'))
        return desconto

    def get_valor_acrescimo_calculado(self, base=None):
        """Retorna o valor do acréscimo em moeda, conforme o tipo. Base = subtotal - desconto"""
        if base is None:
            base = self.get_subtotal() - self.get_valor_desconto_calculado()
        base = Decimal(str(base))
        acrescimo = Decimal(str(self.acrescimo))
        if self.acrescimo_tipo == 'percentual':
            return base * (acrescimo / Decimal('100'))
        return acrescimo

    def calcular_valor_total(self):
        """Calcula e atualiza o valor total do orçamento baseado nos itens e desconto/acréscimo"""
        subtotal = self.get_subtotal()
        valor_desconto = self.get_valor_desconto_calculado(subtotal)
        base_apos_desconto = subtotal - valor_desconto
        valor_acrescimo = self.get_valor_acrescimo_calculado(base_apos_desconto)
        self.valor_total = base_apos_desconto + valor_acrescimo
        self.save(update_fields=['valor_total'])
        return self.valor_total

    def esta_vencido(self):
        """Verifica se a data de validade já passou (independente do status)."""
        if not self.data_validade:
            return False
        return timezone.now().date() > self.data_validade

    @classmethod
    def gerar_proximo_numero(cls, empresa):
        """
        Gera o próximo número sequencial de orçamento para a empresa informada.
        A numeração é independente por empresa.
        """
        import re
        ultimo_orcamento = (
            cls.objects.filter(empresa=empresa)
            .aggregate(Max('numero'))
        )
        ultimo_numero = ultimo_orcamento.get('numero__max')

        if ultimo_numero:
            try:
                if ultimo_numero.startswith('ORC-'):
                    numero_sequencial = int(ultimo_numero.split('-')[1])
                    proximo_numero = numero_sequencial + 1
                else:
                    numeros = re.findall(r'\d+', ultimo_numero)
                    if numeros:
                        proximo_numero = int(numeros[-1]) + 1
                    else:
                        proximo_numero = 1
            except (ValueError, IndexError):
                proximo_numero = 1
        else:
            proximo_numero = 1

        return f"ORC-{proximo_numero:03d}"


class HistoricoStatusOrcamento(models.Model):
    """Linha do histórico de mudanças de status (criação e alterações posteriores)."""

    class Origem(models.TextChoices):
        CRIACAO = 'criacao', 'Criação'
        ATUALIZAR_STATUS = 'atualizar_status', 'Alterar status'
        EDICAO = 'edicao', 'Edição do orçamento'

    orcamento = models.ForeignKey(
        'Orcamento',
        on_delete=models.CASCADE,
        related_name='historicos_status',
        verbose_name='Orçamento',
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historicos_status_orcamento',
        verbose_name='Usuário',
    )
    status_anterior = models.ForeignKey(
        StatusOrcamento,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='+',
        verbose_name='Status anterior',
    )
    status_novo = models.ForeignKey(
        StatusOrcamento,
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name='Status novo',
    )
    data_registro = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name='Data do registro',
    )
    origem = models.CharField(
        max_length=30,
        choices=Origem.choices,
        verbose_name='Origem',
    )

    class Meta:
        verbose_name = 'Histórico de status do orçamento'
        verbose_name_plural = 'Históricos de status de orçamentos'
        ordering = ['data_registro', 'id']
        indexes = [
            models.Index(
                fields=['orcamento', 'data_registro'],
                name='ordens_serv_historic_idx',
            ),
        ]

    def __str__(self):
        return f'{self.orcamento_id} {self.get_origem_display()} → {self.status_novo_id}'


class ItemOrcamento(models.Model):
    """Modelo para representar itens de um orçamento (peças e serviços)"""
    
    TIPO_CHOICES = [
        ('peca', 'Peça'),
        ('servico', 'Serviço'),
    ]
    
    orcamento = models.ForeignKey(
        Orcamento,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Orçamento'
    )
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        default='servico',
        verbose_name='Tipo'
    )
    descricao = models.CharField(max_length=200, verbose_name='Descrição')
    quantidade = models.PositiveIntegerField(default=1, verbose_name='Quantidade')
    valor_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Valor Unitário'
    )
    produto = models.ForeignKey(
        'produtos.Produto',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='itens_orcamento',
        verbose_name='Produto do cadastro',
    )

    class Meta:
        verbose_name = 'Item de Orçamento'
        verbose_name_plural = 'Itens de Orçamento'
        ordering = ['id']
    
    def __str__(self):
        return f"{self.descricao} - Orçamento {self.orcamento.numero}"
    
    @property
    def valor_total(self):
        return self.quantidade * self.valor_unitario
