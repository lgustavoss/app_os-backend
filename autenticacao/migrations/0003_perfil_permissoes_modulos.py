from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autenticacao', '0002_perfil_empresa_atual_inicial'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfilusuario',
            name='clientes_pode_cadastrar',
            field=models.BooleanField(default=True, verbose_name='Clientes — cadastrar/editar'),
        ),
        migrations.AddField(
            model_name='perfilusuario',
            name='clientes_pode_visualizar',
            field=models.BooleanField(default=True, verbose_name='Clientes — visualizar'),
        ),
        migrations.AddField(
            model_name='perfilusuario',
            name='configuracoes_pode_configurar',
            field=models.BooleanField(default=True, verbose_name='Configurações — configurar'),
        ),
        migrations.AddField(
            model_name='perfilusuario',
            name='configuracoes_pode_visualizar',
            field=models.BooleanField(default=True, verbose_name='Configurações — visualizar'),
        ),
        migrations.AddField(
            model_name='perfilusuario',
            name='orcamentos_pode_cadastrar',
            field=models.BooleanField(default=True, verbose_name='Orçamentos — cadastrar/editar'),
        ),
        migrations.AddField(
            model_name='perfilusuario',
            name='orcamentos_pode_visualizar',
            field=models.BooleanField(default=True, verbose_name='Orçamentos — visualizar'),
        ),
    ]
