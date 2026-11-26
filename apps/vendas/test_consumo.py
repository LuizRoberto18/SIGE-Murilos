from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.ingredientes.models import Ingrediente

from .models import Movimentacao, RegistroVenda


class ConsumoIngredienteTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            email="gestor@murilos.test", password="SenhaSegura123!"
        )
        self.client.force_login(self.usuario)
        self.queijo = Ingrediente.objects.create(
            nome="Queijo", unidade="G", quantidade_estoque=1000, custo_unitario=1
        )
        self.molho = Ingrediente.objects.create(
            nome="Molho", unidade="ML", quantidade_estoque=1000, custo_unitario=1
        )
        self.url = reverse("vendas:consumo")

    def criar_periodo(self, inicio, fim, pedidos, tipo=RegistroVenda.Tipo.DIA):
        return RegistroVenda.objects.create(
            tipo=tipo,
            data_inicio=inicio,
            data_fim=fim,
            total_pedidos=pedidos,
            usuario=self.usuario,
        )

    def criar_movimento(self, periodo, ingrediente, quantidade, tipo, versao=1):
        return Movimentacao.objects.create(
            registro=periodo,
            ingrediente=ingrediente,
            usuario=self.usuario,
            tipo=tipo,
            versao=versao,
            quantidade=quantidade,
            custo_unitario=1,
            saldo_anterior=1000,
            saldo_posterior=1000,
        )

    def filtrar(self, inicio, fim):
        return self.client.get(
            self.url,
            {"data_inicio": inicio.isoformat(), "data_fim": fim.isoformat()},
        )

    def item(self, consumo, ingrediente):
        return next(item for item in consumo["itens"] if item["ingrediente"].pk == ingrediente.pk)

    def test_calcula_consumo_total_e_media_por_pedido(self):
        referencia = date(2026, 11, 26)
        periodo = self.criar_periodo(referencia, referencia, 10)
        self.criar_movimento(periodo, self.queijo, 100, Movimentacao.Tipo.BAIXA)
        self.criar_movimento(periodo, self.molho, 50, Movimentacao.Tipo.BAIXA)

        resposta = self.filtrar(referencia, referencia)
        consumo = resposta.context["consumo"]

        self.assertEqual(consumo["pedidos"], Decimal("10.00"))
        self.assertEqual(self.item(consumo, self.queijo)["total"], Decimal("100.000"))
        self.assertEqual(self.item(consumo, self.queijo)["media_pedido"], Decimal("10.000"))
        self.assertContains(resposta, "100 G")
        self.assertContains(resposta, "5 ML")

    def test_filtro_considera_apenas_periodos_sobrepostos(self):
        primeiro_dia = date(2026, 11, 25)
        segundo_dia = date(2026, 11, 26)
        primeiro = self.criar_periodo(primeiro_dia, primeiro_dia, 2)
        segundo = self.criar_periodo(segundo_dia, segundo_dia, 4)
        self.criar_movimento(primeiro, self.queijo, 20, Movimentacao.Tipo.BAIXA)
        self.criar_movimento(segundo, self.queijo, 80, Movimentacao.Tipo.BAIXA)

        consumo = self.filtrar(segundo_dia, segundo_dia).context["consumo"]

        self.assertEqual(consumo["periodos_considerados"], 1)
        self.assertEqual(self.item(consumo, self.queijo)["total"], Decimal("80.000"))
        self.assertEqual(self.item(consumo, self.queijo)["media_pedido"], Decimal("20.000"))

    def test_estorno_compensa_baixa_corrigida(self):
        referencia = date(2026, 11, 26)
        periodo = self.criar_periodo(referencia, referencia, 4)
        self.criar_movimento(periodo, self.queijo, 100, Movimentacao.Tipo.BAIXA)
        self.criar_movimento(periodo, self.queijo, 100, Movimentacao.Tipo.ESTORNO, versao=2)
        self.criar_movimento(periodo, self.queijo, 40, Movimentacao.Tipo.BAIXA, versao=2)

        consumo = self.filtrar(referencia, referencia).context["consumo"]

        self.assertEqual(self.item(consumo, self.queijo)["total"], Decimal("40.000"))
        self.assertEqual(self.item(consumo, self.queijo)["media_pedido"], Decimal("10.000"))

    def test_intervalo_parcial_proporciona_consumo_e_pedidos(self):
        inicio = date(2026, 11, 23)
        fim = date(2026, 11, 29)
        periodo = self.criar_periodo(inicio, fim, 70, RegistroVenda.Tipo.SEMANA)
        self.criar_movimento(periodo, self.queijo, 700, Movimentacao.Tipo.BAIXA)

        consumo = self.filtrar(date(2026, 11, 25), date(2026, 11, 25)).context["consumo"]

        self.assertTrue(consumo["valores_proporcionais"])
        self.assertEqual(consumo["pedidos"], Decimal("10.00"))
        self.assertEqual(self.item(consumo, self.queijo)["total"], Decimal("100.000"))
        self.assertEqual(self.item(consumo, self.queijo)["media_pedido"], Decimal("10.000"))

    def test_zero_pedidos_retorna_media_zero(self):
        referencia = date(2026, 11, 26)
        periodo = self.criar_periodo(referencia, referencia, 0)
        self.criar_movimento(periodo, self.queijo, 20, Movimentacao.Tipo.BAIXA)

        resposta = self.filtrar(referencia, referencia)
        consumo = resposta.context["consumo"]

        self.assertEqual(consumo["pedidos"], Decimal("0.00"))
        self.assertEqual(self.item(consumo, self.queijo)["media_pedido"], Decimal("0.000"))
        self.assertContains(resposta, "possui zero pedidos")

    def test_datas_invalidas_nao_executam_consulta(self):
        resposta = self.client.get(
            self.url,
            {"data_inicio": "2026-11-27", "data_fim": "2026-11-26"},
        )

        self.assertIsNone(resposta.context["consumo"])
        self.assertIn("data_fim", resposta.context["form"].errors)

    def test_pagina_exige_login(self):
        self.client.logout()
        self.assertRedirects(
            self.client.get(self.url), f"{reverse('accounts:entrar')}?next={self.url}"
        )
