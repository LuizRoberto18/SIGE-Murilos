from django.contrib.auth.decorators import login_required
from django.db.models import F, Q
from django.shortcuts import render

from apps.ingredientes.models import Ingrediente
from apps.pizzas.models import Pizza


@login_required
def dashboard(request):
    ingredientes = Ingrediente.objects.filter(ativo=True)
    atencao = ingredientes.filter(
        Q(quantidade_estoque__lt=F("estoque_minimo")) | Q(quantidade_estoque__lt=0)
    ).order_by("quantidade_estoque", "nome")
    contexto = {
        "total_ingredientes": ingredientes.count(),
        "total_pizzas": Pizza.objects.filter(ativo=True).count(),
        "total_baixos": ingredientes.filter(quantidade_estoque__lt=F("estoque_minimo")).count(),
        "total_negativos": ingredientes.filter(quantidade_estoque__lt=0).count(),
        "atencao": atencao,
    }
    return render(request, "core/dashboard.html", contexto)
