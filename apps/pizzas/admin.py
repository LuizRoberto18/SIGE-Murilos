from django.contrib import admin

from .models import ItemFicha, Pizza


class ItemFichaInline(admin.TabularInline):
    model = ItemFicha
    extra = 1


@admin.register(Pizza)
class PizzaAdmin(admin.ModelAdmin):
    list_display = ("nome", "preco_venda", "ativo", "criado_em")
    search_fields = ("nome",)
    list_filter = ("ativo",)
    ordering = ("nome",)
    inlines = (ItemFichaInline,)


@admin.register(ItemFicha)
class ItemFichaAdmin(admin.ModelAdmin):
    list_display = ("pizza", "ingrediente", "quantidade")
    search_fields = ("pizza__nome", "ingrediente__nome")
    list_filter = ("pizza",)
    ordering = ("pizza__nome", "ingrediente__nome")
