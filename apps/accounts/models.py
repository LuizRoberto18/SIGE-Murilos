from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class GerenciadorUsuario(BaseUserManager):
    def create_user(self, email, password=None, **campos):
        if not email:
            raise ValueError("O e-mail é obrigatório.")
        usuario = self.model(email=self.normalize_email(email), **campos)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, password=None, **campos):
        campos.setdefault("is_staff", True)
        campos.setdefault("is_superuser", True)
        if campos["is_staff"] is not True or campos["is_superuser"] is not True:
            raise ValueError("Superusuário deve ter is_staff e is_superuser.")
        return self.create_user(email, password, **campos)


class Usuario(AbstractUser):
    username = None
    email = models.EmailField("e-mail", unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = GerenciadorUsuario()

    def __str__(self):
        return self.email
