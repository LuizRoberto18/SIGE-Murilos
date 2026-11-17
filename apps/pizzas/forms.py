from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import ItemFicha, Pizza


class PizzaForm(forms.ModelForm):
    class Meta:
        model = Pizza
        fields = ["nome", "preco_venda", "ativo"]

    def clean_nome(self):
        nome = self.cleaned_data["nome"].strip()
        if Pizza.objects.filter(nome__iexact=nome).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Já existe uma pizza com este nome.")
        return nome


class ItemFichaForm(forms.ModelForm):
    class Meta:
        model = ItemFicha
        fields = ["ingrediente", "quantidade"]


class FichaFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        usados = set()
        for form in self.forms:
            dados = form.cleaned_data
            if not dados or dados.get("DELETE"):
                continue
            ingrediente = dados.get("ingrediente")
            if ingrediente and ingrediente.pk in usados:
                raise forms.ValidationError("O mesmo ingrediente não pode aparecer duas vezes.")
            if ingrediente:
                usados.add(ingrediente.pk)


ItensFichaFormSet = inlineformset_factory(
    Pizza,
    ItemFicha,
    form=ItemFichaForm,
    formset=FichaFormSet,
    extra=1,
    can_delete=True,
)
