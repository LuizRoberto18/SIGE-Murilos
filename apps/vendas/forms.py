from django import forms
from django.forms import inlineformset_factory

from apps.pizzas.models import Pizza

from .models import ItemVenda, RegistroVenda


class RegistroVendaForm(forms.ModelForm):
    class Meta:
        model = RegistroVenda
        fields = ["tipo", "data_inicio", "data_fim", "total_pedidos"]
        widgets = {
            "data_inicio": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "data_fim": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }


class ItemVendaForm(forms.ModelForm):
    class Meta:
        model = ItemVenda
        fields = ["pizza", "quantidade"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["pizza"].queryset = Pizza.objects.filter(
            ativo=True, itens_ficha__isnull=False
        ).distinct()


ItensVendaFormSet = inlineformset_factory(
    RegistroVenda,
    ItemVenda,
    form=ItemVendaForm,
    extra=1,
    can_delete=True,
)
