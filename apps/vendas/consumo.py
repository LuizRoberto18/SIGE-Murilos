"""Consumo de ingredientes calculado pelas movimentações de venda."""

from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Prefetch

from .models import Movimentacao, RegistroVenda
from .periodos import fator_sobreposicao


def _arredondar(valor, casas):
    return valor.quantize(Decimal(casas), rounding=ROUND_HALF_UP)


def calcular_consumo(inicio, fim):
    periodos = list(
        RegistroVenda.objects.filter(data_inicio__lte=fim, data_fim__gte=inicio).prefetch_related(
            Prefetch(
                "movimentacoes",
                queryset=Movimentacao.objects.select_related("ingrediente"),
            )
        )
    )
    pedidos = Decimal("0")
    totais = defaultdict(Decimal)
    ingredientes = {}
    valores_proporcionais = False

    for periodo in periodos:
        fator = fator_sobreposicao(periodo, inicio, fim)
        pedidos += Decimal(periodo.total_pedidos) * fator
        valores_proporcionais = valores_proporcionais or fator != 1
        for movimento in periodo.movimentacoes.all():
            sinal = Decimal("1") if movimento.tipo == Movimentacao.Tipo.BAIXA else Decimal("-1")
            totais[movimento.ingrediente_id] += movimento.quantidade * sinal * fator
            ingredientes[movimento.ingrediente_id] = movimento.ingrediente

    itens = []
    for ingrediente_id, total in totais.items():
        if total <= 0:
            continue
        media = total / pedidos if pedidos > 0 else Decimal("0")
        itens.append(
            {
                "ingrediente": ingredientes[ingrediente_id],
                "total": _arredondar(total, "0.001"),
                "media_pedido": _arredondar(media, "0.001"),
            }
        )
    itens.sort(key=lambda item: (-item["total"], item["ingrediente"].nome.casefold()))
    return {
        "inicio": inicio,
        "fim": fim,
        "pedidos": _arredondar(pedidos, "0.01"),
        "itens": itens,
        "periodos_considerados": len(periodos),
        "valores_proporcionais": valores_proporcionais,
    }
