from decimal import Decimal
from io import BytesIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from openpyxl import load_workbook

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


class ModeloEstoqueTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            email="funcionario@murilos.test", password="SenhaSegura123!"
        )
        self.client.force_login(usuario)
        self.modelo = (
            Path(__file__).resolve().parent / "arquivos" / "modelo_estoque.xlsx"
        ).read_bytes()

    def test_tela_oferece_download(self):
        resposta = self.client.get(reverse("ingredientes:importar"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, reverse("ingredientes:modelo"))

    def test_download_tem_colunas_do_modelo(self):
        resposta = self.client.get(reverse("ingredientes:modelo"))
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("modelo_estoque.xlsx", resposta["Content-Disposition"])
        conteudo = b"".join(resposta.streaming_content)
        planilha = load_workbook(BytesIO(conteudo), read_only=True)
        try:
            cabecalho = next(planilha.active.iter_rows(min_row=1, max_row=1, values_only=True))
            self.assertEqual(
                cabecalho[:4],
                ("ingrediente", "unidade", "quantidade", "custo_unitario"),
            )
        finally:
            planilha.close()

    def test_modelo_e_aceito_sem_alterar_estoque(self):
        arquivo = SimpleUploadedFile(
            "modelo_estoque.xlsx",
            self.modelo,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        resposta = self.client.post(
            reverse("ingredientes:importar"), {"arquivo": arquivo}, follow=True
        )
        self.assertContains(resposta, "Planilha reconhecida")
        self.assertEqual(Ingrediente.objects.count(), 0)

    def test_arquivo_invalido_e_rejeitado(self):
        arquivo = SimpleUploadedFile("falso.xlsx", b"nao e xlsx")
        resposta = self.client.post(reverse("ingredientes:importar"), {"arquivo": arquivo})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "não pôde ser lido")

    def test_tela_e_download_exigem_login(self):
        self.client.logout()
        for nome in ("ingredientes:importar", "ingredientes:modelo"):
            with self.subTest(nome=nome):
                self.assertEqual(self.client.get(reverse(nome)).status_code, 302)
