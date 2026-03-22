from django.db import migrations, models


def seed_statuses(apps, schema_editor):
    StatusOrcamento = apps.get_model('ordens_servico', 'StatusOrcamento')
    rows = [
        ('rascunho', 'Rascunho', 10, True, False),
        ('enviado', 'Enviado', 20, True, False),
        ('aprovado', 'Aprovado', 30, True, True),
        ('rejeitado', 'Rejeitado', 40, True, True),
        ('vencido', 'Vencido', 50, True, False),
        ('cancelado', 'Cancelado', 60, True, True),
    ]
    for codigo, nome, ordem, ativo, ignora in rows:
        StatusOrcamento.objects.get_or_create(
            codigo=codigo,
            defaults={
                'nome': nome,
                'ordem': ordem,
                'ativo': ativo,
                'ignora_data_validade': ignora,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('ordens_servico', '0008_orcamento_auditoria_ultima_alteracao'),
    ]

    operations = [
        migrations.CreateModel(
            name='StatusOrcamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.SlugField(help_text='Identificador fixo (ex.: em_analise). Não pode ser alterado após criado.', max_length=40, unique=True, verbose_name='Código interno')),
                ('nome', models.CharField(max_length=100, verbose_name='Nome exibido')),
                ('ordem', models.PositiveSmallIntegerField(db_index=True, default=0)),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo na seleção')),
                ('ignora_data_validade', models.BooleanField(default=False, help_text='Se marcado, a data de validade não considera o orçamento vencido (ex.: aprovado, cancelado).', verbose_name='Ignora vencimento')),
            ],
            options={
                'verbose_name': 'Status de orçamento',
                'verbose_name_plural': 'Status de orçamentos',
                'ordering': ['ordem', 'id'],
            },
        ),
        migrations.RunPython(seed_statuses, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='orcamento',
            name='status',
            field=models.CharField(
                default='rascunho',
                help_text='Código do registro em StatusOrcamento.',
                max_length=40,
                verbose_name='Status',
            ),
        ),
    ]
