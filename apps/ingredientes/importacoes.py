"""Aplicação atômica das planilhas confirmadas."""

import json
from decimal import ROUND_HALF_UP, Decimal
from hashlib import sha256

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Importacao, Ingrediente, ItemImportacao


class ErroImportacao(Exception):
    """A planilha não pode mais ser aplicada ao estado atual do estoque."""


def hash_importacao(pendente, tipo):
    """Identifica tipo e valores normalizados, independentemente da ordem das linhas."""
    linhas = [
        {
            "nome": linha["nome"].casefold(),
            "unidade": linha["unidade"],
            "quantidade": str(Decimal(linha["quantidade"]).normalize()),
            "custo": str(Decimal(linha["custo_unitario"]).normalize()),
        }
        for linha in pendente["linhas"]
    ]
    dados = json.dumps(
        {"tipo": tipo, "linhas": sorted(linhas, key=lambda linha: linha["nome"])},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(dados.encode("utf-8")).hexdigest()


def _atualizar_saldo(ingrediente, quantidade, custo, tipo, novo):
    anterior = ingrediente.quantidade_estoque
    custo_anterior = ingrediente.custo_unitario

    if tipo == Importacao.Tipo.CONTAGEM:
        saldo = quantidade
        custo_atual = custo
    else:
        saldo = anterior + quantidade
        if novo or anterior <= 0:
            custo_atual = custo if quantidade > 0 or novo else custo_anterior
        elif quantidade > 0:
            custo_atual = ((anterior * custo_anterior + quantidade * custo) / saldo).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )
        else:
            custo_atual = custo_anterior

    ingrediente.quantidade_estoque = saldo
    ingrediente.custo_unitario = custo_atual
    try:
        ingrediente.full_clean()
    except ValidationError as erro:
        raise ErroImportacao(
            f"Os valores de {ingrediente.nome} não cabem no cadastro de estoque."
        ) from erro
    ingrediente.save()
    return anterior, custo_anterior


@transaction.atomic
def aplicar_importacao(pendente, tipo, usuario, repetir=False):
    """Grava a importação e seus itens uma única vez, junto com os novos saldos."""
    importacao = Importacao.objects.create(
        identificador=pendente["token"],
        hash_conteudo=hash_importacao(pendente, tipo),
        repeticao_autorizada=repetir,
        tipo=tipo,
        usuario=usuario,
        nome_arquivo=pendente["arquivo"],
    )
    for linha in pendente["linhas"]:
        nome = linha["nome"]
        unidade = linha["unidade"]
        quantidade = Decimal(linha["quantidade"])
        custo = Decimal(linha["custo_unitario"])
        ingrediente = Ingrediente.objects.select_for_update().filter(nome__iexact=nome).first()
        novo = ingrediente is None
        if novo:
            ingrediente = Ingrediente(
                nome=nome, unidade=unidade, quantidade_estoque=0, custo_unitario=0
            )
        elif ingrediente.unidade != unidade:
            raise ErroImportacao(
                f"A unidade de {nome} mudou desde a prévia. Envie a planilha novamente."
            )

        saldo_anterior, custo_anterior = _atualizar_saldo(
            ingrediente, quantidade, custo, tipo, novo
        )
        ItemImportacao.objects.create(
            importacao=importacao,
            ingrediente=ingrediente,
            nome_ingrediente=ingrediente.nome,
            unidade=unidade,
            quantidade=quantidade,
            custo_unitario=custo,
            saldo_anterior=saldo_anterior,
            saldo_posterior=ingrediente.quantidade_estoque,
            custo_anterior=custo_anterior,
            custo_posterior=ingrediente.custo_unitario,
        )
    return importacao
