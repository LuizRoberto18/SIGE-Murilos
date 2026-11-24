from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import RegistroVendaForm
from .models import RegistroVenda


@login_required
def listar_periodos(request):
    periodos = RegistroVenda.objects.select_related("usuario")
    return render(request, "vendas/lista.html", {"periodos": periodos})


@login_required
def novo_periodo(request):
    form = RegistroVendaForm(request.POST or None)
    if request.method == "POST":
        with transaction.atomic():
            if form.is_valid():
                periodo = form.save(commit=False)
                periodo.usuario = request.user
                periodo.save()
                messages.success(request, "Período de vendas registrado.")
                return redirect("vendas:listar")
        messages.error(request, "Corrija os erros do formulário.")
    return render(request, "vendas/formulario.html", {"form": form, "titulo": "Novo período"})


@login_required
def editar_periodo(request, pk):
    periodo = get_object_or_404(RegistroVenda, pk=pk)
    form = RegistroVendaForm(request.POST or None, instance=periodo)
    if request.method == "POST":
        with transaction.atomic():
            if form.is_valid():
                form.save()
                messages.success(request, "Período de vendas atualizado.")
                return redirect("vendas:listar")
        messages.error(request, "Corrija os erros do formulário.")
    return render(request, "vendas/formulario.html", {"form": form, "titulo": "Editar período"})
