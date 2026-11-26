from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.ingredientes.models import Ingrediente
from apps.pizzas.models import ItemFicha, Pizza
from apps.vendas.models import ItemVenda, RegistroVenda


class PainelIndicadoresTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            email="gestor@murilos.test", password="SenhaSegura123!"
        )
        self.client.force_login(self.usuario)
        ingrediente = Ingrediente.objects.create(
            nome="Queijo", unidade="G", quantidade_estoque=1000, custo_unitario=1
        )
        self.mussarela = Pizza.objects.create(nome="Mussarela", preco_venda=30)
        self.calabresa = Pizza.objects.create(nome="Calabresa", preco_venda=40)
        ItemFicha.objects.create(pizza=self.mussarela, ingrediente=ingrediente, quantidade=10)
        ItemFicha.objects.create(pizza=self.calabresa, ingrediente=ingrediente, quantidade=8)
        self.url = reverse("core:dashboard")

    def criar_periodo(self, tipo, inicio, fim, pedidos, *itens):
        periodo = RegistroVenda.objects.create(
            tipo=tipo,
            data_inicio=inicio,
            data_fim=fim,
            total_pedidos=pedidos,
            usuario=self.usuario,
        )
        for pizza, quantidade, preco, custo in itens:
            ItemVenda.objects.create(
                registro=periodo,
                pizza=pizza,
                quantidade=quantidade,
                preco_unitario=preco,
                custo_unitario=custo,
            )
        return periodo

    def filtrar(self, granularidade, referencia):
        return self.client.get(
            self.url,
            {"granularidade": granularidade, "data_referencia": referencia.isoformat()},
        )

    def test_calcula_pedidos_custos_faturamento_lucro_e_ranking(self):
        referencia = date(2026, 11, 26)
        self.criar_periodo(
            RegistroVenda.Tipo.DIA,
            referencia,
            referencia,
            10,
            (self.mussarela, 5, 30, 10),
            (self.calabresa, 2, 40, 20),
        )

        indicadores = self.filtrar("DIA", referencia).context["indicadores"]

        self.assertEqual(indicadores["pedidos"], Decimal("10.00"))
        self.assertEqual(indicadores["custo"], Decimal("90.00"))
        self.assertEqual(indicadores["faturamento"], Decimal("230.00"))
        self.assertEqual(indicadores["lucro"], Decimal("140.00"))
        self.assertEqual(
            [item["pizza"] for item in indicadores["mais_vendidos"]],
            [self.mussarela, self.calabresa],
        )
        self.assertEqual(indicadores["mais_vendidos"][0]["margem"], Decimal("66.67"))
        self.assertEqual(indicadores["mais_vendidos"][1]["margem"], Decimal("50.00"))

    def test_filtros_usam_dia_semana_e_mes_da_data_escolhida(self):
        dia_semana = date(2026, 11, 24)
        outro_mes = date(2026, 12, 1)
        self.criar_periodo(
            RegistroVenda.Tipo.DIA,
            dia_semana,
            dia_semana,
            4,
            (self.mussarela, 2, 30, 10),
        )
        self.criar_periodo(
            RegistroVenda.Tipo.DIA,
            outro_mes,
            outro_mes,
            7,
            (self.calabresa, 3, 40, 20),
        )

        dia = self.filtrar("DIA", dia_semana).context["indicadores"]
        semana = self.filtrar("SEMANA", date(2026, 11, 26)).context["indicadores"]
        mes = self.filtrar("MES", outro_mes).context["indicadores"]

        self.assertEqual((dia["inicio"], dia["fim"]), (dia_semana, dia_semana))
        self.assertEqual(
            (semana["inicio"], semana["fim"]), (date(2026, 11, 23), date(2026, 11, 29))
        )
        self.assertEqual((mes["inicio"], mes["fim"]), (date(2026, 12, 1), date(2026, 12, 31)))
        self.assertEqual(dia["pedidos"], Decimal("4.00"))
        self.assertEqual(semana["pedidos"], Decimal("4.00"))
        self.assertEqual(mes["pedidos"], Decimal("7.00"))

    def test_dia_derivado_de_semana_e_identificado_como_media(self):
        self.criar_periodo(
            RegistroVenda.Tipo.SEMANA,
            date(2026, 1, 5),
            date(2026, 1, 11),
            70,
            (self.mussarela, 70, 10, 4),
        )

        resposta = self.filtrar("DIA", date(2026, 1, 7))
        indicadores = resposta.context["indicadores"]

        self.assertTrue(indicadores["medias_diarias"])
        self.assertEqual(indicadores["pedidos"], Decimal("10.00"))
        self.assertEqual(indicadores["faturamento"], Decimal("100.00"))
        self.assertEqual(indicadores["custo"], Decimal("40.00"))
        self.assertContains(resposta, "médias diárias estimadas")

    def test_dia_derivado_de_mes_usa_quantidade_media(self):
        self.criar_periodo(
            RegistroVenda.Tipo.MES,
            date(2026, 2, 1),
            date(2026, 2, 28),
            280,
            (self.calabresa, 140, 10, 4),
        )

        indicadores = self.filtrar("DIA", date(2026, 2, 14)).context["indicadores"]

        self.assertTrue(indicadores["medias_diarias"])
        self.assertEqual(indicadores["pedidos"], Decimal("10.00"))
        self.assertEqual(indicadores["mais_vendidos"][0]["quantidade"], Decimal("5.00"))
        self.assertEqual(indicadores["lucro"], Decimal("30.00"))

    def test_usa_preco_e_custo_historicos_da_venda(self):
        referencia = date(2026, 11, 26)
        self.criar_periodo(
            RegistroVenda.Tipo.DIA,
            referencia,
            referencia,
            1,
            (self.mussarela, 1, 30, 10),
        )
        self.mussarela.preco_venda = 90
        self.mussarela.save()

        indicadores = self.filtrar("DIA", referencia).context["indicadores"]

        self.assertEqual(indicadores["faturamento"], Decimal("30.00"))
        self.assertEqual(indicadores["custo"], Decimal("10.00"))

    def test_banco_vazio_e_filtro_invalido(self):
        vazio = self.filtrar("MES", date(2026, 11, 26)).context["indicadores"]
        self.assertEqual(vazio["pedidos"], Decimal("0.00"))
        self.assertEqual(vazio["mais_vendidos"], [])

        invalido = self.client.get(
            self.url, {"granularidade": "ANO", "data_referencia": "inválida"}
        )
        self.assertIsNone(invalido.context["indicadores"])
        self.assertTrue(invalido.context["filtro"].errors)

    def test_painel_exige_login(self):
        self.client.logout()
        self.assertRedirects(
            self.client.get(self.url), f"{reverse('accounts:entrar')}?next={self.url}"
        )
