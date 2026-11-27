from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F
from django.shortcuts import render
from django.utils import timezone

from apps.ingredientes.models import Ingrediente
from apps.pizzas.models import Pizza

from .forms import IndicadorFiltroForm, MovimentoFiltroForm
from .historico import consultar_movimentacoes
from .indicadores import calcular_indicadores_intervalo


@login_required
def dashboard(request):
    ingredientes = Ingrediente.objects.filter(ativo=True)
    atencao = ingredientes.filter(quantidade_estoque__lte=F("estoque_minimo")).order_by(
        "quantidade_estoque", "nome"
    )
    filtro = IndicadorFiltroForm(request.GET or None)
    indicadores = None
    if not filtro.is_bound:
        hoje = timezone.localdate()
        indicadores = calcular_indicadores_intervalo(hoje.replace(day=1), hoje)
    elif filtro.is_valid():
        indicadores = calcular_indicadores_intervalo(
            filtro.cleaned_data["data_inicio"],
            filtro.cleaned_data["data_fim"],
        )
    total_ingredientes = ingredientes.count()
    total_baixos = ingredientes.filter(quantidade_estoque__lte=F("estoque_minimo")).count()
    total_negativos = ingredientes.filter(quantidade_estoque__lt=0).count()
    total_baixos_nao_negativos = total_baixos - total_negativos
    total_saudaveis = total_ingredientes - total_baixos
    contexto = {
        "total_ingredientes": total_ingredientes,
        "total_pizzas": Pizza.objects.filter(ativo=True).count(),
        "total_baixos": total_baixos,
        "total_baixos_nao_negativos": total_baixos_nao_negativos,
        "total_negativos": total_negativos,
        "total_saudaveis": total_saudaveis,
        "percentual_saudaveis": round(total_saudaveis / total_ingredientes * 100, 2)
        if total_ingredientes
        else 0,
        "percentual_baixos": round(total_baixos_nao_negativos / total_ingredientes * 100, 2)
        if total_ingredientes
        else 0,
        "percentual_negativos": round(total_negativos / total_ingredientes * 100, 2)
        if total_ingredientes
        else 0,
        "atencao": atencao,
        "filtro": filtro,
        "indicadores": indicadores,
    }
    return render(request, "core/dashboard.html", contexto)


@login_required
def movimentacoes(request):
    form = MovimentoFiltroForm(request.GET or None)
    filtros = form.cleaned_data if form.is_valid() else {}
    registros = consultar_movimentacoes(filtros)
    pagina = Paginator(registros, 25).get_page(request.GET.get("pagina"))
    parametros = request.GET.copy()
    parametros.pop("pagina", None)
    return render(
        request,
        "core/movimentacoes.html",
        {"form": form, "pagina": pagina, "parametros": parametros.urlencode()},
    )
