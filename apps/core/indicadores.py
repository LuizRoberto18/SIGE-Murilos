"""Indicadores de vendas calculados a partir dos valores históricos."""

from calendar import monthrange
from collections import defaultdict
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Prefetch

from apps.vendas.models import ItemVenda, RegistroVenda
from apps.vendas.periodos import fator_sobreposicao


def intervalo_filtro(granularidade, referencia):
    if granularidade == "SEMANA":
        inicio = referencia - timedelta(days=referencia.weekday())
        return inicio, inicio + timedelta(days=6)
    if granularidade == "MES":
        inicio = referencia.replace(day=1)
        return inicio, referencia.replace(day=monthrange(referencia.year, referencia.month)[1])
    return referencia, referencia


def _arredondar(valor, casas="0.01"):
    return valor.quantize(Decimal(casas), rounding=ROUND_HALF_UP)


def calcular_indicadores(granularidade, referencia):
    inicio, fim = intervalo_filtro(granularidade, referencia)
    periodos = list(
        RegistroVenda.objects.filter(data_inicio__lte=fim, data_fim__gte=inicio)
        .select_related("usuario")
        .prefetch_related(
            Prefetch("itens_venda", queryset=ItemVenda.objects.select_related("pizza"))
        )
    )
    pedidos = Decimal("0")
    faturamento = Decimal("0")
    custo = Decimal("0")
    produtos = defaultdict(
        lambda: {
            "pizza": None,
            "quantidade": Decimal("0"),
            "faturamento": Decimal("0"),
            "custo": Decimal("0"),
        }
    )
    medias_diarias = False
    valores_proporcionais = False

    for periodo in periodos:
        fator = fator_sobreposicao(periodo, inicio, fim)
        dias_periodo = (periodo.data_fim - periodo.data_inicio).days + 1
        pedidos += Decimal(periodo.total_pedidos) * fator
        valores_proporcionais = valores_proporcionais or fator != 1
        medias_diarias = medias_diarias or (
            granularidade == "DIA" and (periodo.tipo != RegistroVenda.Tipo.DIA or dias_periodo > 1)
        )
        for item in periodo.itens_venda.all():
            quantidade = Decimal(item.quantidade) * fator
            receita_item = Decimal(item.quantidade) * item.preco_unitario * fator
            custo_item = Decimal(item.quantidade) * item.custo_unitario * fator
            faturamento += receita_item
            custo += custo_item
            produto = produtos[item.pizza_id]
            produto["pizza"] = item.pizza
            produto["quantidade"] += quantidade
            produto["faturamento"] += receita_item
            produto["custo"] += custo_item

    lucro = faturamento - custo
    mais_vendidos = []
    for produto in produtos.values():
        lucro_produto = produto["faturamento"] - produto["custo"]
        margem = Decimal("0")
        if produto["faturamento"] > 0:
            margem = lucro_produto / produto["faturamento"] * 100
        mais_vendidos.append(
            {
                "pizza": produto["pizza"],
                "quantidade": _arredondar(produto["quantidade"]),
                "faturamento": _arredondar(produto["faturamento"]),
                "lucro": _arredondar(lucro_produto),
                "margem": _arredondar(margem),
            }
        )
    mais_vendidos.sort(
        key=lambda item: (
            -item["quantidade"],
            -item["faturamento"],
            item["pizza"].nome.casefold(),
        )
    )
    return {
        "inicio": inicio,
        "fim": fim,
        "pedidos": _arredondar(pedidos),
        "faturamento": _arredondar(faturamento),
        "custo": _arredondar(custo),
        "lucro": _arredondar(lucro),
        "mais_vendidos": mais_vendidos[:5],
        "periodos_considerados": len(periodos),
        "medias_diarias": medias_diarias,
        "valores_proporcionais": valores_proporcionais,
    }
