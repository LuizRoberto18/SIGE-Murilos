from django.urls import path

from . import views

app_name = "vendas"
urlpatterns = [
    path("", views.listar_periodos, name="listar"),
    path("novo/", views.novo_periodo, name="novo"),
    path("<int:pk>/editar/", views.editar_periodo, name="editar"),
    path("<int:pk>/pizzas/", views.pizzas_vendidas, name="pizzas"),
]
