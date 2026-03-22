from django.db import migrations, models
import django.db.models.deletion


def preencher_status_nulos(apps, schema_editor):
    Orcamento = apps.get_model('ordens_servico', 'Orcamento')
    StatusOrcamento = apps.get_model('ordens_servico', 'StatusOrcamento')
    primeiro = StatusOrcamento.objects.order_by('ordem', 'id').first()
    if not primeiro:
        if Orcamento.objects.filter(status__isnull=True).exists():
            raise RuntimeError(
                'Existem orçamentos sem status e nenhum status cadastrado. '
                'Cadastre pelo menos um status de orçamento antes de aplicar esta migração.'
            )
        return
    Orcamento.objects.filter(status__isnull=True).update(status_id=primeiro.pk)


class Migration(migrations.Migration):
    dependencies = [
        ('ordens_servico', '0012_status_fk_finalize_schema'),
    ]

    operations = [
        migrations.RunPython(preencher_status_nulos, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='orcamento',
            name='status',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='orcamentos',
                to='ordens_servico.statusorcamento',
                verbose_name='Status',
            ),
        ),
    ]
