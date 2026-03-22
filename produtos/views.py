from django.db.models import Q
from django.db.models.deletion import ProtectedError
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from autenticacao.permissions_modulos import ProdutoModulePermission
from .models import Produto
from .serializers import ProdutoSerializer


class ProdutoViewSet(viewsets.ModelViewSet):
    """CRUD de produtos do catálogo global."""

    permission_classes = [IsAuthenticated, ProdutoModulePermission]
    serializer_class = ProdutoSerializer
    queryset = Produto.objects.all().order_by('codigo')
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {
                    'erro': 'Não é possível excluir: existem itens de orçamento vinculados a este produto.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def get_queryset(self):
        qs = super().get_queryset()
        q = (self.request.query_params.get('search') or '').strip()
        if q:
            if q.isdigit():
                cod = int(q)
                qs = qs.filter(Q(descricao__icontains=q) | Q(codigo=cod))
            else:
                qs = qs.filter(descricao__icontains=q)
        return qs
