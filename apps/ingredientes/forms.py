from decimal import Decimal

from django import forms

from .models import Ingrediente


class IngredienteForm(forms.ModelForm):
    class Meta:
        model = Ingrediente
        fields = [
            "nome",
            "unidade",
            "quantidade_estoque",
            "custo_unitario",
            "estoque_minimo",
            "ativo",
        ]

    def clean_nome(self):
        nome = self.cleaned_data["nome"].strip()
        duplicado = Ingrediente.objects.filter(nome__iexact=nome).exclude(pk=self.instance.pk)
        if duplicado.exists():
            raise forms.ValidationError("Já existe um ingrediente com este nome.")
        return nome

    def clean_quantidade_estoque(self):
        quantidade = self.cleaned_data["quantidade_estoque"]
        if quantidade < Decimal("0") and (
            self.instance.pk is None or quantidade != self.instance.quantidade_estoque
        ):
            raise forms.ValidationError("A quantidade informada manualmente não pode ser negativa.")
        return quantidade
