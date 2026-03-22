from rest_framework import serializers
from common.doc_validation import only_digits, empresa_cnpj_duplicado
from .models import ConfiguracaoEmpresa
from .constants import (
    LOGO_LARGURA_MAX_CM,
    LOGO_ALTURA_MAX_CM,
    SELO_LARGURA_MAX_CM,
    SELO_ALTURA_MAX_CM,
    SELO_COLUNA_LARGURA_CM,
)


class ConfiguracaoEmpresaSerializer(serializers.ModelSerializer):
    logomarca_url = serializers.SerializerMethodField()
    logo_dimensoes_maximas = serializers.SerializerMethodField()
    selo_certificacao_1_url = serializers.SerializerMethodField()
    selo_certificacao_2_url = serializers.SerializerMethodField()
    selo_certificacao_3_url = serializers.SerializerMethodField()
    selo_dimensoes_maximas = serializers.SerializerMethodField()

    remover_logomarca = serializers.BooleanField(required=False, default=False, write_only=True)
    remover_selo_certificacao_1 = serializers.BooleanField(required=False, default=False, write_only=True)
    remover_selo_certificacao_2 = serializers.BooleanField(required=False, default=False, write_only=True)
    remover_selo_certificacao_3 = serializers.BooleanField(required=False, default=False, write_only=True)
    
    class Meta:
        model = ConfiguracaoEmpresa
        fields = [
            'id',
            'razao_social',
            'nome_fantasia',
            'nome_exibicao_menu',
            'cnpj',
            'inscricao_estadual',
            'inscricao_municipal',
            'endereco',
            'numero',
            'complemento',
            'bairro',
            'cidade',
            'estado',
            'cep',
            'telefone',
            'celular',
            'email',
            'website',
            'logomarca',
            'logomarca_url',
            'logo_dimensoes_maximas',
            'selo_certificacao_1',
            'selo_certificacao_2',
            'selo_certificacao_3',
            'selo_certificacao_1_url',
            'selo_certificacao_2_url',
            'selo_certificacao_3_url',
            'selo_dimensoes_maximas',
            'texto_selos_cabecalho_pdf',
            'texto_rodape',
            'observacoes_padrao',
            'data_criacao',
            'data_atualizacao',
            'remover_logomarca',
            'remover_selo_certificacao_1',
            'remover_selo_certificacao_2',
            'remover_selo_certificacao_3',
        ]
        read_only_fields = ['id', 'data_criacao', 'data_atualizacao']

    def validate_cnpj(self, value):
        digits = only_digits(value)
        if len(digits) != 14:
            raise serializers.ValidationError('CNPJ deve conter 14 dígitos.')
        exclude = self.instance.pk if self.instance else None
        if empresa_cnpj_duplicado(digits, exclude_pk=exclude):
            raise serializers.ValidationError('Já existe uma empresa cadastrada com este CNPJ.')
        return digits

    def get_logomarca_url(self, obj):
        """Retorna a URL da logomarca se existir"""
        if obj.logomarca:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logomarca.url)
            return obj.logomarca.url
        return None

    def get_logo_dimensoes_maximas(self, obj):
        """
        Retorna as dimensões máximas da logo (em cm) para exibição no frontend.
        O frontend deve usar como tamanho máximo ao importar e permitir que o
        usuário ajuste (diminuir/aumentar) para otimizar a visualização.
        """
        return {
            'largura_cm': LOGO_LARGURA_MAX_CM,
            'altura_cm': LOGO_ALTURA_MAX_CM,
        }

    def _abs_media_url(self, filefield):
        if not filefield:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(filefield.url)
        return filefield.url

    def get_selo_certificacao_1_url(self, obj):
        return self._abs_media_url(obj.selo_certificacao_1)

    def get_selo_certificacao_2_url(self, obj):
        return self._abs_media_url(obj.selo_certificacao_2)

    def get_selo_certificacao_3_url(self, obj):
        return self._abs_media_url(obj.selo_certificacao_3)

    def get_selo_dimensoes_maximas(self, obj):
        slot = round(SELO_COLUNA_LARGURA_CM / 3, 2)
        return {
            'largura_cm': SELO_LARGURA_MAX_CM,
            'altura_cm': SELO_ALTURA_MAX_CM,
            'altura_alvo_cm': LOGO_ALTURA_MAX_CM,
            'largura_coluna_cm': SELO_COLUNA_LARGURA_CM,
            'largura_slot_aprox_cm': slot,
            'max_selos': 3,
            'dica_pdf': (
                f'No PDF, cada selo ocupa um retângulo retrato de ~{slot} cm × {LOGO_ALTURA_MAX_CM} cm '
                f'(faixa total {SELO_COLUNA_LARGURA_CM} cm). O recorte na tela usa essa mesma proporção. '
                'Evite artes muito largas e baixas.'
            ),
        }

    def create(self, validated_data):
        validated_data.pop('remover_logomarca', False)
        validated_data.pop('remover_selo_certificacao_1', False)
        validated_data.pop('remover_selo_certificacao_2', False)
        validated_data.pop('remover_selo_certificacao_3', False)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        remover_logo = validated_data.pop('remover_logomarca', False)
        r_selo1 = validated_data.pop('remover_selo_certificacao_1', False)
        r_selo2 = validated_data.pop('remover_selo_certificacao_2', False)
        r_selo3 = validated_data.pop('remover_selo_certificacao_3', False)

        # Novo upload tem prioridade sobre remoção
        if remover_logo and 'logomarca' not in validated_data:
            if instance.logomarca:
                instance.logomarca.delete(save=False)
            instance.logomarca = None

        for flag, field in (
            (r_selo1, 'selo_certificacao_1'),
            (r_selo2, 'selo_certificacao_2'),
            (r_selo3, 'selo_certificacao_3'),
        ):
            if flag and field not in validated_data:
                f = getattr(instance, field)
                if f:
                    f.delete(save=False)
                setattr(instance, field, None)

        return super().update(instance, validated_data)

