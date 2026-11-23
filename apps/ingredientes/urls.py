from django.urls import path

from . import views

app_name = "ingredientes"
urlpatterns = [
    path("", views.listar_ingredientes, name="listar"),
    path("novo/", views.novo_ingrediente, name="novo"),
    path("importar/", views.importar_estoque, name="importar"),
    path("importar/modelo/", views.baixar_modelo, name="modelo"),
    path("<int:pk>/editar/", views.editar_ingrediente, name="editar"),
]
