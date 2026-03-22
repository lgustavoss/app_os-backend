from rest_framework import serializers
from common.user_display import usuario_exibicao
from produtos.models import Produto
from .models import HistoricoStatusOrcamento, Orcamento, ItemOrcamento, StatusOrcamento


def validate_orcamento_status_fk(value, instance=None):
    """Valida FK de status. Permite manter status inativo já gravado no orçamento."""
    if value is None:
        raise serializers.ValidationError('O status do orçamento é obrigatório.')
    pk = getattr(value, 'pk', value)
    try:
        st = StatusOrcamento.objects.get(pk=pk)
    except StatusOrcamento.DoesNotExist:
        raise serializers.ValidationError('Status inválido.')
    if st.ativo:
        return st
    if instance is not None and getattr(instance, 'status_id', None) == st.pk:
        return st
    raise serializers.ValidationError(
        'Este status está inativo e não pode ser atribuído a orçamentos.'
    )


class StatusOrcamentoSerializer(serializers.ModelSerializer):
    """id permanece na API para vínculo técnico; não expor como “número” ao utilizador."""

    class Meta:
        model = StatusOrcamento
        fields = ['id', 'nome', 'ordem', 'ativo']


class HistoricoStatusOrcamentoSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.SerializerMethodField()
    status_anterior_nome = serializers.SerializerMethodField()
    status_novo_nome = serializers.SerializerMethodField()
    origem_label = serializers.SerializerMethodField()

    class Meta:
        model = HistoricoStatusOrcamento
        fields = [
            'id',
            'data_registro',
            'origem',
            'origem_label',
            'usuario',
            'usuario_nome',
            'status_anterior',
            'status_anterior_nome',
            'status_novo',
            'status_novo_nome',
        ]

    def get_usuario_nome(self, obj):
        return usuario_exibicao(obj.usuario)

    def get_status_anterior_nome(self, obj):
        return obj.status_anterior.nome if obj.status_anterior_id else None

    def get_status_novo_nome(self, obj):
        return obj.status_novo.nome if obj.status_novo_id else None

    def get_origem_label(self, obj):
        return obj.get_origem_display()


class ItemOrcamentoSerializer(serializers.ModelSerializer):
    valor_total = serializers.ReadOnlyField()
    orcamento = serializers.PrimaryKeyRelatedField(queryset=Orcamento.objects.all(), required=False)
    produto = serializers.PrimaryKeyRelatedField(
        queryset=Produto.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = ItemOrcamento
        fields = [
            'id',
            'orcamento',
            'tipo',
            'descricao',
            'quantidade',
            'valor_unitario',
            'valor_total',
            'produto',
        ]

    def validate(self, attrs):
        inst = self.instance
        tipo = attrs.get('tipo', inst.tipo if inst else None) or 'servico'
        produto_in_attrs = 'produto' in attrs

        if tipo == 'servico':
            attrs['produto'] = None
        else:
            p = attrs['produto'] if produto_in_attrs else (inst.produto if inst else None)
            if p is None:
                raise serializers.ValidationError(
                    {
                        'produto': 'Itens do tipo Produto devem referenciar um produto cadastrado. '
                        'Use o tipo Serviço para descrição livre.'
                    }
                )
            attrs['produto'] = p
            attrs.setdefault('descricao', p.descricao[:200])
            attrs.setdefault('valor_unitario', p.valor)

        if 'descricao' in attrs and attrs['descricao'] is not None:
            attrs['descricao'] = str(attrs['descricao']).strip()[:200]
        desc = attrs.get('descricao', inst.descricao if inst else '') or ''
        desc = str(desc).strip()
        p_obj = attrs.get('produto', inst.produto if inst else None)
        if tipo == 'peca' and p_obj is not None and not desc:
            attrs['descricao'] = p_obj.descricao[:200]
            desc = attrs['descricao']

        vu = attrs.get('valor_unitario', inst.valor_unitario if inst else None)
        q = attrs.get('quantidade', inst.quantidade if inst else None)
        if not desc:
            raise serializers.ValidationError({'descricao': 'Informe a descrição do item.'})
        if vu is None:
            raise serializers.ValidationError({'valor_unitario': 'Obrigatório.'})
        if q is None or int(q) < 1:
            raise serializers.ValidationError({'quantidade': 'Quantidade inválida.'})
        return attrs


class OrcamentoSerializer(serializers.ModelSerializer):
    itens = ItemOrcamentoSerializer(many=True, read_only=True)
    status_nome = serializers.SerializerMethodField()
    cliente_nome = serializers.SerializerMethodField()
    cliente_cnpj_cpf = serializers.SerializerMethodField()
    usuario_criacao_nome = serializers.SerializerMethodField()
    usuario_ultima_alteracao_nome = serializers.SerializerMethodField()
    empresa_nome = serializers.SerializerMethodField()
    empresa_razao_social = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()
    valor_desconto_calculado = serializers.SerializerMethodField()
    valor_acrescimo_calculado = serializers.SerializerMethodField()
    historico_status = serializers.SerializerMethodField()

    def get_status_nome(self, obj):
        return obj.status.nome

    def get_cliente_nome(self, obj):
        return obj.cliente.razao_social if obj.cliente else None

    def get_cliente_cnpj_cpf(self, obj):
        return obj.cliente.cnpj_cpf if obj.cliente else None

    def get_usuario_criacao_nome(self, obj):
        return usuario_exibicao(obj.usuario_criacao)

    def get_usuario_ultima_alteracao_nome(self, obj):
        return usuario_exibicao(obj.usuario_ultima_alteracao)

    def get_empresa_nome(self, obj):
        """Mesma regra do seletor de empresa no front: menu → fantasia → razão social."""
        e = obj.empresa
        if not e:
            return None
        menu = (e.nome_exibicao_menu or '').strip()
        if menu:
            return menu
        nf = (e.nome_fantasia or '').strip()
        if nf:
            return nf
        return (e.razao_social or '').strip() or None

    def get_empresa_razao_social(self, obj):
        return obj.empresa.razao_social if obj.empresa else None

    def get_subtotal(self, obj):
        return str(obj.get_subtotal())

    def get_valor_desconto_calculado(self, obj):
        return str(obj.get_valor_desconto_calculado())

    def get_valor_acrescimo_calculado(self, obj):
        return str(obj.get_valor_acrescimo_calculado())

    def get_historico_status(self, obj):
        if not self.context.get('for_detail'):
            return None
        cache = getattr(obj, '_prefetched_objects_cache', None)
        if cache and 'historicos_status' in cache:
            qs = cache['historicos_status']
        else:
            qs = obj.historicos_status.select_related(
                'usuario', 'status_anterior', 'status_novo'
            ).order_by('data_registro', 'id')
        return HistoricoStatusOrcamentoSerializer(qs, many=True).data

    class Meta:
        model = Orcamento
        fields = [
            'id',
            'numero',
            'empresa',
            'empresa_nome',
            'empresa_razao_social',
            'ativo',
            'cliente',
            'cliente_nome',
            'cliente_cnpj_cpf',
            'descricao',
            'status',
            'status_nome',
            'data_criacao',
            'data_validade',
            'subtotal',
            'desconto',
            'desconto_tipo',
            'valor_desconto_calculado',
            'acrescimo',
            'acrescimo_tipo',
            'valor_acrescimo_calculado',
            'valor_total',
            'condicoes_pagamento',
            'prazo_entrega',
            'observacoes',
            'usuario_criacao',
            'usuario_criacao_nome',
            'data_ultima_alteracao',
            'usuario_ultima_alteracao',
            'usuario_ultima_alteracao_nome',
            'itens',
            'historico_status',
        ]
        read_only_fields = [
            'numero',
            'empresa',
            'usuario_criacao',
            'data_criacao',
            'data_ultima_alteracao',
            'usuario_ultima_alteracao',
            'valor_total',
            'ativo',
        ]

    def validate_status(self, value):
        return validate_orcamento_status_fk(value, self.instance)


class ItemOrcamentoCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de itens dentro do payload de orçamento"""

    produto = serializers.PrimaryKeyRelatedField(
        queryset=Produto.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = ItemOrcamento
        fields = ['tipo', 'descricao', 'quantidade', 'valor_unitario', 'produto']

    def validate(self, attrs):
        tipo = attrs.get('tipo', 'servico')
        if tipo == 'servico':
            attrs['produto'] = None
        elif tipo == 'peca':
            p = attrs.get('produto')
            if p is None:
                raise serializers.ValidationError(
                    {
                        'produto': 'Itens do tipo Produto devem referenciar um produto cadastrado. '
                        'Use o tipo Serviço para descrição livre.'
                    }
                )
            attrs.setdefault('descricao', p.descricao[:200])
            attrs.setdefault('valor_unitario', p.valor)
        if attrs.get('descricao') is not None:
            attrs['descricao'] = str(attrs['descricao']).strip()[:200]
        desc = (attrs.get('descricao') or '').strip()
        p = attrs.get('produto')
        if tipo == 'peca' and p is not None and not desc:
            attrs['descricao'] = p.descricao[:200]
            desc = attrs['descricao']
        if not desc:
            raise serializers.ValidationError({'descricao': 'Informe a descrição do item.'})
        if attrs.get('valor_unitario') is None:
            raise serializers.ValidationError({'valor_unitario': 'Obrigatório.'})
        if attrs.get('quantidade') is None or int(attrs['quantidade']) < 1:
            raise serializers.ValidationError({'quantidade': 'Quantidade inválida.'})
        return attrs


class OrcamentoCreateSerializer(serializers.ModelSerializer):
    itens = ItemOrcamentoCreateSerializer(many=True, required=False)
    numero = serializers.CharField(required=False, read_only=True)
    desconto = serializers.DecimalField(max_digits=10, decimal_places=2, default=0, required=False)
    desconto_tipo = serializers.ChoiceField(
        choices=[('valor', 'Valor Fixo'), ('percentual', 'Percentual')], default='valor', required=False
    )
    acrescimo = serializers.DecimalField(max_digits=10, decimal_places=2, default=0, required=False)
    acrescimo_tipo = serializers.ChoiceField(
        choices=[('valor', 'Valor Fixo'), ('percentual', 'Percentual')], default='valor', required=False
    )

    class Meta:
        model = Orcamento
        fields = [
            'numero',
            'cliente',
            'descricao',
            'status',
            'data_validade',
            'desconto',
            'desconto_tipo',
            'acrescimo',
            'acrescimo_tipo',
            'condicoes_pagamento',
            'prazo_entrega',
            'observacoes',
            'itens',
        ]

    def create(self, validated_data):
        """Cria o orçamento e seus itens (número sequencial por empresa)."""
        itens_data = validated_data.pop('itens', [])
        empresa = validated_data.get('empresa')
        if not empresa:
            from rest_framework import serializers as ser

            raise ser.ValidationError({'empresa': 'Empresa é obrigatória para criar orçamento.'})
        validated_data['numero'] = Orcamento.gerar_proximo_numero(empresa)
        orcamento = Orcamento.objects.create(**validated_data)

        for item_data in itens_data:
            ItemOrcamento.objects.create(orcamento=orcamento, **item_data)

        orcamento.calcular_valor_total()

        return orcamento

    def validate_status(self, value):
        return validate_orcamento_status_fk(value)
