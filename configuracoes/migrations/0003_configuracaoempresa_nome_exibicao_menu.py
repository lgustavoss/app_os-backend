# Generated manually for nome de exibição no menu

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configuracoes', '0002_alter_configuracaoempresa_logomarca'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuracaoempresa',
            name='nome_exibicao_menu',
            field=models.CharField(
                blank=True,
                help_text='Nome curto exibido no seletor de empresa no topo. Se vazio, usa nome fantasia ou razão social.',
                max_length=200,
                null=True,
                verbose_name='Nome de exibição no menu',
            ),
        ),
    ]
