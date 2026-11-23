"""Leitura e prévia de planilhas de estoque, sem alterar o banco."""

import csv
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from io import StringIO
from zipfile import ZipFile

from openpyxl import load_workbook

from .models import Ingrediente

COLUNAS = ("ingrediente", "unidade", "quantidade", "custo_unitario")
UNIDADES_BASE = {"G", "ML", "UN"}
CONVERSOES = {"KG": "G", "L": "ML"}
MAX_LINHAS = 5000


def _extrair_linhas(linhas):
    try:
        cabecalho = next(linhas)
    except StopIteration as erro:
        raise ValueError("A planilha está vazia.") from erro

    nomes = [str(campo).strip().lower() if campo is not None else "" for campo in cabecalho]
    faltantes = [campo for campo in COLUNAS if nomes.count(campo) != 1]
    if faltantes:
        raise ValueError(
            "Colunas obrigatórias ausentes ou repetidas: " + ", ".join(faltantes) + "."
        )

    indices = {campo: nomes.index(campo) for campo in COLUNAS}
    registros = []
    for numero, linha in enumerate(linhas, start=2):
        if not any(valor is not None and str(valor).strip() for valor in linha):
            continue
        if len(registros) >= MAX_LINHAS:
            raise ValueError(f"A planilha pode ter no máximo {MAX_LINHAS} linhas preenchidas.")
        registros.append(
            (
                numero,
                {
                    campo: linha[indice] if indice < len(linha) else None
                    for campo, indice in indices.items()
                },
            )
        )
    return registros


def _ler_csv(arquivo):
    conteudo = arquivo.read()
    try:
        texto = conteudo.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = conteudo.decode("cp1252")

    # CSVs exportados por planilhas brasileiras costumam usar ponto e vírgula.
    separador = ";"
    linhas_texto = texto.splitlines()
    primeira_linha = linhas_texto[0] if linhas_texto else ""
    if primeira_linha.count(",") > primeira_linha.count(";"):
        separador = ","
    leitor = csv.reader(StringIO(texto, newline=""), delimiter=separador, strict=True)
    return _extrair_linhas(iter(leitor))


def _ler_xlsx(arquivo):
    with ZipFile(arquivo) as pacote:
        if sum(item.file_size for item in pacote.infolist()) > 10 * 1024 * 1024:
            raise ValueError("A planilha excede o tamanho permitido.")
    arquivo.seek(0)
    planilha = load_workbook(arquivo, read_only=True, data_only=True, keep_links=False)
    try:
        return _extrair_linhas(iter(planilha.worksheets[0].iter_rows(values_only=True)))
    finally:
        planilha.close()


def _numero(valor):
    if valor is None or isinstance(valor, bool):
        return None
    texto = str(valor).strip().replace(",", ".")
    if not texto:
        return None
    try:
        numero = Decimal(texto)
    except InvalidOperation:
        return None
    return numero if numero.is_finite() and 0 <= numero < Decimal("1e12") else None


def _cabe_no_campo(numero, casas, digitos):
    if numero is None:
        return False
    passo = Decimal(1).scaleb(-casas)
    try:
        return numero == numero.quantize(passo) and numero < Decimal(10) ** (digitos - casas)
    except InvalidOperation:
        return False


def analisar_planilha(arquivo, extensao):
    """Retorna linhas de prévia e totais; não salva ingredientes ou arquivos."""
    try:
        registros = _ler_xlsx(arquivo) if extensao == ".xlsx" else _ler_csv(arquivo)
    finally:
        arquivo.seek(0)

    existentes = {item.nome.casefold(): item for item in Ingrediente.objects.all()}
    encontrados = set()
    linhas = []
    for numero, dados in registros:
        nome = str(dados["ingrediente"] or "").strip()
        unidade = str(dados["unidade"] or "").strip().upper()
        quantidade = _numero(dados["quantidade"])
        custo = _numero(dados["custo_unitario"])
        erros = []

        if not nome:
            erros.append("Informe o ingrediente.")
        elif len(nome) > 120:
            erros.append("Nome com mais de 120 caracteres.")
        elif nome.casefold() in encontrados:
            erros.append("Ingrediente repetido na planilha.")
        encontrados.add(nome.casefold())

        base = CONVERSOES.get(unidade, unidade)
        if unidade not in UNIDADES_BASE | CONVERSOES.keys():
            erros.append("Unidade inválida: use G, ML, UN, KG ou L.")
        existente = existentes.get(nome.casefold())
        if existente and base in UNIDADES_BASE and existente.unidade != base:
            erros.append(f"Unidade diferente do cadastro ({existente.unidade}).")
        if quantidade is None:
            erros.append("Quantidade inválida: informe um número não negativo.")
        if custo is None:
            erros.append("Custo inválido: informe um número não negativo.")

        convertido = unidade in CONVERSOES
        quantidade_base = quantidade * 1000 if quantidade is not None and convertido else quantidade
        custo_base = custo / 1000 if custo is not None and convertido else custo
        if custo_base is not None and convertido:
            try:
                custo_base = custo_base.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            except InvalidOperation:
                custo_base = None
        if quantidade is not None and not _cabe_no_campo(quantidade_base, 3, 12):
            erros.append("Quantidade excede a precisão ou o limite do estoque.")
        if custo is not None and not _cabe_no_campo(custo_base, 4, 12):
            erros.append("Custo excede a precisão ou o limite do cadastro.")

        linhas.append(
            {
                "numero": numero,
                "nome": nome,
                "unidade": unidade,
                "quantidade": dados["quantidade"],
                "custo": dados["custo_unitario"],
                "unidade_base": base if base in UNIDADES_BASE else "",
                "quantidade_base": quantidade_base,
                "custo_base": custo_base,
                "conversao": f"{unidade} → {base}; custo ÷ 1000" if convertido else "—",
                "situacao": "Cadastrado" if existente else "Novo",
                "erros": erros,
            }
        )

    return {
        "linhas": linhas,
        "validas": sum(not linha["erros"] for linha in linhas),
        "invalidas": sum(bool(linha["erros"]) for linha in linhas),
        "novos": sum(linha["situacao"] == "Novo" and not linha["erros"] for linha in linhas),
    }
