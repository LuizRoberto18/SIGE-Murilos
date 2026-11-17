from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.ingredientes.models import Ingrediente
from apps.pizzas.models import Pizza


class DashboardTests(TestCase):
    def setUp(self):
        self.url = reverse("core:dashboard")
        self.usuario = get_user_model().objects.create_user(
            email="gestor@murilos.test", password="SenhaSegura123!"
        )

    def test_exige_login(self):
        resposta = self.client.get(self.url)
        self.assertRedirects(resposta, f"{reverse('accounts:entrar')}?next={self.url}")

    def test_banco_vazio(self):
        self.client.force_login(self.usuario)
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.context["total_ingredientes"], 0)
        self.assertEqual(resposta.context["total_pizzas"], 0)
        self.assertEqual(resposta.context["total_baixos"], 0)
        self.assertEqual(resposta.context["total_negativos"], 0)

    def test_indicadores_reais(self):
        Ingrediente.objects.create(
            nome="Queijo", unidade="G", quantidade_estoque=2, custo_unitario=1, estoque_minimo=5
        )
        Ingrediente.objects.create(
            nome="Molho", unidade="ML", quantidade_estoque=-1, custo_unitario=1, estoque_minimo=0
        )
        Ingrediente.objects.create(
            nome="Inativo",
            unidade="UN",
            quantidade_estoque=0,
            custo_unitario=1,
            estoque_minimo=4,
            ativo=False,
        )
        Pizza.objects.create(nome="Mussarela", preco_venda=Decimal("35"))
        Pizza.objects.create(nome="Inativa", preco_venda=Decimal("36"), ativo=False)
        self.client.force_login(self.usuario)
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.context["total_ingredientes"], 2)
        self.assertEqual(resposta.context["total_pizzas"], 1)
        self.assertEqual(resposta.context["total_baixos"], 2)
        self.assertEqual(resposta.context["total_negativos"], 1)
        self.assertContains(resposta, "Queijo")
        self.assertContains(resposta, "Molho")
