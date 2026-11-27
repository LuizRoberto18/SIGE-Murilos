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
    return _calcular_indicadores(
        inicio,
        fim,
        granularidade=granularidade,
        consulta_dia=granularidade == "DIA",
    )


def calcular_indicadores_intervalo(inicio, fim):
    return _calcular_indicadores(
        inicio,
        fim,
        granularidade="INTERVALO",
        consulta_dia=inicio == fim,
    )


def _construir_serie_temporal(periodos, inicio, fim, maximo_pontos=12):
    """Distribui os registros históricos em até 12 blocos comparáveis."""
    total_dias = (fim - inicio).days + 1
    dias_por_bloco = max(1, (total_dias + maximo_pontos - 1) // maximo_pontos)
    serie = []
    cursor = inicio

    while cursor <= fim:
        fim_bloco = min(cursor + timedelta(days=dias_por_bloco - 1), fim)
        faturamento = Decimal("0")
        custo = Decimal("0")

        for periodo in periodos:
            if periodo.data_inicio > fim_bloco or periodo.data_fim < cursor:
                continue
            fator = fator_sobreposicao(periodo, cursor, fim_bloco)
            for item in periodo.itens_venda.all():
                faturamento += Decimal(item.quantidade) * item.preco_unitario * fator
                custo += Decimal(item.quantidade) * item.custo_unitario * fator

        serie.append(
            {
                "inicio": cursor,
                "fim": fim_bloco,
                "rotulo": (
                    cursor.strftime("%d/%m")
                    if cursor == fim_bloco
                    else f"{cursor:%d/%m}\u2013{fim_bloco:%d/%m}"
                ),
                "faturamento": _arredondar(faturamento),
                "custo": _arredondar(custo),
                "lucro": _arredondar(faturamento - custo),
            }
        )
        cursor = fim_bloco + timedelta(days=1)

    maior_valor = max(
        (max(ponto["faturamento"], ponto["custo"]) for ponto in serie),
        default=Decimal("0"),
    )
    for ponto in serie:
        for campo in ("faturamento", "custo"):
            valor = ponto[campo]
            altura = int(valor / maior_valor * 100) if maior_valor else 0
            ponto[f"{campo}_altura"] = max(4, altura) if valor else 0

    return serie


def _construir_curva_abc(produtos):
    """Classifica pizzas pelo faturamento acumulado nos cortes 80/95/100."""
    faixas = {
        classe: {"classe": classe, "quantidade": 0, "faturamento": Decimal("0")}
        for classe in ("A", "B", "C")
    }
    total = sum((produto["faturamento"] for produto in produtos), start=Decimal("0"))
    if total <= 0:
        return {"itens": [], "faixas": list(faixas.values()), "total": Decimal("0.00")}

    ordenados = sorted(
        produtos,
        key=lambda produto: (-produto["faturamento"], produto["pizza"].nome.casefold()),
    )
    acumulado = Decimal("0")
    itens = []
    for produto in ordenados:
        participacao = produto["faturamento"] / total * 100
        if acumulado < 80:
            classe = "A"
        elif acumulado < 95:
            classe = "B"
        else:
            classe = "C"
        acumulado += participacao
        faixas[classe]["quantidade"] += 1
        faixas[classe]["faturamento"] += produto["faturamento"]
        itens.append(
            {
                "pizza": produto["pizza"],
                "faturamento": produto["faturamento"],
                "participacao": _arredondar(participacao),
                "acumulado": _arredondar(min(acumulado, Decimal("100"))),
                "classe": classe,
            }
        )

    for faixa in faixas.values():
        faixa["faturamento"] = _arredondar(faixa["faturamento"])
        faixa["participacao"] = _arredondar(faixa["faturamento"] / total * 100)

    return {"itens": itens, "faixas": list(faixas.values()), "total": _arredondar(total)}


def _calcular_indicadores(inicio, fim, *, granularidade, consulta_dia):
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
            consulta_dia and (periodo.tipo != RegistroVenda.Tipo.DIA or dias_periodo > 1)
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
    margem_total = lucro / faturamento * 100 if faturamento > 0 else Decimal("0")
    ticket_medio = faturamento / pedidos if pedidos > 0 else Decimal("0")
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
    total_pizzas_vendidas = sum((item["quantidade"] for item in mais_vendidos), start=Decimal("0"))
    for produto in mais_vendidos:
        participacao = Decimal("0")
        if total_pizzas_vendidas > 0:
            participacao = produto["quantidade"] / total_pizzas_vendidas * 100
        produto["participacao"] = _arredondar(participacao)

    return {
        "granularidade": granularidade,
        "inicio": inicio,
        "fim": fim,
        "pedidos": _arredondar(pedidos),
        "faturamento": _arredondar(faturamento),
        "custo": _arredondar(custo),
        "lucro": _arredondar(lucro),
        "margem": _arredondar(margem_total),
        "ticket_medio": _arredondar(ticket_medio),
        "total_pizzas_vendidas": _arredondar(total_pizzas_vendidas),
        "mais_vendidos": mais_vendidos[:5],
        "curva_abc": _construir_curva_abc(mais_vendidos),
        "serie_temporal": _construir_serie_temporal(periodos, inicio, fim),
        "periodos_considerados": len(periodos),
        "medias_diarias": medias_diarias,
        "valores_proporcionais": valores_proporcionais,
    }
