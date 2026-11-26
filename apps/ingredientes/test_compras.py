from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.vendas.models import Movimentacao, RegistroVenda

from .models import Ingrediente


class SugestoesComprasTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            email="gestor@murilos.test", password="SenhaSegura123!"
        )
        self.client.force_login(self.usuario)
        self.periodo = RegistroVenda.objects.create(
            tipo=RegistroVenda.Tipo.SEMANA,
            data_inicio=date(2026, 11, 1),
            data_fim=date(2026, 11, 5),
            total_pedidos=10,
            usuario=self.usuario,
        )
        self.critico = self.criar_ingrediente("Queijo", 5, 20)
        self.projetado = self.criar_ingrediente("Molho", 100, 20, unidade="ML")
        self.no_minimo = self.criar_ingrediente("Farinha", 10, 10)
        self.inativo = self.criar_ingrediente("Inativo", 0, 100, ativo=False)
        self.criar_movimento(self.critico, Movimentacao.Tipo.BAIXA, 1, 100)
        self.criar_movimento(self.critico, Movimentacao.Tipo.ESTORNO, 2, 100)
        self.criar_movimento(self.critico, Movimentacao.Tipo.BAIXA, 2, 50)
        self.criar_movimento(self.projetado, Movimentacao.Tipo.BAIXA, 1, 100)
        self.url = reverse("ingredientes:sugestoes")

    def criar_ingrediente(self, nome, saldo, minimo, unidade="G", ativo=True):
        return Ingrediente.objects.create(
            nome=nome,
            unidade=unidade,
            quantidade_estoque=saldo,
            custo_unitario=Decimal("0.0500"),
            estoque_minimo=minimo,
            ativo=ativo,
        )

    def criar_movimento(self, ingrediente, tipo, versao, quantidade):
        return Movimentacao.objects.create(
            registro=self.periodo,
            ingrediente=ingrediente,
            usuario=self.usuario,
            tipo=tipo,
            versao=versao,
            quantidade=quantidade,
            custo_unitario=ingrediente.custo_unitario,
            saldo_anterior=1000,
            saldo_posterior=1000,
        )

    def test_cobertura_padrao_e_formula_consideram_baixas_e_estornos(self):
        resposta = self.client.get(self.url)
        resultado = resposta.context["resultado"]
        sugestoes = {item["ingrediente"].nome: item for item in resultado["sugestoes"]}

        self.assertEqual(resposta.context["dias_cobertura"], 7)
        self.assertEqual(resultado["dias_historico"], 5)
        self.assertEqual(sugestoes["Queijo"]["consumo_medio"], Decimal("10.000"))
        self.assertEqual(sugestoes["Queijo"]["quantidade"], Decimal("85.000"))
        self.assertEqual(sugestoes["Molho"]["consumo_medio"], Decimal("20.000"))
        self.assertEqual(sugestoes["Molho"]["quantidade"], Decimal("60.000"))

    def test_alerta_inclui_saldo_igual_ao_minimo(self):
        resposta = self.client.get(self.url)

        self.assertTrue(self.no_minimo.estoque_baixo)
        self.assertEqual(resposta.context["resultado"]["total_criticos"], 2)
        dashboard = self.client.get(reverse("core:dashboard"))
        self.assertEqual(dashboard.context["total_baixos"], 2)
        self.assertContains(dashboard, self.no_minimo.nome)

    def test_cobertura_pode_ser_configurada(self):
        resposta = self.client.get(self.url, {"dias_cobertura": 3})
        sugestoes = resposta.context["resultado"]["sugestoes"]

        self.assertEqual(resposta.context["dias_cobertura"], 3)
        self.assertEqual(len(sugestoes), 1)
        self.assertEqual(sugestoes[0]["ingrediente"], self.critico)
        self.assertEqual(sugestoes[0]["quantidade"], Decimal("45.000"))

    def test_exibe_apenas_sugestoes_positivas_e_ingredientes_ativos(self):
        resposta = self.client.get(self.url)
        nomes = [item["ingrediente"].nome for item in resposta.context["resultado"]["sugestoes"]]

        self.assertEqual(nomes, ["Queijo", "Molho"])
        self.assertNotIn(self.no_minimo.nome, nomes)
        self.assertNotIn(self.inativo.nome, nomes)

    def test_cobertura_invalida_nao_calcula_sugestoes(self):
        resposta = self.client.get(self.url, {"dias_cobertura": 0})

        self.assertIsNone(resposta.context["resultado"])
        self.assertIn("dias_cobertura", resposta.context["form"].errors)

    def test_consulta_exige_login(self):
        self.client.logout()
        self.assertRedirects(
            self.client.get(self.url), f"{reverse('accounts:entrar')}?next={self.url}"
        )
