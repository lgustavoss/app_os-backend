from django.db import migrations, models
import django.db.models.deletion


def _garantir_status_padrao(apps, schema_editor):
    """Se não houver status (banco vazio ou legado), cria os padrões antes de tornar FK obrigatória."""
    StatusOrcamento = apps.get_model('ordens_servico', 'StatusOrcamento')
    if StatusOrcamento.objects.exists():
        return
    for nome, ordem, ativo in [
        ('Rascunho', 10, True),
        ('Enviado', 20, True),
        ('Aprovado', 30, True),
        ('Rejeitado', 40, True),
        ('Vencido', 50, True),
        ('Cancelado', 60, True),
    ]:
        StatusOrcamento.objects.create(nome=nome, ordem=ordem, ativo=ativo)


def preencher_status_nulos(apps, schema_editor):
    Orcamento = apps.get_model('ordens_servico', 'Orcamento')
    StatusOrcamento = apps.get_model('ordens_servico', 'StatusOrcamento')
    _garantir_status_padrao(apps, schema_editor)
    primeiro = StatusOrcamento.objects.order_by('ordem', 'id').first()
    if primeiro:
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
