from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.ingredientes.models import Ingrediente
from apps.pizzas.models import ItemFicha, Pizza

from .models import ItemVenda, Movimentacao, RegistroVenda


class BaixaEstoqueTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            email="gestor@murilos.test", password="SenhaSegura123!"
        )
        self.client.force_login(self.usuario)
        self.periodo = RegistroVenda.objects.create(
            tipo="DIA",
            data_inicio=date(2026, 11, 26),
            data_fim=date(2026, 11, 26),
            total_pedidos=5,
            usuario=self.usuario,
        )
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
        self.mussarela = Pizza.objects.create(nome="Mussarela", preco_venda=30)
        self.calabresa = Pizza.objects.create(nome="Calabresa", preco_venda=40)
        ItemFicha.objects.create(pizza=self.mussarela, ingrediente=self.queijo, quantidade=100)
        ItemFicha.objects.create(pizza=self.mussarela, ingrediente=self.molho, quantidade=50)
        ItemFicha.objects.create(pizza=self.calabresa, ingrediente=self.queijo, quantidade=80)
        ItemFicha.objects.create(pizza=self.calabresa, ingrediente=self.molho, quantidade=20)
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

    def salvar_venda_inicial(self):
        dados = self.dados_itens(
            (self.mussarela, 2, None, False),
            (self.calabresa, 3, None, False),
        )
        return self.client.post(self.url, dados, follow=True)

    def dados_atuais(self, quantidade_mussarela=2, quantidade_calabresa=3):
        mussarela = ItemVenda.objects.get(pizza=self.mussarela)
        calabresa = ItemVenda.objects.get(pizza=self.calabresa)
        return self.dados_itens(
            (self.mussarela, quantidade_mussarela, mussarela, False),
            (self.calabresa, quantidade_calabresa, calabresa, False),
            iniciais=2,
        )

    def test_soma_consumo_e_registra_baixa_unica(self):
        resposta = self.salvar_venda_inicial()
        self.assertContains(resposta, "Venda salva e estoque atualizado")
        self.queijo.refresh_from_db()
        self.molho.refresh_from_db()
        self.periodo.refresh_from_db()
        self.assertEqual(self.queijo.quantidade_estoque, Decimal("560"))
        self.assertEqual(self.molho.quantidade_estoque, Decimal("340"))
        self.assertEqual(self.periodo.versao_estoque, 1)

        baixas = Movimentacao.objects.filter(tipo=Movimentacao.Tipo.BAIXA)
        self.assertEqual(baixas.count(), 2)
        baixa_queijo = baixas.get(ingrediente=self.queijo)
        self.assertEqual(baixa_queijo.quantidade, Decimal("440"))
        self.assertEqual(baixa_queijo.saldo_anterior, Decimal("1000"))
        self.assertEqual(baixa_queijo.saldo_posterior, Decimal("560"))
        self.assertEqual(baixa_queijo.custo_unitario, Decimal("0.0500"))
        self.assertEqual(baixa_queijo.usuario, self.usuario)

    def test_registra_preco_e_custo_do_momento(self):
        self.salvar_venda_inicial()
        mussarela = ItemVenda.objects.get(pizza=self.mussarela)
        calabresa = ItemVenda.objects.get(pizza=self.calabresa)
        self.assertEqual(mussarela.preco_unitario, Decimal("30.00"))
        self.assertEqual(mussarela.custo_unitario, Decimal("6.0000"))
        self.assertEqual(calabresa.preco_unitario, Decimal("40.00"))
        self.assertEqual(calabresa.custo_unitario, Decimal("4.4000"))

        self.mussarela.preco_venda = 50
        self.mussarela.save()
        self.queijo.custo_unitario = Decimal("0.1000")
        self.queijo.save()
        mussarela.refresh_from_db()
        self.assertEqual(mussarela.preco_unitario, Decimal("30.00"))
        self.assertEqual(mussarela.custo_unitario, Decimal("6.0000"))

    def test_reenvio_identico_nao_duplica_baixa(self):
        self.salvar_venda_inicial()
        resposta = self.client.post(self.url, self.dados_atuais(), follow=True)
        self.assertContains(resposta, "Nenhuma alteração foi identificada")
        self.queijo.refresh_from_db()
        self.molho.refresh_from_db()
        self.periodo.refresh_from_db()
        self.assertEqual(self.queijo.quantidade_estoque, Decimal("560"))
        self.assertEqual(self.molho.quantidade_estoque, Decimal("340"))
        self.assertEqual(self.periodo.versao_estoque, 1)
        self.assertEqual(Movimentacao.objects.count(), 2)

    def test_correcao_estorna_baixa_anterior_e_aplica_nova(self):
        self.salvar_venda_inicial()
        resposta = self.client.post(
            self.url,
            self.dados_atuais(quantidade_mussarela=1, quantidade_calabresa=1),
            follow=True,
        )
        self.assertContains(resposta, "Venda salva e estoque atualizado")
        self.queijo.refresh_from_db()
        self.molho.refresh_from_db()
        self.periodo.refresh_from_db()
        self.assertEqual(self.queijo.quantidade_estoque, Decimal("820"))
        self.assertEqual(self.molho.quantidade_estoque, Decimal("430"))
        self.assertEqual(self.periodo.versao_estoque, 2)
        self.assertEqual(
            Movimentacao.objects.filter(tipo=Movimentacao.Tipo.ESTORNO, versao=2).count(), 2
        )
        self.assertEqual(
            Movimentacao.objects.filter(tipo=Movimentacao.Tipo.BAIXA, versao=2).count(), 2
        )

    def test_remover_pizzas_devolve_todo_consumo(self):
        self.salvar_venda_inicial()
        mussarela = ItemVenda.objects.get(pizza=self.mussarela)
        calabresa = ItemVenda.objects.get(pizza=self.calabresa)
        dados = self.dados_itens(
            (self.mussarela, 2, mussarela, True),
            (self.calabresa, 3, calabresa, True),
            iniciais=2,
        )
        self.client.post(self.url, dados)
        self.queijo.refresh_from_db()
        self.molho.refresh_from_db()
        self.assertEqual(self.queijo.quantidade_estoque, Decimal("1000"))
        self.assertEqual(self.molho.quantidade_estoque, Decimal("500"))
        self.assertEqual(ItemVenda.objects.count(), 0)
        self.assertEqual(Movimentacao.objects.filter(tipo=Movimentacao.Tipo.ESTORNO).count(), 2)

    def test_estoque_negativo_e_sinalizado(self):
        self.queijo.quantidade_estoque = 10
        self.queijo.save()
        resposta = self.client.post(
            self.url,
            self.dados_itens((self.mussarela, 1, None, False)),
            follow=True,
        )
        self.queijo.refresh_from_db()
        self.assertEqual(self.queijo.quantidade_estoque, Decimal("-90"))
        self.assertTrue(self.queijo.estoque_negativo)
        self.assertContains(resposta, "Estoque negativo: Queijo")

    def test_falha_durante_movimentacao_desfaz_venda_e_estoque(self):
        dados = self.dados_itens((self.mussarela, 1, None, False))
        with patch.object(Movimentacao, "save", side_effect=RuntimeError("Falha simulada")):
            with self.assertRaises(RuntimeError):
                self.client.post(self.url, dados)
        self.queijo.refresh_from_db()
        self.molho.refresh_from_db()
        self.periodo.refresh_from_db()
        self.assertEqual(self.queijo.quantidade_estoque, Decimal("1000"))
        self.assertEqual(self.molho.quantidade_estoque, Decimal("500"))
        self.assertEqual(self.periodo.versao_estoque, 0)
        self.assertEqual(ItemVenda.objects.count(), 0)
        self.assertEqual(Movimentacao.objects.count(), 0)

    def test_item_anterior_a_hu10_recebe_baixa_ao_primeiro_salvamento(self):
        item = ItemVenda.objects.create(registro=self.periodo, pizza=self.mussarela, quantidade=1)
        dados = self.dados_itens((self.mussarela, 1, item, False), iniciais=1)
        self.client.post(self.url, dados)
        self.queijo.refresh_from_db()
        self.assertEqual(self.queijo.quantidade_estoque, Decimal("900"))
        self.assertEqual(Movimentacao.objects.filter(tipo=Movimentacao.Tipo.BAIXA).count(), 2)
