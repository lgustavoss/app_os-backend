# Generated manually for selos no PDF do orçamento

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configuracoes', '0003_configuracaoempresa_nome_exibicao_menu'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuracaoempresa',
            name='selo_certificacao_1',
            field=models.ImageField(
                blank=True,
                help_text='Ex.: NCC, INMETRO — aparece no topo direito do orçamento.',
                null=True,
                upload_to='configuracoes/empresa/selos/',
                validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])],
                verbose_name='Selo de certificação 1 (PDF)',
            ),
        ),
        migrations.AddField(
            model_name='configuracaoempresa',
            name='selo_certificacao_2',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='configuracoes/empresa/selos/',
                validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])],
                verbose_name='Selo de certificação 2 (PDF)',
            ),
        ),
        migrations.AddField(
            model_name='configuracaoempresa',
            name='selo_certificacao_3',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='configuracoes/empresa/selos/',
                validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])],
                verbose_name='Selo de certificação 3 (PDF)',
            ),
        ),
        migrations.AddField(
            model_name='configuracaoempresa',
            name='texto_selos_cabecalho_pdf',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Usado no topo direito quando não há imagens de selo (ex.: frase de certificação).',
                max_length=400,
                verbose_name='Texto no cabeçalho do PDF (sem selos)',
            ),
        ),
    ]
