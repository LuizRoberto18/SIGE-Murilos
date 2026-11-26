from datetime import date
from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.ingredientes.models import Importacao, Ingrediente, ItemImportacao
from apps.vendas.models import Movimentacao, RegistroVenda


class HistoricoMovimentacoesTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            email="gestor@murilos.test", password="SenhaSegura123!"
        )
        self.ingrediente = Ingrediente.objects.create(
            nome="Queijo",
            unidade="G",
            quantidade_estoque=20,
            custo_unitario=Decimal("0.0500"),
        )
        self.outro = Ingrediente.objects.create(
            nome="Molho",
            unidade="ML",
            quantidade_estoque=10,
            custo_unitario=Decimal("0.0200"),
        )
        self.periodo = RegistroVenda.objects.create(
            tipo="DIA",
            data_inicio=date(2026, 11, 26),
            data_fim=date(2026, 11, 26),
            total_pedidos=1,
            usuario=self.usuario,
        )
        self.url = reverse("core:movimentacoes")
        self.client.force_login(self.usuario)

    def criar_importacao(self, tipo, ingrediente=None, anterior=10, posterior=15):
        ingrediente = ingrediente or self.ingrediente
        importacao = Importacao.objects.create(
            identificador=uuid4(),
            hash_conteudo=uuid4().hex,
            tipo=tipo,
            usuario=self.usuario,
            nome_arquivo="estoque.csv",
        )
        ItemImportacao.objects.create(
            importacao=importacao,
            ingrediente=ingrediente,
            nome_ingrediente=ingrediente.nome,
            unidade=ingrediente.unidade,
            quantidade=abs(Decimal(str(posterior))),
            custo_unitario=ingrediente.custo_unitario,
            saldo_anterior=anterior,
            saldo_posterior=posterior,
            custo_anterior=ingrediente.custo_unitario,
            custo_posterior=ingrediente.custo_unitario,
        )
        return importacao

    def criar_movimento(self, tipo, versao, ingrediente=None, anterior=15, posterior=11):
        ingrediente = ingrediente or self.ingrediente
        return Movimentacao.objects.create(
            registro=self.periodo,
            ingrediente=ingrediente,
            usuario=self.usuario,
            tipo=tipo,
            versao=versao,
            quantidade=abs(Decimal(str(posterior - anterior))),
            custo_unitario=ingrediente.custo_unitario,
            saldo_anterior=anterior,
            saldo_posterior=posterior,
        )

    def test_exige_login(self):
        self.client.logout()
        self.assertRedirects(
            self.client.get(self.url), f"{reverse('accounts:entrar')}?next={self.url}"
        )

    def test_banco_vazio(self):
        resposta = self.client.get(self.url)
        self.assertContains(resposta, "Nenhuma movimentação encontrada")
        self.assertEqual(resposta.context["pagina"].paginator.count, 0)

    def test_reune_importacoes_baixas_e_estornos(self):
        compra = self.criar_importacao(Importacao.Tipo.COMPRA, anterior=10, posterior=15)
        contagem = self.criar_importacao(Importacao.Tipo.CONTAGEM, anterior=15, posterior=12)
        self.criar_movimento(Movimentacao.Tipo.BAIXA, 1, anterior=12, posterior=8)
        self.criar_movimento(Movimentacao.Tipo.ESTORNO, 2, anterior=8, posterior=12)

        resposta = self.client.get(self.url)
        registros = list(resposta.context["pagina"])
        self.assertEqual(len(registros), 4)
        self.assertEqual(
            {registro["diferenca"] for registro in registros},
            {Decimal("5"), Decimal("-3"), Decimal("-4"), Decimal("4")},
        )
        self.assertContains(resposta, "Compra")
        self.assertContains(resposta, "Contagem")
        self.assertContains(resposta, "Baixa por venda")
        self.assertContains(resposta, "Estorno de venda")
        self.assertContains(resposta, self.usuario.email)
        self.assertContains(resposta, reverse("ingredientes:detalhe_importacao", args=[compra.pk]))
        self.assertContains(
            resposta, reverse("ingredientes:detalhe_importacao", args=[contagem.pk])
        )
        self.assertContains(resposta, reverse("vendas:pizzas", args=[self.periodo.pk]))

    def test_filtra_por_origem_e_ingrediente(self):
        self.criar_importacao(Importacao.Tipo.COMPRA)
        self.criar_importacao(Importacao.Tipo.CONTAGEM, ingrediente=self.outro)
        self.criar_movimento(Movimentacao.Tipo.BAIXA, 1)

        resposta = self.client.get(self.url, {"origem": Importacao.Tipo.COMPRA})
        self.assertEqual(resposta.context["pagina"].paginator.count, 1)
        self.assertEqual(list(resposta.context["pagina"])[0]["origem"], "Compra")

        resposta = self.client.get(self.url, {"ingrediente": self.outro.pk})
        self.assertEqual(resposta.context["pagina"].paginator.count, 1)
        self.assertEqual(list(resposta.context["pagina"])[0]["ingrediente"], "Molho")

    def test_historico_permanece_apos_novos_lancamentos(self):
        importacao = self.criar_importacao(Importacao.Tipo.COMPRA)
        resposta_inicial = self.client.get(self.url)
        self.assertEqual(resposta_inicial.context["pagina"].paginator.count, 1)

        self.criar_movimento(Movimentacao.Tipo.BAIXA, 1)
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.context["pagina"].paginator.count, 2)
        self.assertContains(resposta, f"Importação #{importacao.pk}")
        self.assertContains(resposta, f"Venda #{self.periodo.pk}")

    def test_paginação_preserva_filtros(self):
        for versao in range(1, 27):
            self.criar_movimento(
                Movimentacao.Tipo.BAIXA,
                versao,
                anterior=100 - versao,
                posterior=99 - versao,
            )
        resposta = self.client.get(self.url, {"origem": Movimentacao.Tipo.BAIXA})
        self.assertEqual(len(resposta.context["pagina"]), 25)
        self.assertContains(resposta, "origem=BAIXA&amp;pagina=2")

    def test_rejeita_intervalo_de_datas_invertido(self):
        resposta = self.client.get(
            self.url, {"data_inicio": "2026-11-27", "data_fim": "2026-11-26"}
        )
        self.assertContains(resposta, "A data final deve ser igual ou posterior à inicial")
