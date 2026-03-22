from django.db import migrations


def forwards(apps, schema_editor):
    ItemOrcamento = apps.get_model('ordens_servico', 'ItemOrcamento')
    ItemOrcamento.objects.filter(tipo='peca', produto__isnull=True).update(tipo='servico')


class Migration(migrations.Migration):

    dependencies = [
        ('ordens_servico', '0015_itemorcamento_produto'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
