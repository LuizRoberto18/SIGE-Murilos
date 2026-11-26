from django import forms
from django.utils import timezone

from apps.ingredientes.models import Importacao, Ingrediente
from apps.vendas.models import Movimentacao


class IndicadorFiltroForm(forms.Form):
    data_inicio = forms.DateField(
        label="De",
        initial=lambda: timezone.localdate().replace(day=1),
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
    )
    data_fim = forms.DateField(
        label="Até",
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


class MovimentoFiltroForm(forms.Form):
    origem = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Todas as origens"),
            *Importacao.Tipo.choices,
            *Movimentacao.Tipo.choices,
        ],
    )
    ingrediente = forms.ModelChoiceField(
        required=False,
        queryset=Ingrediente.objects.all(),
        empty_label="Todos os ingredientes",
    )
    data_inicio = forms.DateField(
        required=False,
        label="Data inicial",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    data_fim = forms.DateField(
        required=False,
        label="Data final",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )

    def clean(self):
        dados = super().clean()
        inicio = dados.get("data_inicio")
        fim = dados.get("data_fim")
        if inicio and fim and inicio > fim:
            self.add_error("data_fim", "A data final deve ser igual ou posterior à inicial.")
        return dados
