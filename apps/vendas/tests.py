from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .forms import RegistroVendaForm
from .models import RegistroVenda


class RegistroVendaTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            email="vendas@murilos.test", password="SenhaSegura123!"
        )
        self.client.force_login(self.usuario)
        self.dados = {
            "tipo": "SEMANA",
            "data_inicio": "2026-11-01",
            "data_fim": "2026-11-07",
            "total_pedidos": "12",
        }

    def criar_periodo(self, **campos):
        dados = {**self.dados, **campos}
        resposta = self.client.post(reverse("vendas:novo"), dados)
        return resposta

    def test_registra_periodo_e_lista(self):
        resposta = self.criar_periodo()
        self.assertRedirects(resposta, reverse("vendas:listar"))
        periodo = RegistroVenda.objects.get()
        self.assertEqual(periodo.tipo, RegistroVenda.Tipo.SEMANA)
        self.assertEqual(periodo.total_pedidos, 12)
        self.assertEqual(periodo.usuario, self.usuario)
        self.assertContains(self.client.get(reverse("vendas:listar")), "12")

    def test_aceita_zero_pedidos_e_intervalo_adjacente(self):
        self.criar_periodo()
        resposta = self.criar_periodo(
            tipo="DIA", data_inicio="2026-11-08", data_fim="2026-11-08", total_pedidos="0"
        )
        self.assertRedirects(resposta, reverse("vendas:listar"))
        self.assertEqual(RegistroVenda.objects.count(), 2)
        self.assertTrue(RegistroVenda.objects.filter(total_pedidos=0).exists())

    def test_rejeita_pedidos_negativos_e_nao_inteiros(self):
        for valor in ("-1", "1.5", "abc"):
            with self.subTest(valor=valor):
                resposta = self.criar_periodo(total_pedidos=valor)
                self.assertEqual(resposta.status_code, 200)
                self.assertIn("total_pedidos", resposta.context["form"].errors)
        self.assertEqual(RegistroVenda.objects.count(), 0)

    def test_rejeita_datas_invertidas(self):
        resposta = self.criar_periodo(data_inicio="2026-11-08", data_fim="2026-11-01")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("data_fim", resposta.context["form"].errors)
        self.assertEqual(RegistroVenda.objects.count(), 0)

    def test_rejeita_periodos_sobrepostos_independente_do_tipo(self):
        self.criar_periodo()
        casos = [
            ("2026-11-01", "2026-11-07"),
            ("2026-11-03", "2026-11-05"),
            ("2026-10-30", "2026-11-09"),
            ("2026-10-30", "2026-11-01"),
            ("2026-11-07", "2026-11-10"),
        ]
        for inicio, fim in casos:
            with self.subTest(inicio=inicio, fim=fim):
                resposta = self.criar_periodo(tipo="MES", data_inicio=inicio, data_fim=fim)
                self.assertEqual(resposta.status_code, 200)
                self.assertContains(resposta, "Já existe um período de vendas")
        self.assertEqual(RegistroVenda.objects.count(), 1)

    def test_edicao_preserva_periodo_e_rejeita_conflito(self):
        self.criar_periodo()
        primeiro = RegistroVenda.objects.get()
        self.criar_periodo(tipo="DIA", data_inicio="2026-11-08", data_fim="2026-11-08")
        segundo = RegistroVenda.objects.exclude(pk=primeiro.pk).get()
        url = reverse("vendas:editar", args=[segundo.pk])

        resposta = self.client.post(url, {**self.dados, "tipo": "DIA", "data_inicio": "2026-11-07"})
        self.assertContains(resposta, "Já existe um período de vendas")
        segundo.refresh_from_db()
        self.assertEqual(segundo.data_inicio, date(2026, 11, 8))

        resposta = self.client.post(
            url,
            {**self.dados, "tipo": "DIA", "data_inicio": "2026-11-09", "data_fim": "2026-11-09"},
        )
        self.assertRedirects(resposta, reverse("vendas:listar"))
        segundo.refresh_from_db()
        self.assertEqual(segundo.data_inicio, date(2026, 11, 9))

    def test_modelo_e_banco_validam_datas_e_pedidos(self):
        periodo = RegistroVenda(
            tipo="DIA",
            data_inicio=date(2026, 11, 9),
            data_fim=date(2026, 11, 8),
            total_pedidos=0,
            usuario=self.usuario,
        )
        with self.assertRaises(ValidationError):
            periodo.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            periodo.save()

        periodo.data_inicio = date(2026, 11, 8)
        periodo.total_pedidos = -1
        with self.assertRaises(ValidationError):
            periodo.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            periodo.save()

    def test_formulario_modelo_tambem_rejeita_sobreposicao(self):
        self.criar_periodo()
        self.assertFalse(RegistroVendaForm(self.dados).is_valid())
        novo = RegistroVenda(
            tipo="MES",
            data_inicio=date(2026, 11, 7),
            data_fim=date(2026, 11, 30),
            total_pedidos=1,
            usuario=self.usuario,
        )
        with self.assertRaises(ValidationError):
            novo.full_clean()

    def test_paginas_exigem_login(self):
        self.criar_periodo()
        periodo = RegistroVenda.objects.get()
        self.client.logout()
        for url in (
            reverse("vendas:listar"),
            reverse("vendas:novo"),
            reverse("vendas:editar", args=[periodo.pk]),
        ):
            with self.subTest(url=url):
                self.assertRedirects(
                    self.client.get(url), f"{reverse('accounts:entrar')}?next={url}"
                )
        resposta = self.client.post(reverse("vendas:novo"), self.dados)
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(RegistroVenda.objects.count(), 1)
