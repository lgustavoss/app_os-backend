import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('ordens_servico', '0011_status_fk_limpar_dados'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orcamento',
            name='status',
        ),
        migrations.RenameField(
            model_name='orcamento',
            old_name='status_new',
            new_name='status',
        ),
        migrations.AlterField(
            model_name='orcamento',
            name='status',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='orcamentos',
                to='ordens_servico.statusorcamento',
                verbose_name='Status',
            ),
        ),
        migrations.RemoveField(
            model_name='statusorcamento',
            name='codigo',
        ),
        migrations.RemoveField(
            model_name='statusorcamento',
            name='ignora_data_validade',
        ),
    ]
