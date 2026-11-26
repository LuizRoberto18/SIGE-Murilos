from decimal import ROUND_HALF_UP, Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.functions import Lower


class Pizza(models.Model):
    nome = models.CharField(max_length=120)
    preco_venda = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(Lower("nome"), name="pizza_nome_ci"),
            models.CheckConstraint(
                condition=models.Q(preco_venda__gt=0), name="pizza_preco_positivo"
            ),
        ]

    @property
    def ficha_pendente(self):
        return not self.itens_ficha.exists()

    def calcular_custo(self, itens=None, custos=None):
        if itens is None:
            itens = getattr(self, "_prefetched_objects_cache", {}).get("itens_ficha")
        if itens is None:
            itens = self.itens_ficha.select_related("ingrediente")
        total = sum(
            (
                item.quantidade
                * (
                    custos[item.ingrediente_id]
                    if custos is not None
                    else item.ingrediente.custo_unitario
                )
                for item in itens
            ),
            Decimal("0"),
        )
        return total.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    @property
    def custo_atual(self):
        return self.calcular_custo()

    def __str__(self):
        return self.nome


class ItemFicha(models.Model):
    pizza = models.ForeignKey(Pizza, on_delete=models.PROTECT, related_name="itens_ficha")
    ingrediente = models.ForeignKey(
        "ingredientes.Ingrediente", on_delete=models.PROTECT, related_name="itens_ficha"
    )
    quantidade = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )

    class Meta:
        ordering = ["ingrediente__nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["pizza", "ingrediente"], name="ficha_ingrediente_unico"
            ),
            models.CheckConstraint(
                condition=models.Q(quantidade__gt=0), name="ficha_quantidade_positiva"
            ),
        ]

    @property
    def custo_atual(self):
        return self.quantidade * self.ingrediente.custo_unitario

    def __str__(self):
        return f"{self.pizza}: {self.ingrediente} ({self.quantidade})"
