from django.db import models
from django.contrib.auth.models import User


class Cliente(models.Model):
    """Modelo para representar um Cliente"""
    
    TIPO_DOCUMENTO_CHOICES = [
        ('CPF', 'CPF'),
        ('CNPJ', 'CNPJ'),
    ]
    
    cnpj_cpf = models.CharField(max_length=18, unique=True, verbose_name='CNPJ/CPF')
    tipo_documento = models.CharField(
        max_length=4,
        choices=TIPO_DOCUMENTO_CHOICES,
        verbose_name='Tipo de Documento'
    )
    razao_social = models.CharField(max_length=200, verbose_name='Razão Social')
    nome_fantasia = models.CharField(max_length=200, blank=True, null=True, verbose_name='Nome Fantasia')
    inscricao_estadual = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Inscrição estadual',
    )
    email = models.EmailField(blank=True, null=True, verbose_name='E-mail')
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefone')
    endereco = models.CharField(max_length=200, blank=True, null=True, verbose_name='Endereço')
    cep = models.CharField(max_length=10, blank=True, null=True, verbose_name='CEP')
    cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name='Cidade')
    estado = models.CharField(max_length=2, blank=True, null=True, verbose_name='Estado')
    
    # Campos de auditoria
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name='Data de Cadastro')
    usuario_cadastro = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='clientes_cadastrados',
        verbose_name='Usuário de Cadastro'
    )
    data_ultima_alteracao = models.DateTimeField(auto_now=True, verbose_name='Data da Última Alteração')
    usuario_ultima_alteracao = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clientes_alterados',
        verbose_name='Usuário da Última Alteração'
    )
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['razao_social']
        indexes = [
            models.Index(fields=['ativo', 'razao_social']),
        ]
    
    def __str__(self):
        return f"{self.razao_social} - {self.cnpj_cpf}"

