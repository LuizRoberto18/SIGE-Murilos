"""Consulta unificada das alterações de estoque."""

from django.urls import reverse

from apps.ingredientes.models import Importacao, ItemImportacao
from apps.vendas.models import Movimentacao


def _filtrar_data(queryset, campo, inicio, fim):
    if inicio:
        queryset = queryset.filter(**{f"{campo}__date__gte": inicio})
    if fim:
        queryset = queryset.filter(**{f"{campo}__date__lte": fim})
    return queryset


def consultar_movimentacoes(filtros):
    origem = filtros.get("origem")
    ingrediente = filtros.get("ingrediente")
    inicio = filtros.get("data_inicio")
    fim = filtros.get("data_fim")

    importacoes = ItemImportacao.objects.select_related("importacao__usuario", "ingrediente")
    vendas = Movimentacao.objects.select_related("registro", "usuario", "ingrediente")
    if ingrediente:
        importacoes = importacoes.filter(ingrediente=ingrediente)
        vendas = vendas.filter(ingrediente=ingrediente)
    importacoes = _filtrar_data(importacoes, "importacao__criado_em", inicio, fim)
    vendas = _filtrar_data(vendas, "criado_em", inicio, fim)

    if origem in Importacao.Tipo.values:
        importacoes = importacoes.filter(importacao__tipo=origem)
        vendas = vendas.none()
    elif origem in Movimentacao.Tipo.values:
        vendas = vendas.filter(tipo=origem)
        importacoes = importacoes.none()

    registros = [
        {
            "data": item.importacao.criado_em,
            "usuario": item.importacao.usuario.email,
            "origem": item.importacao.get_tipo_display(),
            "origem_id": f"Importação #{item.importacao_id}",
            "origem_url": reverse("ingredientes:detalhe_importacao", args=[item.importacao_id]),
            "ingrediente": item.nome_ingrediente,
            "unidade": item.unidade,
            "diferenca": item.saldo_posterior - item.saldo_anterior,
            "saldo_anterior": item.saldo_anterior,
            "saldo_posterior": item.saldo_posterior,
        }
        for item in importacoes
    ]
    registros.extend(
        {
            "data": movimento.criado_em,
            "usuario": movimento.usuario.email,
            "origem": movimento.get_tipo_display(),
            "origem_id": f"Venda #{movimento.registro_id} · versão {movimento.versao}",
            "origem_url": reverse("vendas:pizzas", args=[movimento.registro_id]),
            "ingrediente": movimento.ingrediente.nome,
            "unidade": movimento.ingrediente.unidade,
            "diferenca": movimento.saldo_posterior - movimento.saldo_anterior,
            "saldo_anterior": movimento.saldo_anterior,
            "saldo_posterior": movimento.saldo_posterior,
        }
        for movimento in vendas
    )
    return sorted(registros, key=lambda registro: registro["data"], reverse=True)
