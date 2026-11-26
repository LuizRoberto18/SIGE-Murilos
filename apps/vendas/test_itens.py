from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse

from apps.ingredientes.models import Ingrediente
from apps.pizzas.models import ItemFicha, Pizza

from .models import ItemVenda, RegistroVenda


class PizzasVendidasTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            email="funcionario@murilos.test", password="SenhaSegura123!"
        )
        self.client.force_login(self.usuario)
        self.periodo = RegistroVenda.objects.create(
            tipo="DIA",
            data_inicio=date(2026, 11, 25),
            data_fim=date(2026, 11, 25),
            total_pedidos=4,
            usuario=self.usuario,
        )
        queijo = Ingrediente.objects.create(
            nome="Queijo", unidade="G", quantidade_estoque=100, custo_unitario=1
        )
        self.mussarela = Pizza.objects.create(nome="Mussarela", preco_venda=30)
        self.calabresa = Pizza.objects.create(nome="Calabresa", preco_venda=35)
        self.sem_ficha = Pizza.objects.create(nome="Sem ficha", preco_venda=25)
        self.inativa = Pizza.objects.create(nome="Inativa", preco_venda=20, ativo=False)
        for pizza in (self.mussarela, self.calabresa, self.inativa):
            ItemFicha.objects.create(pizza=pizza, ingrediente=queijo, quantidade=10)
        self.url = reverse("vendas:pizzas", args=[self.periodo.pk])

    def dados_itens(self, *itens, iniciais=0):
        dados = {
            "itens_venda-TOTAL_FORMS": str(len(itens)),
            "itens_venda-INITIAL_FORMS": str(iniciais),
            "itens_venda-MIN_NUM_FORMS": "0",
            "itens_venda-MAX_NUM_FORMS": "1000",
        }
        for indice, (pizza, quantidade, item, excluir) in enumerate(itens):
            dados[f"itens_venda-{indice}-pizza"] = str(pizza.pk)
            dados[f"itens_venda-{indice}-quantidade"] = str(quantidade)
            if item:
                dados[f"itens_venda-{indice}-id"] = str(item.pk)
            if excluir:
                dados[f"itens_venda-{indice}-DELETE"] = "on"
        return dados

    def test_registra_varias_pizzas_no_mesmo_periodo(self):
        dados = self.dados_itens(
            (self.mussarela, 3, None, False),
            (self.calabresa, 2, None, False),
        )
        resposta = self.client.post(self.url, dados)
        self.assertRedirects(resposta, self.url)
        self.assertEqual(self.periodo.itens_venda.count(), 2)
        self.assertEqual(self.periodo.itens_venda.get(pizza=self.mussarela).quantidade, 3)
        self.assertEqual(self.periodo.itens_venda.get(pizza=self.calabresa).quantidade, 2)
        self.assertContains(self.client.get(reverse("vendas:listar")), "2 tipos")

    def test_aceita_quantidade_zero_e_rejeita_negativa_ou_fracionada(self):
        resposta = self.client.post(self.url, self.dados_itens((self.mussarela, 0, None, False)))
        self.assertRedirects(resposta, self.url)
        self.assertEqual(ItemVenda.objects.get().quantidade, 0)

        for quantidade in (-1, "1.5", "abc"):
            with self.subTest(quantidade=quantidade):
                resposta = self.client.post(
                    self.url, self.dados_itens((self.calabresa, quantidade, None, False))
                )
                self.assertEqual(resposta.status_code, 200)
                self.assertIn("quantidade", resposta.context["formset"].forms[0].errors)
        self.assertEqual(ItemVenda.objects.count(), 1)

    def test_nao_oferece_pizza_inativa_ou_sem_ficha(self):
        resposta = self.client.get(self.url)
        self.assertContains(resposta, "Mussarela")
        self.assertContains(resposta, "Calabresa")
        self.assertNotContains(resposta, "Sem ficha")
        self.assertNotContains(resposta, "Inativa")

        for pizza in (self.sem_ficha, self.inativa):
            with self.subTest(pizza=pizza.nome):
                resposta = self.client.post(self.url, self.dados_itens((pizza, 1, None, False)))
                self.assertEqual(resposta.status_code, 200)
                self.assertIn("pizza", resposta.context["formset"].forms[0].errors)
        self.assertEqual(ItemVenda.objects.count(), 0)

    def test_modelo_rejeita_pizza_sem_ficha(self):
        item = ItemVenda(registro=self.periodo, pizza=self.sem_ficha, quantidade=1)
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_rejeita_pizza_duplicada(self):
        resposta = self.client.post(
            self.url,
            self.dados_itens(
                (self.mussarela, 2, None, False),
                (self.mussarela, 3, None, False),
            ),
        )
        self.assertContains(resposta, "duplicado para pizza")
        self.assertEqual(ItemVenda.objects.count(), 0)

    def test_edita_quantidade_e_remove_item(self):
        self.client.post(
            self.url,
            self.dados_itens(
                (self.mussarela, 2, None, False),
                (self.calabresa, 3, None, False),
            ),
        )
        primeiro = ItemVenda.objects.get(pizza=self.mussarela)
        segundo = ItemVenda.objects.get(pizza=self.calabresa)
        resposta = self.client.post(
            self.url,
            self.dados_itens(
                (self.mussarela, 5, primeiro, False),
                (self.calabresa, 3, segundo, True),
                iniciais=2,
            ),
        )
        self.assertRedirects(resposta, self.url)
        primeiro.refresh_from_db()
        self.assertEqual(primeiro.quantidade, 5)
        self.assertFalse(ItemVenda.objects.filter(pk=segundo.pk).exists())

    def test_constraints_e_relacionamentos_protegidos(self):
        ItemVenda.objects.create(registro=self.periodo, pizza=self.mussarela, quantidade=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ItemVenda.objects.create(registro=self.periodo, pizza=self.mussarela, quantidade=2)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ItemVenda.objects.create(registro=self.periodo, pizza=self.calabresa, quantidade=-1)
        with self.assertRaises(ProtectedError):
            self.periodo.delete()
        with self.assertRaises(ProtectedError):
            self.mussarela.delete()

    def test_falha_no_segundo_item_desfaz_o_primeiro(self):
        dados = self.dados_itens(
            (self.mussarela, 2, None, False),
            (self.calabresa, 3, None, False),
        )
        original = ItemVenda.save
        chamadas = 0

        def falhar_na_segunda(instancia, *args, **kwargs):
            nonlocal chamadas
            chamadas += 1
            if chamadas == 2:
                raise RuntimeError("Falha simulada")
            return original(instancia, *args, **kwargs)

        with patch.object(ItemVenda, "save", falhar_na_segunda):
            with self.assertRaises(RuntimeError):
                self.client.post(self.url, dados)
        self.assertEqual(ItemVenda.objects.count(), 0)

    def test_pagina_exige_login(self):
        self.client.logout()
        self.assertRedirects(
            self.client.get(self.url), f"{reverse('accounts:entrar')}?next={self.url}"
        )
        resposta = self.client.post(self.url, self.dados_itens((self.mussarela, 1, None, False)))
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(ItemVenda.objects.count(), 0)
