from django.urls import path

from . import views

app_name = "pizzas"
urlpatterns = [
    path("", views.listar_pizzas, name="listar"),
    path("nova/", views.nova_pizza, name="nova"),
    path("<int:pk>/editar/", views.editar_pizza, name="editar"),
    path("<int:pk>/ficha-tecnica/", views.ficha_tecnica, name="ficha"),
]
