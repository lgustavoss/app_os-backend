from django.db import models
from django.db.models import Max


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
