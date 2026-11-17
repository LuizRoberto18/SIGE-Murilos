from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import EntrarForm


def entrar(request):
    proximo = request.POST.get("next") or request.GET.get("next") or reverse("core:dashboard")
    if not url_has_allowed_host_and_scheme(proximo, {request.get_host()}):
        proximo = reverse("core:dashboard")
    if request.user.is_authenticated:
        return redirect(proximo)
    form = EntrarForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = authenticate(
            request, email=form.cleaned_data["email"], password=form.cleaned_data["senha"]
        )
        if usuario is not None:
            login(request, usuario)
            return redirect(proximo)
        messages.error(request, "E-mail ou senha inválidos.")
    return render(request, "accounts/login.html", {"form": form, "proximo": proximo})


@login_required
@require_POST
def sair(request):
    logout(request)
    return redirect("accounts:entrar")
