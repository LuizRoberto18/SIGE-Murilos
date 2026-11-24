from decimal import Decimal

from django.conf import settings
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


class Importacao(models.Model):
    class Tipo(models.TextChoices):
        COMPRA = "COMPRA", "Compra"
        CONTAGEM = "CONTAGEM", "Contagem"

    identificador = models.UUIDField(unique=True, editable=False)
    hash_conteudo = models.CharField(max_length=64, db_index=True)
    repeticao_autorizada = models.BooleanField(default=False)
    tipo = models.CharField(max_length=8, choices=Tipo.choices)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    nome_arquivo = models.CharField(max_length=255)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["hash_conteudo"],
                condition=models.Q(repeticao_autorizada=False),
                name="importacao_conteudo_unico",
            ),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} #{self.pk}"


class ItemImportacao(models.Model):
    importacao = models.ForeignKey(Importacao, on_delete=models.PROTECT, related_name="itens")
    ingrediente = models.ForeignKey(
        Ingrediente, on_delete=models.PROTECT, related_name="itens_importacao"
    )
    nome_ingrediente = models.CharField(max_length=120)
    unidade = models.CharField(max_length=2, choices=Ingrediente.Unidade.choices)
    quantidade = models.DecimalField(max_digits=12, decimal_places=3)
    custo_unitario = models.DecimalField(max_digits=12, decimal_places=4)
    saldo_anterior = models.DecimalField(max_digits=12, decimal_places=3)
    saldo_posterior = models.DecimalField(max_digits=12, decimal_places=3)
    custo_anterior = models.DecimalField(max_digits=12, decimal_places=4)
    custo_posterior = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        ordering = ["pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["importacao", "ingrediente"], name="item_importacao_unico"
            ),
            models.CheckConstraint(
                condition=models.Q(quantidade__gte=0), name="item_importacao_quantidade_positiva"
            ),
            models.CheckConstraint(
                condition=models.Q(custo_unitario__gte=0), name="item_importacao_custo_positivo"
            ),
        ]

    def __str__(self):
        return f"{self.nome_ingrediente} — {self.importacao}"
