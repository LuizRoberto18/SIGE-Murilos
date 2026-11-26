import csv
from decimal import Decimal
from pathlib import Path
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

from django import forms
from openpyxl.utils.exceptions import InvalidFileException

from .models import Importacao, Ingrediente
from .planilhas import analisar_planilha


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


TAMANHO_MAXIMO = 2 * 1024 * 1024


class PlanilhaEstoqueForm(forms.Form):
    arquivo = forms.FileField(
        label="Planilha XLSX ou CSV",
        widget=forms.ClearableFileInput(attrs={"accept": ".xlsx,.csv"}),
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data["arquivo"]
        extensao = Path(arquivo.name).suffix.lower()
        if extensao not in (".xlsx", ".csv"):
            raise forms.ValidationError("Selecione um arquivo XLSX ou CSV.")
        if arquivo.size > TAMANHO_MAXIMO:
            raise forms.ValidationError("O arquivo deve ter no máximo 2 MB.")

        try:
            self.previa = analisar_planilha(arquivo, extensao)
        except ValueError as erro:
            raise forms.ValidationError(str(erro)) from erro
        except (
            BadZipFile,
            csv.Error,
            InvalidFileException,
            IndexError,
            KeyError,
            OSError,
            ParseError,
            UnicodeError,
        ) as erro:
            raise forms.ValidationError(
                f"O arquivo {extensao[1:].upper()} não pôde ser lido."
            ) from erro
        return arquivo


class ConfirmarImportacaoForm(forms.Form):
    token = forms.UUIDField(widget=forms.HiddenInput)
    tipo = forms.ChoiceField(
        label="Tipo de atualização",
        choices=Importacao.Tipo.choices,
        widget=forms.RadioSelect,
    )
    repetir = forms.BooleanField(
        required=False,
        label="Confirmo que quero registrar novamente uma planilha com os mesmos dados",
    )


class SugestaoCompraForm(forms.Form):
    dias_cobertura = forms.IntegerField(
        label="Dias de cobertura",
        min_value=1,
        max_value=365,
        initial=7,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 365}),
    )
