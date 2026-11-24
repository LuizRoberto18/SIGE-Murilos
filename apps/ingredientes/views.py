from pathlib import Path
from uuid import uuid4

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import ConfirmarImportacaoForm, IngredienteForm, PlanilhaEstoqueForm
from .importacoes import ErroImportacao, aplicar_importacao, hash_importacao
from .models import Importacao, Ingrediente


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
    previa = None
    if request.method == "POST":
        request.session.pop("importacao_pendente", None)
        if form.is_valid():
            previa = form.previa
            messages.success(request, "Planilha reconhecida. Prévia gerada sem alterar o estoque.")
            if previa["linhas"] and not previa["invalidas"]:
                request.session["importacao_pendente"] = {
                    "token": str(uuid4()),
                    "arquivo": request.FILES["arquivo"].name[:255],
                    "linhas": [
                        {
                            "nome": linha["nome"],
                            "unidade": linha["unidade_base"],
                            "quantidade": str(linha["quantidade_base"]),
                            "custo_unitario": str(linha["custo_base"]),
                        }
                        for linha in previa["linhas"]
                    ],
                }
        else:
            messages.error(request, "Corrija os erros da planilha.")
    pendente = request.session.get("importacao_pendente")
    confirmar_form = (
        ConfirmarImportacaoForm(initial={"token": pendente["token"]}) if pendente else None
    )
    return render(
        request,
        "ingredientes/importar.html",
        {"form": form, "previa": previa, "pendente": pendente, "confirmar_form": confirmar_form},
    )


@login_required
@require_POST
def confirmar_importacao(request):
    form = ConfirmarImportacaoForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Escolha compra ou contagem para confirmar a importação.")
        return redirect("ingredientes:importar")

    token = form.cleaned_data["token"]
    existente = Importacao.objects.filter(identificador=token).first()
    if existente:
        request.session.pop("importacao_pendente", None)
        messages.info(request, "Esta importação já foi confirmada.")
        return redirect("ingredientes:detalhe_importacao", pk=existente.pk)

    pendente = request.session.get("importacao_pendente")
    if not pendente or pendente["token"] != str(token) or not pendente["linhas"]:
        messages.error(request, "Prévia expirada ou substituída. Envie a planilha novamente.")
        return redirect("ingredientes:importar")

    conteudo = hash_importacao(pendente, form.cleaned_data["tipo"])
    repetir = form.cleaned_data["repetir"]
    if Importacao.objects.filter(hash_conteudo=conteudo).exists() and not repetir:
        messages.warning(
            request,
            "Uma importação com estes dados e tipo já foi confirmada. "
            "Marque a repetição consciente para registrar uma nova operação.",
        )
        return redirect("ingredientes:importar")

    try:
        importacao = aplicar_importacao(
            pendente, form.cleaned_data["tipo"], request.user, repetir=repetir
        )
    except ErroImportacao as erro:
        request.session.pop("importacao_pendente", None)
        messages.error(request, str(erro))
        return redirect("ingredientes:importar")
    except IntegrityError:
        existente = Importacao.objects.filter(identificador=token).first()
        if existente:
            request.session.pop("importacao_pendente", None)
            messages.info(request, "Esta importação já foi confirmada.")
            return redirect("ingredientes:detalhe_importacao", pk=existente.pk)
        if Importacao.objects.filter(hash_conteudo=conteudo).exists():
            messages.warning(request, "Uma importação com estes dados e tipo já foi confirmada.")
            return redirect("ingredientes:importar")
        request.session.pop("importacao_pendente", None)
        messages.error(request, "O estoque mudou. Envie a planilha novamente.")
        return redirect("ingredientes:importar")

    request.session.pop("importacao_pendente", None)
    messages.success(request, "Estoque atualizado e importação registrada.")
    return redirect("ingredientes:detalhe_importacao", pk=importacao.pk)


@login_required
@require_GET
def detalhe_importacao(request, pk):
    importacao = get_object_or_404(Importacao.objects.select_related("usuario"), pk=pk)
    return render(
        request,
        "ingredientes/importacao.html",
        {"importacao": importacao, "itens": importacao.itens.all()},
    )


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
