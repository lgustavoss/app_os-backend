# Data migration: define empresa_atual para usuários existentes

from django.db import migrations


def definir_empresa_atual_inicial(apps, schema_editor):
    PerfilUsuario = apps.get_model('autenticacao', 'PerfilUsuario')
    ConfiguracaoEmpresa = apps.get_model('configuracoes', 'ConfiguracaoEmpresa')
    User = apps.get_model('auth', 'User')
    primeira = ConfiguracaoEmpresa.objects.order_by('id').first()
    for user in User.objects.all():
        perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
        if primeira and perfil.empresa_atual_id is None:
            perfil.empresa_atual = primeira
            perfil.save(update_fields=['empresa_atual'])


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('autenticacao', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(definir_empresa_atual_inicial, reverse_noop),
    ]
