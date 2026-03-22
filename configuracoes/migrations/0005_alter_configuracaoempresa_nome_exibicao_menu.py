# Alinha help_text / verbose_name do modelo com o estado atual

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configuracoes', '0004_configuracaoempresa_selos_pdf'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configuracaoempresa',
            name='nome_exibicao_menu',
            field=models.CharField(
                blank=True,
                help_text='Nome curto no seletor de empresa. Se vazio, usa nome fantasia ou razão social.',
                max_length=200,
                null=True,
                verbose_name='Nome de exibição no menu',
            ),
        ),
    ]
