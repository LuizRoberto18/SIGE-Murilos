"""Cálculo das sugestões de reposição do estoque."""

from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import F, Sum

from apps.vendas.models import Movimentacao, RegistroVenda

from .models import Ingrediente


def _dias_historico():
    return sum(
        (fim - inicio).days + 1
        for inicio, fim in RegistroVenda.objects.values_list("data_inicio", "data_fim")
    )


def _consumos():
    totais = defaultdict(Decimal)
    movimentos = Movimentacao.objects.values("ingrediente_id", "tipo").annotate(
        total=Sum("quantidade")
    )
    for movimento in movimentos:
        sinal = Decimal("1") if movimento["tipo"] == Movimentacao.Tipo.BAIXA else Decimal("-1")
        totais[movimento["ingrediente_id"]] += sinal * movimento["total"]
    return totais


def calcular_sugestoes(dias_cobertura):
    dias_historico = _dias_historico()
    consumos = _consumos()
    ingredientes = Ingrediente.objects.filter(ativo=True).order_by("nome")
    total_criticos = ingredientes.filter(quantidade_estoque__lte=F("estoque_minimo")).count()
    sugestoes = []
    for ingrediente in ingredientes:
        consumo_total = max(consumos[ingrediente.pk], Decimal("0"))
        consumo_medio = consumo_total / Decimal(dias_historico) if dias_historico else Decimal("0")
        quantidade = (
            consumo_medio * Decimal(dias_cobertura)
            + ingrediente.estoque_minimo
            - ingrediente.quantidade_estoque
        ).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        if quantidade <= 0:
            continue
        sugestoes.append(
            {
                "ingrediente": ingrediente,
                "consumo_medio": consumo_medio.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP),
                "quantidade": quantidade,
                "critico": ingrediente.estoque_baixo,
            }
        )
    sugestoes.sort(key=lambda item: (not item["critico"], -item["quantidade"]))
    return {
        "sugestoes": sugestoes,
        "dias_historico": dias_historico,
        "total_criticos": total_criticos,
    }
