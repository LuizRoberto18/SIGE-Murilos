from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("conta/", include("apps.accounts.urls")),
    path("ingredientes/", include("apps.ingredientes.urls")),
    path("pizzas/", include("apps.pizzas.urls")),
    path("vendas/", include("apps.vendas.urls")),
]
