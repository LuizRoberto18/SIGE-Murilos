from django.urls import path

from . import views

app_name = "pizzas"
urlpatterns = [
    path("", views.listar_pizzas, name="listar"),
    path("nova/", views.nova_pizza, name="nova"),
    path("ranking/", views.ranking_pizzas, name="ranking"),
    path("<int:pk>/editar/", views.editar_pizza, name="editar"),
    path("<int:pk>/ficha-tecnica/", views.ficha_tecnica, name="ficha"),
    path("<int:pk>/custo/", views.custo_pizza, name="custo"),
]
