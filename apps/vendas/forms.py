from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone

from apps.pizzas.models import Pizza

from .models import ItemVenda, RegistroVenda


def inicio_mes_atual():
    return timezone.localdate().replace(day=1)


class ConsumoFiltroForm(forms.Form):
    data_inicio = forms.DateField(
        label="Data inicial",
        initial=inicio_mes_atual,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
    )
    data_fim = forms.DateField(
        label="Data final",
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
    )

    def clean(self):
        dados = super().clean()
        inicio = dados.get("data_inicio")
        fim = dados.get("data_fim")
        if inicio and fim and inicio > fim:
            self.add_error("data_fim", "A data final deve ser igual ou posterior à inicial.")
        return dados


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
