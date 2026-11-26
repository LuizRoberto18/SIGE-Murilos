from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from .estoque import ErroEstoque, salvar_venda
from .forms import ItensVendaFormSet, RegistroVendaForm
from .models import RegistroVenda


@login_required
def listar_periodos(request):
    periodos = RegistroVenda.objects.select_related("usuario").annotate(
        total_pizzas=Count("itens_venda")
    )
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


@login_required
def pizzas_vendidas(request, pk):
    periodo = get_object_or_404(RegistroVenda, pk=pk)
    formset = ItensVendaFormSet(request.POST or None, instance=periodo)
    if request.method == "POST":
        if formset.is_valid():
            try:
                alterado, negativos = salvar_venda(formset, request.user)
            except ErroEstoque as erro:
                messages.error(request, str(erro))
            else:
                if alterado:
                    messages.success(request, "Venda salva e estoque atualizado.")
                    if negativos:
                        messages.warning(request, f"Estoque negativo: {', '.join(negativos)}.")
                else:
                    messages.info(request, "Nenhuma alteração foi identificada na venda.")
                return redirect("vendas:pizzas", pk=pk)
        else:
            messages.error(request, "Corrija os erros das pizzas vendidas.")
    return render(request, "vendas/pizzas.html", {"periodo": periodo, "formset": formset})
