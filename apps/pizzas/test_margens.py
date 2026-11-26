from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.ingredientes.models import Ingrediente

from .models import ItemFicha, Pizza


class MargensPizzaTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            email="gestor@murilos.test", password="SenhaSegura123!"
        )
        self.client.force_login(self.usuario)
        self.ingrediente = Ingrediente.objects.create(
            nome="Queijo",
            unidade="G",
            quantidade_estoque=1000,
            custo_unitario=Decimal("1.0000"),
        )
        self.mais_rentavel = self.criar_pizza("Mais rentável", 40, 10)
        self.intermediaria = self.criar_pizza("Intermediária", 30, 15)
        self.prejuizo = self.criar_pizza("Prejuízo", 10, 12)
        self.pendente = Pizza.objects.create(nome="Pendente", preco_venda=50)
        self.inativa = self.criar_pizza("Inativa", 100, 1, ativo=False)
        self.url = reverse("pizzas:ranking")

    def criar_pizza(self, nome, preco, quantidade, ativo=True):
        pizza = Pizza.objects.create(nome=nome, preco_venda=preco, ativo=ativo)
        ItemFicha.objects.create(
            pizza=pizza,
            ingrediente=self.ingrediente,
            quantidade=quantidade,
        )
        return pizza

    def test_calcula_lucro_unitario_e_margem_percentual(self):
        indicadores = self.mais_rentavel.calcular_rentabilidade()

        self.assertEqual(indicadores["custo"], Decimal("10.0000"))
        self.assertEqual(indicadores["lucro"], Decimal("30.0000"))
        self.assertEqual(indicadores["margem"], Decimal("75.00"))

    def test_preco_zero_nao_causa_divisao_por_zero(self):
        pizza = Pizza(nome="Preço zero", preco_venda=Decimal("0"))
        item = ItemFicha(pizza=pizza, ingrediente=self.ingrediente, quantidade=5)

        indicadores = pizza.calcular_rentabilidade([item])

        self.assertEqual(indicadores["custo"], Decimal("5.0000"))
        self.assertEqual(indicadores["lucro"], Decimal("-5.0000"))
        self.assertEqual(indicadores["margem"], Decimal("0.00"))

    def test_ranking_ordena_por_margem_calculada(self):
        resposta = self.client.get(self.url)
        ranking = resposta.context["ranking"]

        self.assertEqual(
            [item["pizza"] for item in ranking],
            [self.mais_rentavel, self.intermediaria, self.prejuizo],
        )
        self.assertEqual(
            [item["margem"] for item in ranking],
            [Decimal("75.00"), Decimal("50.00"), Decimal("-20.00")],
        )
        self.assertNotContains(resposta, self.inativa.nome)

    def test_exibe_moeda_percentual_e_separa_ficha_pendente(self):
        resposta = self.client.get(self.url)

        self.assertContains(resposta, "Lucro unitário (R$)")
        self.assertContains(resposta, "Margem (%)")
        self.assertContains(resposta, "Fichas pendentes")
        self.assertEqual(resposta.context["pendentes"], [self.pendente])

    def test_ranking_exige_login(self):
        self.client.logout()
        self.assertRedirects(
            self.client.get(self.url), f"{reverse('accounts:entrar')}?next={self.url}"
        )
