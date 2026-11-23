from decimal import Decimal
from pathlib import Path
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile, ZipFile

from django import forms
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

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


COLUNAS_MODELO = ("ingrediente", "unidade", "quantidade", "custo_unitario")
TAMANHO_MAXIMO = 2 * 1024 * 1024
TAMANHO_EXTRAIDO_MAXIMO = 10 * 1024 * 1024


class PlanilhaEstoqueForm(forms.Form):
    arquivo = forms.FileField(label="Planilha XLSX")

    def clean_arquivo(self):
        arquivo = self.cleaned_data["arquivo"]
        if Path(arquivo.name).suffix.lower() != ".xlsx":
            raise forms.ValidationError("Selecione um arquivo XLSX.")
        if arquivo.size > TAMANHO_MAXIMO:
            raise forms.ValidationError("O arquivo deve ter no máximo 2 MB.")

        try:
            with ZipFile(arquivo) as pacote:
                if sum(item.file_size for item in pacote.infolist()) > TAMANHO_EXTRAIDO_MAXIMO:
                    raise forms.ValidationError("A planilha excede o tamanho permitido.")
            arquivo.seek(0)
            planilha = load_workbook(arquivo, read_only=True, data_only=True, keep_links=False)
            try:
                cabecalho = next(
                    planilha.worksheets[0].iter_rows(min_row=1, max_row=1, values_only=True),
                    (),
                )
                colunas = tuple(
                    str(valor).strip().lower() if valor is not None else ""
                    for valor in cabecalho[:4]
                )
                if colunas != COLUNAS_MODELO:
                    raise forms.ValidationError(
                        "A planilha deve começar com as colunas do modelo, na mesma ordem."
                    )
            finally:
                planilha.close()
        except (
            BadZipFile,
            InvalidFileException,
            IndexError,
            KeyError,
            ValueError,
            OSError,
            ParseError,
        ) as erro:
            raise forms.ValidationError("O arquivo XLSX não pôde ser lido.") from erro
        finally:
            arquivo.seek(0)
        return arquivo
