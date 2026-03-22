from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0002_cliente_ativo_cliente_clientes_cl_ativo_794ed4_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='inscricao_estadual',
            field=models.CharField(
                blank=True,
                max_length=20,
                null=True,
                verbose_name='Inscrição estadual',
            ),
        ),
        migrations.AddField(
            model_name='cliente',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='E-mail'),
        ),
    ]
