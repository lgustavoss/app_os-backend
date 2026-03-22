import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produtos', '0001_initial'),
        ('ordens_servico', '0014_historicostatusorcamento'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemorcamento',
            name='produto',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='itens_orcamento',
                to='produtos.produto',
                verbose_name='Produto do cadastro',
            ),
        ),
    ]
