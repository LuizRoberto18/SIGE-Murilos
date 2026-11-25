from django import forms

from .models import RegistroVenda


class RegistroVendaForm(forms.ModelForm):
    class Meta:
        model = RegistroVenda
        fields = ["tipo", "data_inicio", "data_fim", "total_pedidos"]
        widgets = {
            "data_inicio": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "data_fim": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }
