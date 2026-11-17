from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .forms import IngredienteForm
from .models import Ingrediente


class IngredienteTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            email="gestor@murilos.test", password="SenhaSegura123!"
        )
        self.client.force_login(usuario)
        self.dados = {
            "nome": "Queijo",
            "unidade": "G",
            "quantidade_estoque": "10",
            "custo_unitario": "0.0500",
            "estoque_minimo": "5",
            "ativo": "on",
        }

    def test_criacao_e_listagem(self):
        resposta = self.client.post(reverse("ingredientes:novo"), self.dados)
        self.assertRedirects(resposta, reverse("ingredientes:listar"))
        self.assertContains(self.client.get(reverse("ingredientes:listar")), "Queijo")

    def test_edicao(self):
        item = Ingrediente.objects.create(
            nome="Queijo", unidade="G", quantidade_estoque=10, custo_unitario=1
        )
        dados = {**self.dados, "nome": "Queijo novo"}
        self.assertRedirects(
            self.client.post(reverse("ingredientes:editar", args=[item.pk]), dados),
            reverse("ingredientes:listar"),
        )
        item.refresh_from_db()
        self.assertEqual(item.nome, "Queijo novo")

    def test_nome_duplicado_sem_diferenciar_maiusculas(self):
        Ingrediente.objects.create(
            nome="Queijo", unidade="G", quantidade_estoque=1, custo_unitario=1
        )
        form = IngredienteForm({**self.dados, "nome": "QUEIJO"})
        self.assertFalse(form.is_valid())
        with self.assertRaises(IntegrityError), transaction.atomic():
            Ingrediente.objects.create(
                nome="QUEIJO", unidade="G", quantidade_estoque=1, custo_unitario=1
            )

    def test_valores_invalidos_no_formulario(self):
        for campo in ("quantidade_estoque", "custo_unitario", "estoque_minimo"):
            with self.subTest(campo=campo):
                form = IngredienteForm({**self.dados, campo: "-1"})
                self.assertFalse(form.is_valid())
                self.assertIn(campo, form.errors)

    def test_estoque_baixo_e_negativo(self):
        item = Ingrediente(
            nome="Queijo",
            unidade="G",
            quantidade_estoque=Decimal("2"),
            custo_unitario=1,
            estoque_minimo=5,
        )
        self.assertTrue(item.estoque_baixo)
        self.assertFalse(item.estoque_negativo)
        item.quantidade_estoque = Decimal("-1")
        item.full_clean()
        item.save()
        self.assertTrue(item.estoque_negativo)

    def test_modelo_rejeita_custo_negativo(self):
        item = Ingrediente(nome="Queijo", unidade="G", quantidade_estoque=0, custo_unitario=-1)
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_edicao_preserva_estoque_negativo_existente(self):
        item = Ingrediente.objects.create(
            nome="Queijo", unidade="G", quantidade_estoque=-2, custo_unitario=1
        )
        dados = {**self.dados, "quantidade_estoque": "-2", "nome": "Queijo especial"}
        self.assertRedirects(
            self.client.post(reverse("ingredientes:editar", args=[item.pk]), dados),
            reverse("ingredientes:listar"),
        )
        item.refresh_from_db()
        self.assertEqual(item.quantidade_estoque, Decimal("-2"))

    def test_listagem_apenas_ativos(self):
        Ingrediente.objects.create(
            nome="Inativo", unidade="G", quantidade_estoque=0, custo_unitario=1, ativo=False
        )
        self.assertNotContains(self.client.get(reverse("ingredientes:listar")), "Inativo")

    def test_paginas_exigem_login(self):
        item = Ingrediente.objects.create(
            nome="Queijo", unidade="G", quantidade_estoque=0, custo_unitario=1
        )
        self.client.logout()
        for url in (
            reverse("ingredientes:listar"),
            reverse("ingredientes:novo"),
            reverse("ingredientes:editar", args=[item.pk]),
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 302)
