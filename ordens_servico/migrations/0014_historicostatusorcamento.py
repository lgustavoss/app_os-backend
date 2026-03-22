import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import django.utils.timezone


def backfill_historico_criacao(apps, schema_editor):
    Orcamento = apps.get_model('ordens_servico', 'Orcamento')
    HistoricoStatusOrcamento = apps.get_model('ordens_servico', 'HistoricoStatusOrcamento')
    rows = []
    for o in Orcamento.objects.all().iterator():
        rows.append(
            HistoricoStatusOrcamento(
                orcamento_id=o.pk,
                usuario_id=o.usuario_criacao_id,
                status_anterior_id=None,
                status_novo_id=o.status_id,
                data_registro=o.data_criacao,
                origem='criacao',
            )
        )
    if rows:
        HistoricoStatusOrcamento.objects.bulk_create(rows, batch_size=500)


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ordens_servico', '0013_orcamento_status_obrigatorio'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricoStatusOrcamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_registro', models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='Data do registro')),
                (
                    'origem',
                    models.CharField(
                        choices=[
                            ('criacao', 'Criação'),
                            ('atualizar_status', 'Alterar status'),
                            ('edicao', 'Edição do orçamento'),
                        ],
                        max_length=30,
                        verbose_name='Origem',
                    ),
                ),
                (
                    'orcamento',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='historicos_status',
                        to='ordens_servico.orcamento',
                        verbose_name='Orçamento',
                    ),
                ),
                (
                    'status_anterior',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='ordens_servico.statusorcamento',
                        verbose_name='Status anterior',
                    ),
                ),
                (
                    'status_novo',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='ordens_servico.statusorcamento',
                        verbose_name='Status novo',
                    ),
                ),
                (
                    'usuario',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='historicos_status_orcamento',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='Usuário',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Histórico de status do orçamento',
                'verbose_name_plural': 'Históricos de status de orçamentos',
                'ordering': ['data_registro', 'id'],
            },
        ),
        migrations.AddIndex(
            model_name='historicostatusorcamento',
            index=models.Index(fields=['orcamento', 'data_registro'], name='ordens_serv_historic_idx'),
        ),
        migrations.RunPython(backfill_historico_criacao, migrations.RunPython.noop),
    ]
