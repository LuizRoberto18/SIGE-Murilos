from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AutenticacaoTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            email="admin@murilos.test", password="SenhaSegura123!"
        )

    def test_login_valido_e_redirecionamento(self):
        destino = reverse("ingredientes:listar")
        resposta = self.client.post(
            reverse("accounts:entrar"),
            {"email": self.usuario.email, "senha": "SenhaSegura123!", "next": destino},
        )
        self.assertRedirects(resposta, destino)

    def test_login_invalido(self):
        resposta = self.client.post(
            reverse("accounts:entrar"),
            {"email": self.usuario.email, "senha": "errada"},
        )
        self.assertContains(resposta, "E-mail ou senha inválidos")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_redirecionamento_externo_e_bloqueado(self):
        resposta = self.client.post(
            reverse("accounts:entrar"),
            {
                "email": self.usuario.email,
                "senha": "SenhaSegura123!",
                "next": "https://externo.test",
            },
        )
        self.assertRedirects(resposta, reverse("core:dashboard"))

    def test_logout_exige_post(self):
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get(reverse("accounts:sair")).status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)
        resposta = self.client.post(reverse("accounts:sair"))
        self.assertRedirects(resposta, reverse("accounts:entrar"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_admin_de_usuarios(self):
        admin = get_user_model().objects.create_superuser(
            email="super@murilos.test", password="SenhaSegura123!"
        )
        self.client.force_login(admin)
        self.assertEqual(self.client.get(reverse("admin:accounts_usuario_add")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("admin:accounts_usuario_changelist")).status_code, 200
        )
