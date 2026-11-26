from django.contrib import admin

from .models import ItemVenda, Movimentacao, RegistroVenda


class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 0
    can_delete = False
    readonly_fields = ("pizza", "quantidade", "preco_unitario", "custo_unitario")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(RegistroVenda)
class RegistroVendaAdmin(admin.ModelAdmin):
    list_display = ("tipo", "data_inicio", "data_fim", "total_pedidos", "usuario")
    search_fields = ("usuario__email",)
    list_filter = ("tipo", "data_inicio")
    ordering = ("-data_inicio",)
    readonly_fields = ("usuario", "criado_em", "atualizado_em")
    inlines = (ItemVendaInline,)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)


@admin.register(ItemVenda)
class ItemVendaAdmin(admin.ModelAdmin):
    list_display = (
        "registro",
        "pizza",
        "quantidade",
        "preco_unitario",
        "custo_unitario",
    )
    search_fields = ("pizza__nome", "registro__usuario__email")
    list_filter = ("registro__tipo",)
    ordering = ("-registro__data_inicio", "pizza__nome")
    readonly_fields = ("registro", "pizza", "quantidade", "preco_unitario", "custo_unitario")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = (
        "tipo",
        "registro",
        "ingrediente",
        "quantidade",
        "saldo_anterior",
        "saldo_posterior",
        "versao",
        "criado_em",
    )
    search_fields = ("ingrediente__nome", "registro__usuario__email", "usuario__email")
    list_filter = ("tipo", "criado_em")
    ordering = ("-criado_em", "-pk")
    readonly_fields = (
        "registro",
        "ingrediente",
        "usuario",
        "tipo",
        "versao",
        "quantidade",
        "custo_unitario",
        "saldo_anterior",
        "saldo_posterior",
        "criado_em",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
