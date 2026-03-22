from django.db import models
from django.conf import settings
from django.contrib.auth.models import User


class PerfilUsuario(models.Model):
    """
    Perfil do usuário para multi-empresa.
    Armazena a empresa atual de trabalho (orçamentos, dashboard, etc.).
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil',
        verbose_name='Usuário',
    )
    empresa_atual = models.ForeignKey(
        'configuracoes.ConfiguracaoEmpresa',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_ativos',
        verbose_name='Empresa atual',
    )
    # Permissões por módulo (não-staff). Cadastrar/configurar implica visualizar.
    clientes_pode_visualizar = models.BooleanField(
        default=True,
        verbose_name='Clientes — visualizar',
    )
    clientes_pode_cadastrar = models.BooleanField(
        default=True,
        verbose_name='Clientes — cadastrar/editar',
    )
    orcamentos_pode_visualizar = models.BooleanField(
        default=True,
        verbose_name='Orçamentos — visualizar',
    )
    orcamentos_pode_cadastrar = models.BooleanField(
        default=True,
        verbose_name='Orçamentos — cadastrar/editar',
    )
    configuracoes_pode_visualizar = models.BooleanField(
        default=True,
        verbose_name='Configurações — visualizar',
    )
    configuracoes_pode_configurar = models.BooleanField(
        default=True,
        verbose_name='Configurações — configurar',
    )

    class Meta:
        verbose_name = 'Perfil do Usuário'
        verbose_name_plural = 'Perfis dos Usuários'

    def __str__(self):
        return f"Perfil de {self.user.username}"

    def save(self, *args, **kwargs):
        if self.clientes_pode_cadastrar:
            self.clientes_pode_visualizar = True
        if not self.clientes_pode_visualizar:
            self.clientes_pode_cadastrar = False
        if self.orcamentos_pode_cadastrar:
            self.orcamentos_pode_visualizar = True
        if not self.orcamentos_pode_visualizar:
            self.orcamentos_pode_cadastrar = False
        if self.configuracoes_pode_configurar:
            self.configuracoes_pode_visualizar = True
        if not self.configuracoes_pode_visualizar:
            self.configuracoes_pode_configurar = False
        super().save(*args, **kwargs)
