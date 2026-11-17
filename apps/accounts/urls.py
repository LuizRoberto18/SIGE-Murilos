from django.urls import path

from . import views

app_name = "accounts"
urlpatterns = [
    path("entrar/", views.entrar, name="entrar"),
    path("sair/", views.sair, name="sair"),
]
