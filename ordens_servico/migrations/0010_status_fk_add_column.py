import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('ordens_servico', '0009_statusorcamento_alter_orcamento_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='orcamento',
            name='status_new',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='orcamentos_novos',
                to='ordens_servico.statusorcamento',
                verbose_name='Status',
            ),
        ),
    ]
