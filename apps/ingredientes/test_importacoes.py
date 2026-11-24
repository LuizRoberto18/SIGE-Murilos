from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse

from .models import Importacao, Ingrediente, ItemImportacao


class ConfirmacaoImportacaoTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            email="estoque@murilos.test", password="SenhaSegura123!"
        )
        self.client.force_login(self.usuario)
        self.farinha = Ingrediente.objects.create(
            nome="Farinha", unidade="G", quantidade_estoque=10, custo_unitario=2
        )

    def enviar_csv(self, linhas):
        cabecalho = "ingrediente;unidade;quantidade;custo_unitario\n"
        arquivo = SimpleUploadedFile(
            "estoque.csv", (cabecalho + linhas).encode("utf-8"), content_type="text/csv"
        )
        return self.client.post(reverse("ingredientes:importar"), {"arquivo": arquivo})

    def confirmar(self, tipo="COMPRA", token=None, repetir=False):
        token = token or self.client.session["importacao_pendente"]["token"]
        return self.client.post(
            reverse("ingredientes:confirmar_importacao"),
            {"token": token, "tipo": tipo, "repetir": "on" if repetir else ""},
            follow=True,
        )

    def test_compra_soma_quantidade_e_calcula_custo_medio(self):
        resposta = self.enviar_csv("Farinha;G;5;4\n")
        self.assertContains(resposta, "Confirmar atualização")
        self.farinha.refresh_from_db()
        self.assertEqual(self.farinha.quantidade_estoque, Decimal("10"))
        self.assertEqual(Importacao.objects.count(), 0)

        resposta = self.confirmar()
        self.farinha.refresh_from_db()
        self.assertEqual(self.farinha.quantidade_estoque, Decimal("15"))
        self.assertEqual(self.farinha.custo_unitario, Decimal("2.6667"))
        registro = Importacao.objects.get()
        self.assertEqual(registro.usuario, self.usuario)
        self.assertEqual(registro.tipo, Importacao.Tipo.COMPRA)
        self.assertContains(resposta, "Farinha")
        item = registro.itens.get()
        self.assertEqual(item.saldo_anterior, Decimal("10"))
        self.assertEqual(item.saldo_posterior, Decimal("15"))
        self.assertEqual(item.custo_anterior, Decimal("2"))
        self.assertEqual(item.custo_posterior, Decimal("2.6667"))

    def test_contagem_substitui_saldo_e_custo(self):
        self.enviar_csv("Farinha;G;3;7\n")
        self.confirmar("CONTAGEM")
        self.farinha.refresh_from_db()
        self.assertEqual(self.farinha.quantidade_estoque, Decimal("3"))
        self.assertEqual(self.farinha.custo_unitario, Decimal("7"))
        self.assertEqual(Importacao.objects.get().tipo, Importacao.Tipo.CONTAGEM)

    def test_compra_cria_ingrediente_novo_com_unidade_base(self):
        self.enviar_csv("Queijo;KG;1,5;12,50\n")
        self.confirmar()
        queijo = Ingrediente.objects.get(nome="Queijo")
        self.assertEqual(queijo.unidade, "G")
        self.assertEqual(queijo.quantidade_estoque, Decimal("1500"))
        self.assertEqual(queijo.custo_unitario, Decimal("0.0125"))

    def test_planilha_invalida_nao_pode_ser_confirmada(self):
        resposta = self.enviar_csv("Farinha;G;-1;4\n")
        self.assertNotContains(resposta, "Confirmar atualização")
        self.assertNotIn("importacao_pendente", self.client.session)
        self.assertEqual(Importacao.objects.count(), 0)

    def test_reenvio_do_mesmo_token_nao_aplica_duas_vezes(self):
        self.enviar_csv("Farinha;G;5;4\n")
        token = self.client.session["importacao_pendente"]["token"]
        self.confirmar(token=token)
        resposta = self.confirmar(token=token)
        self.farinha.refresh_from_db()
        self.assertEqual(self.farinha.quantidade_estoque, Decimal("15"))
        self.assertEqual(Importacao.objects.count(), 1)
        self.assertEqual(ItemImportacao.objects.count(), 1)
        self.assertContains(resposta, "já foi confirmada")

    def test_reenvio_do_mesmo_conteudo_exige_confirmacao_de_repeticao(self):
        self.enviar_csv("Farinha;G;5;4\n")
        self.confirmar()
        self.enviar_csv("Farinha;G;5;4\n")

        resposta = self.confirmar()
        self.assertContains(resposta, "já foi confirmada")
        self.farinha.refresh_from_db()
        self.assertEqual(self.farinha.quantidade_estoque, Decimal("15"))
        self.assertEqual(Importacao.objects.count(), 1)

        self.confirmar(repetir=True)
        self.farinha.refresh_from_db()
        self.assertEqual(self.farinha.quantidade_estoque, Decimal("20"))
        self.assertEqual(Importacao.objects.count(), 2)
        self.assertTrue(Importacao.objects.filter(repeticao_autorizada=True).exists())

    def test_falha_em_uma_linha_desfaz_toda_a_importacao(self):
        molho = Ingrediente.objects.create(
            nome="Molho", unidade="G", quantidade_estoque=10, custo_unitario=1
        )
        self.enviar_csv("Farinha;G;5;4\nMolho;G;2;3\n")
        molho.unidade = "ML"
        molho.save()

        resposta = self.confirmar()
        self.assertContains(resposta, "A unidade de Molho mudou")
        self.farinha.refresh_from_db()
        self.assertEqual(self.farinha.quantidade_estoque, Decimal("10"))
        self.assertEqual(Importacao.objects.count(), 0)
        self.assertEqual(ItemImportacao.objects.count(), 0)

    def test_compra_com_saldo_negativo_usa_custo_da_entrada(self):
        self.farinha.quantidade_estoque = Decimal("-2")
        self.farinha.save()
        self.enviar_csv("Farinha;G;5;4\n")
        self.confirmar()
        self.farinha.refresh_from_db()
        self.assertEqual(self.farinha.quantidade_estoque, Decimal("3"))
        self.assertEqual(self.farinha.custo_unitario, Decimal("4"))

    def test_historico_protege_relacionamentos(self):
        self.enviar_csv("Farinha;G;5;4\n")
        self.confirmar()
        item = ItemImportacao.objects.get()
        self.farinha.nome = "Farinha nova"
        self.farinha.save()
        self.assertEqual(item.nome_ingrediente, "Farinha")
        with self.assertRaises(ProtectedError):
            self.farinha.delete()

    def test_confirmacao_exige_login_e_post(self):
        self.enviar_csv("Farinha;G;5;4\n")
        token = self.client.session["importacao_pendente"]["token"]
        self.assertEqual(
            self.client.get(reverse("ingredientes:confirmar_importacao")).status_code, 405
        )
        self.client.logout()
        resposta = self.client.post(
            reverse("ingredientes:confirmar_importacao"), {"token": token, "tipo": "COMPRA"}
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Importacao.objects.count(), 0)

    def test_tipo_invalido_nao_altera_estoque(self):
        self.enviar_csv("Farinha;G;5;4\n")
        self.confirmar("OUTRO")
        self.farinha.refresh_from_db()
        self.assertEqual(self.farinha.quantidade_estoque, Decimal("10"))
        self.assertEqual(Importacao.objects.count(), 0)
