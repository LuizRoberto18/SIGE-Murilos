from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse

from apps.ingredientes.models import Ingrediente

from .forms import PizzaForm
from .models import ItemFicha, Pizza


class PizzaTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            email="gestor@murilos.test", password="SenhaSegura123!"
        )
        self.client.force_login(usuario)
        self.pizza = Pizza.objects.create(nome="Mussarela", preco_venda=Decimal("35"))
        self.queijo = Ingrediente.objects.create(
            nome="Queijo", unidade="G", quantidade_estoque=100, custo_unitario=1
        )
        self.molho = Ingrediente.objects.create(
            nome="Molho", unidade="ML", quantidade_estoque=100, custo_unitario=1
        )

    def dados_ficha(self, *itens):
        dados = {
            "itens_ficha-TOTAL_FORMS": str(len(itens)),
            "itens_ficha-INITIAL_FORMS": "0",
            "itens_ficha-MIN_NUM_FORMS": "0",
            "itens_ficha-MAX_NUM_FORMS": "1000",
        }
        for indice, (ingrediente, quantidade) in enumerate(itens):
            dados[f"itens_ficha-{indice}-ingrediente"] = str(ingrediente.pk)
            dados[f"itens_ficha-{indice}-quantidade"] = str(quantidade)
        return dados

    def test_criacao_e_edicao(self):
        resposta = self.client.post(
            reverse("pizzas:nova"), {"nome": "Calabresa", "preco_venda": "42", "ativo": "on"}
        )
        nova = Pizza.objects.get(nome="Calabresa")
        self.assertRedirects(resposta, reverse("pizzas:ficha", args=[nova.pk]))
        self.assertTrue(nova.ficha_pendente)
        self.assertRedirects(
            self.client.post(
                reverse("pizzas:editar", args=[nova.pk]),
                {"nome": "Calabresa especial", "preco_venda": "43", "ativo": "on"},
            ),
            reverse("pizzas:listar"),
        )
        nova.refresh_from_db()
        self.assertEqual(nova.nome, "Calabresa especial")

    def test_preco_e_nome_invalidos(self):
        self.assertFalse(PizzaForm({"nome": "Nova", "preco_venda": "0", "ativo": "on"}).is_valid())
        self.assertFalse(
            PizzaForm({"nome": "MUSSARELA", "preco_venda": "35", "ativo": "on"}).is_valid()
        )
        with self.assertRaises(ValidationError):
            Pizza(nome="Inválida", preco_venda=0).full_clean()

    def test_listagem_e_protecao(self):
        Pizza.objects.create(nome="Inativa", preco_venda=20, ativo=False)
        resposta = self.client.get(reverse("pizzas:listar"))
        self.assertContains(resposta, "Mussarela")
        self.assertContains(resposta, "Pendente")
        self.assertNotContains(resposta, "Inativa")
        self.client.logout()
        for url in (
            reverse("pizzas:listar"),
            reverse("pizzas:nova"),
            reverse("pizzas:editar", args=[self.pizza.pk]),
            reverse("pizzas:ficha", args=[self.pizza.pk]),
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 302)

    def test_inclusao_e_edicao_da_ficha(self):
        url = reverse("pizzas:ficha", args=[self.pizza.pk])
        self.assertRedirects(self.client.post(url, self.dados_ficha((self.queijo, "150"))), url)
        item = ItemFicha.objects.get(pizza=self.pizza)
        self.assertEqual(item.quantidade, Decimal("150"))
        dados = {
            "itens_ficha-TOTAL_FORMS": "2",
            "itens_ficha-INITIAL_FORMS": "1",
            "itens_ficha-MIN_NUM_FORMS": "0",
            "itens_ficha-MAX_NUM_FORMS": "1000",
            "itens_ficha-0-id": str(item.pk),
            "itens_ficha-0-ingrediente": str(self.queijo.pk),
            "itens_ficha-0-quantidade": "160",
            "itens_ficha-1-ingrediente": str(self.molho.pk),
            "itens_ficha-1-quantidade": "30",
        }
        self.assertRedirects(self.client.post(url, dados), url)
        self.assertEqual(ItemFicha.objects.filter(pizza=self.pizza).count(), 2)
        item.refresh_from_db()
        self.assertEqual(item.quantidade, Decimal("160"))

    def test_quantidade_invalida_e_duplicado(self):
        url = reverse("pizzas:ficha", args=[self.pizza.pk])
        resposta = self.client.post(url, self.dados_ficha((self.queijo, "0")))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(ItemFicha.objects.count(), 0)
        resposta = self.client.post(url, self.dados_ficha((self.queijo, "5"), (self.queijo, "6")))
        self.assertContains(resposta, "duplicado")
        self.assertEqual(ItemFicha.objects.count(), 0)

    def test_constraints_e_exclusao_protegida(self):
        ItemFicha.objects.create(pizza=self.pizza, ingrediente=self.queijo, quantidade=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ItemFicha.objects.create(pizza=self.pizza, ingrediente=self.queijo, quantidade=2)
        with self.assertRaises(ProtectedError):
            self.queijo.delete()
        with self.assertRaises(ProtectedError):
            self.pizza.delete()

    def test_salvamento_atomico(self):
        url = reverse("pizzas:ficha", args=[self.pizza.pk])
        dados = self.dados_ficha((self.queijo, "5"), (self.molho, "6"))
        original = ItemFicha.save
        chamadas = 0

        def falhar_na_segunda(instancia, *args, **kwargs):
            nonlocal chamadas
            chamadas += 1
            if chamadas == 2:
                raise RuntimeError("Falha simulada")
            return original(instancia, *args, **kwargs)

        with patch.object(ItemFicha, "save", falhar_na_segunda):
            with self.assertRaises(RuntimeError):
                self.client.post(url, dados)
        self.assertEqual(ItemFicha.objects.filter(pizza=self.pizza).count(), 0)
