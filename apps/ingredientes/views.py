from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from .forms import IngredienteForm, PlanilhaEstoqueForm
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


@login_required
@require_http_methods(["GET", "POST"])
def importar_estoque(request):
    form = PlanilhaEstoqueForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            messages.success(request, "Planilha reconhecida. O estoque não foi alterado.")
            return redirect("ingredientes:importar")
        messages.error(request, "Selecione uma planilha válida no formato do modelo.")
    return render(request, "ingredientes/importar.html", {"form": form})


@login_required
@require_GET
def baixar_modelo(request):
    caminho = Path(__file__).resolve().parent / "arquivos" / "modelo_estoque.xlsx"
    return FileResponse(
        open(caminho, "rb"),
        as_attachment=True,
        filename="modelo_estoque.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
