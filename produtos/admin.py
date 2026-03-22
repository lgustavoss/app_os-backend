from django.contrib import admin

from .models import Produto


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descricao', 'valor')
    search_fields = ('descricao',)
    readonly_fields = ('codigo',)
