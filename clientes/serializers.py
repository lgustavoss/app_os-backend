from rest_framework import serializers
from common.doc_validation import only_digits, cliente_documento_duplicado
from common.user_display import usuario_exibicao
from .models import Cliente


class ClienteSerializer(serializers.ModelSerializer):
    usuario_cadastro_nome = serializers.SerializerMethodField()
    usuario_ultima_alteracao_nome = serializers.SerializerMethodField()

    def get_usuario_cadastro_nome(self, obj):
        return usuario_exibicao(obj.usuario_cadastro)

    def get_usuario_ultima_alteracao_nome(self, obj):
        return usuario_exibicao(obj.usuario_ultima_alteracao)
    
    class Meta:
        model = Cliente
        fields = [
            'id',
            'cnpj_cpf',
            'tipo_documento',
            'razao_social',
            'nome_fantasia',
            'inscricao_estadual',
            'email',
            'telefone',
            'endereco',
            'cep',
            'cidade',
            'estado',
            'data_cadastro',
            'usuario_cadastro',
            'usuario_cadastro_nome',
            'data_ultima_alteracao',
            'usuario_ultima_alteracao',
            'usuario_ultima_alteracao_nome',
            'ativo',
        ]
        read_only_fields = [
            'data_cadastro',
            'data_ultima_alteracao',
            'usuario_cadastro',
            'usuario_ultima_alteracao',
            'ativo',
        ]

    def validate(self, attrs):
        instance = self.instance
        if 'email' in attrs and attrs.get('email') is not None:
            e = (attrs['email'] or '').strip()
            attrs['email'] = e or None
        if 'inscricao_estadual' in attrs and attrs.get('inscricao_estadual') is not None:
            ie = (attrs['inscricao_estadual'] or '').strip()
            attrs['inscricao_estadual'] = ie or None

        if 'cnpj_cpf' not in attrs and 'tipo_documento' not in attrs:
            return attrs
        doc = attrs.get('cnpj_cpf', instance.cnpj_cpf if instance else '') or ''
        tipo = attrs.get('tipo_documento', instance.tipo_documento if instance else None)
        digits = only_digits(doc)
        if tipo == 'CNPJ' and len(digits) != 14:
            raise serializers.ValidationError({'cnpj_cpf': 'CNPJ deve conter 14 dígitos.'})
        if tipo == 'CPF' and len(digits) != 11:
            raise serializers.ValidationError({'cnpj_cpf': 'CPF deve conter 11 dígitos.'})
        exclude = instance.pk if instance else None
        if cliente_documento_duplicado(digits, exclude_pk=exclude):
            raise serializers.ValidationError(
                {'cnpj_cpf': 'Já existe um cliente cadastrado com este CNPJ/CPF.'}
            )
        if 'cnpj_cpf' in attrs:
            attrs['cnpj_cpf'] = digits
        return attrs


class ClienteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = [
            'cnpj_cpf',
            'tipo_documento',
            'razao_social',
            'nome_fantasia',
            'inscricao_estadual',
            'email',
            'telefone',
            'endereco',
            'cep',
            'cidade',
            'estado',
        ]

    def validate(self, attrs):
        doc = attrs.get('cnpj_cpf', '') or ''
        tipo = attrs.get('tipo_documento')
        digits = only_digits(doc)
        if tipo == 'CNPJ' and len(digits) != 14:
            raise serializers.ValidationError({'cnpj_cpf': 'CNPJ deve conter 14 dígitos.'})
        if tipo == 'CPF' and len(digits) != 11:
            raise serializers.ValidationError({'cnpj_cpf': 'CPF deve conter 11 dígitos.'})
        if cliente_documento_duplicado(digits, exclude_pk=None):
            raise serializers.ValidationError(
                {'cnpj_cpf': 'Já existe um cliente cadastrado com este CNPJ/CPF.'}
            )
        attrs['cnpj_cpf'] = digits
        if attrs.get('email') is not None:
            e = (attrs['email'] or '').strip()
            attrs['email'] = e or None
        if attrs.get('inscricao_estadual') is not None:
            ie = (attrs['inscricao_estadual'] or '').strip()
            attrs['inscricao_estadual'] = ie or None
        return attrs

