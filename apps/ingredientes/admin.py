from django.contrib import admin

from .models import Ingrediente


@admin.register(Ingrediente)
class IngredienteAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "unidade",
        "quantidade_estoque",
        "custo_unitario",
        "estoque_minimo",
        "ativo",
    )
    search_fields = ("nome",)
    list_filter = ("unidade", "ativo")
    ordering = ("nome",)
