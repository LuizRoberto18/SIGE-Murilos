from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.functions import Lower


class Ingrediente(models.Model):
    class Unidade(models.TextChoices):
        G = "G", "Gramas (g)"
        ML = "ML", "Mililitros (ml)"
        UN = "UN", "Unidades (un)"

    nome = models.CharField(max_length=120)
    unidade = models.CharField(max_length=2, choices=Unidade.choices)
    quantidade_estoque = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    custo_unitario = models.DecimalField(
        max_digits=12, decimal_places=4, validators=[MinValueValidator(Decimal("0"))]
    )
    estoque_minimo = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
    )
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(Lower("nome"), name="ingrediente_nome_ci"),
            models.CheckConstraint(
                condition=models.Q(custo_unitario__gte=0), name="ingrediente_custo_positivo"
            ),
            models.CheckConstraint(
                condition=models.Q(estoque_minimo__gte=0), name="ingrediente_minimo_positivo"
            ),
        ]

    @property
    def estoque_baixo(self):
        return self.quantidade_estoque < self.estoque_minimo

    @property
    def estoque_negativo(self):
        return self.quantidade_estoque < 0

    def __str__(self):
        return self.nome
