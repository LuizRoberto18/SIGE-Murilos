from django.contrib import admin

from .models import Importacao, Ingrediente, ItemImportacao


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


class ItemImportacaoInline(admin.TabularInline):
    model = ItemImportacao
    extra = 0
    can_delete = False
    readonly_fields = (
        "ingrediente",
        "nome_ingrediente",
        "unidade",
        "quantidade",
        "custo_unitario",
        "saldo_anterior",
        "saldo_posterior",
        "custo_anterior",
        "custo_posterior",
    )

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Importacao)
class ImportacaoAdmin(admin.ModelAdmin):
    list_display = ("id", "tipo", "nome_arquivo", "usuario", "repeticao_autorizada", "criado_em")
    search_fields = ("nome_arquivo", "usuario__email")
    list_filter = ("tipo", "repeticao_autorizada", "criado_em")
    ordering = ("-criado_em",)
    readonly_fields = (
        "identificador",
        "hash_conteudo",
        "repeticao_autorizada",
        "tipo",
        "usuario",
        "nome_arquivo",
        "criado_em",
    )
    inlines = (ItemImportacaoInline,)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ItemImportacao)
class ItemImportacaoAdmin(admin.ModelAdmin):
    list_display = (
        "importacao",
        "nome_ingrediente",
        "quantidade",
        "saldo_anterior",
        "saldo_posterior",
    )
    search_fields = ("nome_ingrediente", "importacao__nome_arquivo")
    list_filter = ("importacao__tipo",)
    ordering = ("-importacao__criado_em",)
    readonly_fields = (
        "importacao",
        "ingrediente",
        "nome_ingrediente",
        "unidade",
        "quantidade",
        "custo_unitario",
        "saldo_anterior",
        "saldo_posterior",
        "custo_anterior",
        "custo_posterior",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
