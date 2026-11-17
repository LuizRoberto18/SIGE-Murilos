from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import IngredienteForm
from .models import Ingrediente


@login_required
def listar_ingredientes(request):
    ingredientes = Ingrediente.objects.filter(ativo=True)
    return render(request, "ingredientes/lista.html", {"ingredientes": ingredientes})


@login_required
def novo_ingrediente(request):
    form = IngredienteForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Ingrediente cadastrado.")
            return redirect("ingredientes:listar")
        messages.error(request, "Corrija os erros do formulário.")
    return render(
        request, "ingredientes/formulario.html", {"form": form, "titulo": "Novo ingrediente"}
    )


@login_required
def editar_ingrediente(request, pk):
    ingrediente = get_object_or_404(Ingrediente, pk=pk)
    form = IngredienteForm(request.POST or None, instance=ingrediente)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Ingrediente atualizado.")
            return redirect("ingredientes:listar")
        messages.error(request, "Corrija os erros do formulário.")
    return render(
        request, "ingredientes/formulario.html", {"form": form, "titulo": "Editar ingrediente"}
    )
