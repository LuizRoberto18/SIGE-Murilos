"""Cálculos compartilhados para intervalos de registros de venda."""

from decimal import Decimal


def fator_sobreposicao(periodo, inicio, fim):
    inicio_sobreposto = max(periodo.data_inicio, inicio)
    fim_sobreposto = min(periodo.data_fim, fim)
    dias_sobrepostos = (fim_sobreposto - inicio_sobreposto).days + 1
    dias_periodo = (periodo.data_fim - periodo.data_inicio).days + 1
    return Decimal(dias_sobrepostos) / Decimal(dias_periodo)
