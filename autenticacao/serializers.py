from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from configuracoes.models import ConfiguracaoEmpresa
from common.user_display import usuario_exibicao
from .models import PerfilUsuario


def checar_regras_senha(password: str, user=None) -> dict:
    """
    Usa os validadores configurados em AUTH_PASSWORD_VALIDATORS.
    Retorno: {'valido': bool, 'erros': list[str]} — para API e para o serializer.
    """
    if password is None or str(password).strip() == '':
        return {'valido': False, 'erros': ['Informe uma senha.']}
    try:
        if user is not None:
            validate_password(password, user=user)
        else:
            validate_password(password)
        return {'valido': True, 'erros': []}
    except DjangoValidationError as exc:
        return {'valido': False, 'erros': list(exc.messages)}


def _validate_password_api(password, user=None):
    """Converte falhas do Django em ValidationError do DRF (evita 500 no create/update)."""
    resultado = checar_regras_senha(password, user)
    if not resultado['valido']:
        raise serializers.ValidationError({'password': resultado['erros']})


class EmpresaMinimaSerializer(serializers.ModelSerializer):
    """Serializer resumido da empresa para listagem no perfil do usuário."""
    class Meta:
        model = ConfiguracaoEmpresa
        fields = ['id', 'razao_social', 'nome_fantasia', 'nome_exibicao_menu']


def permissoes_efetivas_usuario(user) -> dict:
    """Permissões para o front (staff = tudo liberado)."""
    if not user or not user.is_authenticated:
        return {}
    if getattr(user, 'is_staff', False):
        return {
            'clientes_pode_visualizar': True,
            'clientes_pode_cadastrar': True,
            'orcamentos_pode_visualizar': True,
            'orcamentos_pode_cadastrar': True,
            'configuracoes_pode_visualizar': True,
            'configuracoes_pode_configurar': True,
        }
    perfil = getattr(user, 'perfil', None)
    if not perfil:
        return {
            'clientes_pode_visualizar': False,
            'clientes_pode_cadastrar': False,
            'orcamentos_pode_visualizar': False,
            'orcamentos_pode_cadastrar': False,
            'configuracoes_pode_visualizar': False,
            'configuracoes_pode_configurar': False,
        }
    return {
        'clientes_pode_visualizar': perfil.clientes_pode_visualizar,
        'clientes_pode_cadastrar': perfil.clientes_pode_cadastrar,
        'orcamentos_pode_visualizar': perfil.orcamentos_pode_visualizar,
        'orcamentos_pode_cadastrar': perfil.orcamentos_pode_cadastrar,
        'configuracoes_pode_visualizar': perfil.configuracoes_pode_visualizar,
        'configuracoes_pode_configurar': perfil.configuracoes_pode_configurar,
    }


class PerfilPermissoesSerializer(serializers.Serializer):
    """Leitura/escrita das permissões por módulo (perfil)."""
    clientes_pode_visualizar = serializers.BooleanField(required=False)
    clientes_pode_cadastrar = serializers.BooleanField(required=False)
    orcamentos_pode_visualizar = serializers.BooleanField(required=False)
    orcamentos_pode_cadastrar = serializers.BooleanField(required=False)
    configuracoes_pode_visualizar = serializers.BooleanField(required=False)
    configuracoes_pode_configurar = serializers.BooleanField(required=False)


class UserSerializer(serializers.ModelSerializer):
    """Serializer para informações do usuário (inclui empresa atual e lista de empresas)."""
    empresa_atual = serializers.SerializerMethodField()
    empresas = serializers.SerializerMethodField()
    nome_exibicao = serializers.SerializerMethodField()
    permissoes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_staff', 'is_active', 'date_joined', 'empresa_atual', 'empresas',
            'nome_exibicao', 'permissoes',
        ]
        read_only_fields = ['id', 'date_joined', 'username']

    def get_nome_exibicao(self, obj):
        return usuario_exibicao(obj)

    def get_permissoes(self, obj):
        return permissoes_efetivas_usuario(obj)

    def get_empresa_atual(self, obj):
        perfil = getattr(obj, 'perfil', None)
        if perfil and perfil.empresa_atual_id:
            return EmpresaMinimaSerializer(perfil.empresa_atual).data
        return None

    def get_empresas(self, obj):
        return EmpresaMinimaSerializer(
            ConfiguracaoEmpresa.objects.order_by('razao_social'),
            many=True
        ).data


class LoginSerializer(serializers.Serializer):
    """Login com e-mail e senha."""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class ValidarSenhaEntradaSerializer(serializers.Serializer):
    """Entrada para POST /api/auth/validar-senha/ (pré-validação no front)."""
    password = serializers.CharField(required=True, allow_blank=False)
    usuario_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)


class UsuarioSistemaSerializer(serializers.ModelSerializer):
    """CRUD de usuários (staff): leitura e escrita sem senha em leitura."""
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)
    nome_exibicao = serializers.SerializerMethodField(read_only=True)
    permissoes = PerfilPermissoesSerializer(required=False, write_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'is_staff', 'is_active',
            'date_joined', 'last_login', 'password', 'nome_exibicao',
            'permissoes',
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']

    def get_nome_exibicao(self, obj):
        return usuario_exibicao(obj)

    def _perfil_permissoes_dict(self, user):
        perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
        return {
            'clientes_pode_visualizar': perfil.clientes_pode_visualizar,
            'clientes_pode_cadastrar': perfil.clientes_pode_cadastrar,
            'orcamentos_pode_visualizar': perfil.orcamentos_pode_visualizar,
            'orcamentos_pode_cadastrar': perfil.orcamentos_pode_cadastrar,
            'configuracoes_pode_visualizar': perfil.configuracoes_pode_visualizar,
            'configuracoes_pode_configurar': perfil.configuracoes_pode_configurar,
        }

    def _aplicar_permissoes(self, user, perm_data: dict):
        if not perm_data:
            return
        # DRF pode entregar OrderedDict / ReturnDict; normalizar para leitura estável
        if hasattr(perm_data, 'items'):
            perm_data = dict(perm_data)
        perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
        for key in (
            'clientes_pode_visualizar',
            'clientes_pode_cadastrar',
            'orcamentos_pode_visualizar',
            'orcamentos_pode_cadastrar',
            'configuracoes_pode_visualizar',
            'configuracoes_pode_configurar',
        ):
            if key in perm_data:
                setattr(perfil, key, perm_data[key])
        perfil.save()

    def validate_email(self, value):
        email = (value or '').strip().lower()
        if not email:
            raise serializers.ValidationError('Informe um e-mail válido.')
        qs = User.objects.filter(email__iexact=email)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Já existe usuário com este e-mail.')
        return email

    def create(self, validated_data):
        perm_data = validated_data.pop('permissoes', None) or {}
        password = validated_data.pop('password', None)
        if not password:
            raise serializers.ValidationError({'password': 'Senha é obrigatória na criação.'})
        _validate_password_api(password)
        email = validated_data['email']
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_staff=validated_data.get('is_staff', False),
            is_active=validated_data.get('is_active', True),
        )
        if user.is_staff:
            perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
            perfil.clientes_pode_visualizar = True
            perfil.clientes_pode_cadastrar = True
            perfil.orcamentos_pode_visualizar = True
            perfil.orcamentos_pode_cadastrar = True
            perfil.configuracoes_pode_visualizar = True
            perfil.configuracoes_pode_configurar = True
            perfil.save()
        else:
            self._aplicar_permissoes(user, perm_data)
        return user

    def update(self, instance, validated_data):
        perm_data = validated_data.pop('permissoes', None)
        if perm_data is not None and hasattr(perm_data, 'items'):
            perm_data = dict(perm_data)
        password = validated_data.pop('password', None)
        if password is not None and str(password).strip() == '':
            password = None
        email = validated_data.get('email')
        if email:
            validated_data['username'] = email
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            _validate_password_api(password, user=instance)
            instance.set_password(password)
        instance.save()
        if perm_data is not None:
            if instance.is_staff:
                perfil, _ = PerfilUsuario.objects.get_or_create(user=instance)
                perfil.clientes_pode_visualizar = True
                perfil.clientes_pode_cadastrar = True
                perfil.orcamentos_pode_visualizar = True
                perfil.orcamentos_pode_cadastrar = True
                perfil.configuracoes_pode_visualizar = True
                perfil.configuracoes_pode_configurar = True
                perfil.save()
            else:
                self._aplicar_permissoes(instance, perm_data)
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['permissoes'] = self._perfil_permissoes_dict(instance)
        return data

