import django.utils.timezone
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ordens_servico', '0007_orcamento_empresa_numero_por_empresa'),
    ]

    operations = [
        migrations.AddField(
            model_name='orcamento',
            name='usuario_ultima_alteracao',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='orcamentos_alterados',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Último usuário a alterar',
            ),
        ),
        migrations.AddField(
            model_name='orcamento',
            name='data_ultima_alteracao',
            field=models.DateTimeField(
                default=django.utils.timezone.now,
                verbose_name='Data da última alteração',
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='orcamento',
            name='data_ultima_alteracao',
            field=models.DateTimeField(
                auto_now=True,
                verbose_name='Data da última alteração',
            ),
        ),
    ]
