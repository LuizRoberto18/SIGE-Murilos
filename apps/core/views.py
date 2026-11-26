from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F
from django.shortcuts import render

from apps.ingredientes.models import Ingrediente
from apps.pizzas.models import Pizza

from .forms import MovimentoFiltroForm
from .historico import consultar_movimentacoes


@login_required
def dashboard(request):
    ingredientes = Ingrediente.objects.filter(ativo=True)
    atencao = ingredientes.filter(quantidade_estoque__lte=F("estoque_minimo")).order_by(
        "quantidade_estoque", "nome"
    )
    contexto = {
        "total_ingredientes": ingredientes.count(),
        "total_pizzas": Pizza.objects.filter(ativo=True).count(),
        "total_baixos": ingredientes.filter(quantidade_estoque__lte=F("estoque_minimo")).count(),
        "total_negativos": ingredientes.filter(quantidade_estoque__lt=0).count(),
        "atencao": atencao,
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
