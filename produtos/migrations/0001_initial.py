from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Produto',
            fields=[
                (
                    'codigo',
                    models.PositiveIntegerField(
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name='Código',
                    ),
                ),
                ('descricao', models.CharField(max_length=255, verbose_name='Descrição')),
                (
                    'valor',
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        verbose_name='Valor',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Produto',
                'verbose_name_plural': 'Produtos',
                'ordering': ['codigo'],
            },
        ),
    ]
