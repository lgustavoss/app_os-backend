# Generated manually for multi-empresa

from django.db import migrations, models


def atribuir_empresa_existente(apps, schema_editor):
    """Atribui a primeira empresa (id=1) a todos os orçamentos existentes."""
    ConfiguracaoEmpresa = apps.get_model('configuracoes', 'ConfiguracaoEmpresa')
    Orcamento = apps.get_model('ordens_servico', 'Orcamento')
    primeira = ConfiguracaoEmpresa.objects.order_by('id').first()
    if primeira:
        Orcamento.objects.filter(empresa__isnull=True).update(empresa=primeira)


def reverse_atribuir(apps, schema_editor):
    """Não é possível reverter a atribuição de empresa."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('ordens_servico', '0006_add_ativo_orcamento'),
        ('configuracoes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='orcamento',
            name='empresa',
            field=models.ForeignKey(
                null=True,
                on_delete=models.PROTECT,
                related_name='orcamentos',
                to='configuracoes.configuracaoempresa',
                verbose_name='Empresa',
            ),
        ),
        migrations.RunPython(atribuir_empresa_existente, reverse_atribuir),
        migrations.AlterField(
            model_name='orcamento',
            name='empresa',
            field=models.ForeignKey(
                on_delete=models.PROTECT,
                related_name='orcamentos',
                to='configuracoes.configuracaoempresa',
                verbose_name='Empresa',
            ),
        ),
        migrations.AlterField(
            model_name='orcamento',
            name='numero',
            field=models.CharField(editable=False, max_length=20, verbose_name='Número do Orçamento'),
        ),
        migrations.AddConstraint(
            model_name='orcamento',
            constraint=models.UniqueConstraint(
                fields=('empresa', 'numero'),
                name='ordens_servico_orcamento_empresa_numero_uniq',
            ),
        ),
    ]
