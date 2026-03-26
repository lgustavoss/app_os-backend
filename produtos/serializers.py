from rest_framework import serializers

from .models import EstoqueProdutoEmpresa, MovimentacaoEstoque, Produto


class ProdutoSerializer(serializers.ModelSerializer):
    saldo_estoque = serializers.DecimalField(
        max_digits=12, decimal_places=3, required=False, default=0
    )

    class Meta:
        model = Produto
        fields = ['codigo', 'descricao', 'valor', 'saldo_estoque']
        read_only_fields = ['codigo']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        empresa = self.context.get('empresa_atual')
        saldo = '0.000'
        if empresa is not None:
            estoque = (
                EstoqueProdutoEmpresa.objects.filter(empresa=empresa, produto=instance)
                .values_list('saldo', flat=True)
                .first()
            )
            if estoque is not None:
                saldo = f'{estoque:.3f}'
        data['saldo_estoque'] = saldo
        return data

    def create(self, validated_data):
        validated_data.pop('saldo_estoque', None)
        validated_data['codigo'] = Produto.proximo_codigo()
        return super().create(validated_data)


class MovimentacaoEstoqueSerializer(serializers.ModelSerializer):
    produto_descricao = serializers.CharField(source='produto.descricao', read_only=True)
    orcamento_numero = serializers.CharField(source='orcamento.numero', read_only=True)

    class Meta:
        model = MovimentacaoEstoque
        fields = [
            'id',
            'produto',
            'produto_descricao',
            'empresa',
            'tipo',
            'origem',
            'quantidade',
            'saldo_anterior',
            'saldo_posterior',
            'observacao',
            'orcamento',
            'orcamento_numero',
            'status_orcamento',
            'usuario',
            'data_registro',
        ]
        read_only_fields = fields


class MovimentacaoEstoqueInputSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(
        choices=[
            MovimentacaoEstoque.Tipo.ENTRADA,
            MovimentacaoEstoque.Tipo.SAIDA,
            MovimentacaoEstoque.Tipo.AJUSTE,
        ]
    )
    quantidade = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=0.001)
    observacao = serializers.CharField(required=False, allow_blank=True, max_length=255)
