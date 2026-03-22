from django.db import migrations


def limpar_status_e_remover_catalogo(apps, schema_editor):
    Orcamento = apps.get_model('ordens_servico', 'Orcamento')
    StatusOrcamento = apps.get_model('ordens_servico', 'StatusOrcamento')
    Orcamento.objects.all().update(status_new_id=None)
    StatusOrcamento.objects.all().delete()
    Orcamento.objects.all().update(status='')


class Migration(migrations.Migration):
    dependencies = [
        ('ordens_servico', '0010_status_fk_add_column'),
    ]

    operations = [
        migrations.RunPython(limpar_status_e_remover_catalogo, migrations.RunPython.noop),
    ]
