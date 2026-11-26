from datetime import date
from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.ingredientes.importacoes import aplicar_importacao
from apps.ingredientes.models import Importacao, Ingrediente
from apps.vendas.models import ItemVenda, RegistroVenda

from .models import ItemFicha, Pizza


class CustoPizzaTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            email="gestor@murilos.test", password="SenhaSegura123!"
        )
        self.client.force_login(self.usuario)
        self.queijo = Ingrediente.objects.create(
            nome="Queijo",
            unidade="G",
            quantidade_estoque=1000,
            custo_unitario=Decimal("0.0500"),
        )
        self.molho = Ingrediente.objects.create(
            nome="Molho",
            unidade="ML",
            quantidade_estoque=500,
            custo_unitario=Decimal("0.0200"),
        )
        self.pizza = Pizza.objects.create(nome="Mussarela", preco_venda=Decimal("30.00"))
        ItemFicha.objects.create(pizza=self.pizza, ingrediente=self.queijo, quantidade=100)
        ItemFicha.objects.create(pizza=self.pizza, ingrediente=self.molho, quantidade=50)
        self.url = reverse("pizzas:custo", args=[self.pizza.pk])

    def test_calcula_e_detalha_custo_atual(self):
        resposta = self.client.get(self.url)

        self.assertEqual(self.pizza.custo_atual, Decimal("6.0000"))
        self.assertEqual(resposta.context["pizza"].custo_atual, Decimal("6.0000"))
        self.assertContains(resposta, "Queijo")
        self.assertContains(resposta, "Molho")
        self.assertContains(resposta, "Custo total dos ingredientes")

    def test_listagem_exibe_custo_e_link_para_detalhe(self):
        resposta = self.client.get(reverse("pizzas:listar"))

        self.assertContains(resposta, "Custo atual")
        self.assertContains(resposta, self.url)
        pizza = list(resposta.context["pizzas"])[0]
        self.assertEqual(pizza.custo_atual, Decimal("6.0000"))

    def test_importacao_recalcula_custo_e_preserva_snapshot_da_venda(self):
        periodo = RegistroVenda.objects.create(
            tipo=RegistroVenda.Tipo.DIA,
            data_inicio=date(2026, 11, 26),
            data_fim=date(2026, 11, 26),
            total_pedidos=1,
            usuario=self.usuario,
        )
        dados = {
            "itens_venda-TOTAL_FORMS": "1",
            "itens_venda-INITIAL_FORMS": "0",
            "itens_venda-MIN_NUM_FORMS": "0",
            "itens_venda-MAX_NUM_FORMS": "1000",
            "itens_venda-0-pizza": str(self.pizza.pk),
            "itens_venda-0-quantidade": "1",
        }
        self.client.post(reverse("vendas:pizzas", args=[periodo.pk]), dados)
        venda = ItemVenda.objects.get(registro=periodo, pizza=self.pizza)
        self.assertEqual(venda.custo_unitario, Decimal("6.0000"))

        aplicar_importacao(
            {
                "token": str(uuid4()),
                "arquivo": "contagem.csv",
                "linhas": [
                    {
                        "nome": "Queijo",
                        "unidade": "G",
                        "quantidade": "900",
                        "custo_unitario": "0.1000",
                    }
                ],
            },
            Importacao.Tipo.CONTAGEM,
            self.usuario,
        )

        self.queijo.refresh_from_db()
        venda.refresh_from_db()
        pizza = Pizza.objects.get(pk=self.pizza.pk)
        self.assertEqual(self.queijo.custo_unitario, Decimal("0.1000"))
        self.assertEqual(pizza.custo_atual, Decimal("11.0000"))
        self.assertEqual(venda.custo_unitario, Decimal("6.0000"))
        self.assertEqual(self.client.get(self.url).context["pizza"].custo_atual, Decimal("11.0000"))

    def test_pizza_sem_ficha_tem_custo_zero(self):
        pizza = Pizza.objects.create(nome="Sem ficha", preco_venda=20)
        resposta = self.client.get(reverse("pizzas:custo", args=[pizza.pk]))

        self.assertEqual(resposta.context["pizza"].custo_atual, Decimal("0.0000"))
        self.assertContains(resposta, "ainda não possui ingredientes")

    def test_consulta_exige_login(self):
        self.client.logout()
        self.assertRedirects(
            self.client.get(self.url), f"{reverse('accounts:entrar')}?next={self.url}"
        )
