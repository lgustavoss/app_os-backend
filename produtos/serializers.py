from rest_framework import serializers

from .models import Produto


class ProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produto
        fields = ['codigo', 'descricao', 'valor']
        read_only_fields = ['codigo']

    def create(self, validated_data):
        validated_data['codigo'] = Produto.proximo_codigo()
        return super().create(validated_data)
