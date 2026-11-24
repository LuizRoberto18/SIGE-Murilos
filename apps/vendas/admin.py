from django.contrib import admin

from .models import RegistroVenda


@admin.register(RegistroVenda)
class RegistroVendaAdmin(admin.ModelAdmin):
    list_display = ("tipo", "data_inicio", "data_fim", "total_pedidos", "usuario")
    search_fields = ("usuario__email",)
    list_filter = ("tipo", "data_inicio")
    ordering = ("-data_inicio",)
    readonly_fields = ("usuario", "criado_em", "atualizado_em")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)
