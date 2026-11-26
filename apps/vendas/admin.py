from django.contrib import admin

from .forms import ItemVendaForm
from .models import ItemVenda, RegistroVenda


class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    form = ItemVendaForm
    extra = 1


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
    list_display = ("registro", "pizza", "quantidade")
    search_fields = ("pizza__nome", "registro__usuario__email")
    list_filter = ("registro__tipo",)
    ordering = ("-registro__data_inicio", "pizza__nome")
    form = ItemVendaForm
