from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ItensFichaFormSet, PizzaForm
from .models import Pizza


@login_required
def listar_pizzas(request):
    pizzas = Pizza.objects.filter(ativo=True).prefetch_related("itens_ficha")
    return render(request, "pizzas/lista.html", {"pizzas": pizzas})


@login_required
def nova_pizza(request):
    form = PizzaForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            pizza = form.save()
            messages.success(request, "Pizza cadastrada. Configure sua ficha técnica.")
            return redirect("pizzas:ficha", pk=pizza.pk)
        messages.error(request, "Corrija os erros do formulário.")
    return render(request, "pizzas/formulario.html", {"form": form, "titulo": "Nova pizza"})


@login_required
def editar_pizza(request, pk):
    pizza = get_object_or_404(Pizza, pk=pk)
    form = PizzaForm(request.POST or None, instance=pizza)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Pizza atualizada.")
            return redirect("pizzas:listar")
        messages.error(request, "Corrija os erros do formulário.")
    return render(request, "pizzas/formulario.html", {"form": form, "titulo": "Editar pizza"})


@login_required
def ficha_tecnica(request, pk):
    pizza = get_object_or_404(Pizza, pk=pk)
    formset = ItensFichaFormSet(request.POST or None, instance=pizza)
    if request.method == "POST":
        if formset.is_valid():
            with transaction.atomic():
                formset.save()
            messages.success(request, "Ficha técnica atualizada.")
            return redirect("pizzas:ficha", pk=pk)
        messages.error(request, "Corrija os erros da ficha técnica.")
    return render(request, "pizzas/ficha_tecnica.html", {"pizza": pizza, "formset": formset})
