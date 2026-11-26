from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.pizzas.models import Pizza


class RegistroVenda(models.Model):
    class Tipo(models.TextChoices):
        DIA = "DIA", "Dia"
        SEMANA = "SEMANA", "Semana"
        MES = "MES", "Mês"

    tipo = models.CharField(max_length=6, choices=Tipo.choices)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    total_pedidos = models.IntegerField(validators=[MinValueValidator(0)])
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    versao_estoque = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ["-data_inicio", "-pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(data_inicio__lte=models.F("data_fim")),
                name="venda_periodo_ordenado",
            ),
            models.CheckConstraint(
                condition=models.Q(total_pedidos__gte=0),
                name="venda_pedidos_positivos",
            ),
        ]

    def clean(self):
        super().clean()
        if not self.data_inicio or not self.data_fim:
            return
        if self.data_inicio > self.data_fim:
            raise ValidationError(
                {"data_fim": "A data final deve ser igual ou posterior à inicial."}
            )

        sobrepostos = RegistroVenda.objects.filter(
            data_inicio__lte=self.data_fim,
            data_fim__gte=self.data_inicio,
        ).exclude(pk=self.pk)
        if sobrepostos.exists():
            raise ValidationError("Já existe um período de vendas que inclui alguma dessas datas.")

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.data_inicio:%d/%m/%Y} a {self.data_fim:%d/%m/%Y}"


class ItemVenda(models.Model):
    registro = models.ForeignKey(
        RegistroVenda, on_delete=models.PROTECT, related_name="itens_venda"
    )
    pizza = models.ForeignKey(Pizza, on_delete=models.PROTECT, related_name="itens_venda")
    quantidade = models.IntegerField(validators=[MinValueValidator(0)])
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    custo_unitario = models.DecimalField(max_digits=14, decimal_places=4, default=0, editable=False)

    class Meta:
        ordering = ["pizza__nome"]
        constraints = [
            models.UniqueConstraint(fields=["registro", "pizza"], name="venda_pizza_unica"),
            models.CheckConstraint(
                condition=models.Q(quantidade__gte=0), name="venda_quantidade_positiva"
            ),
            models.CheckConstraint(
                condition=models.Q(preco_unitario__gte=0), name="venda_preco_positivo"
            ),
            models.CheckConstraint(
                condition=models.Q(custo_unitario__gte=0), name="venda_custo_positivo"
            ),
        ]

    def clean(self):
        super().clean()
        if (
            self.pizza_id
            and not Pizza.objects.filter(
                pk=self.pizza_id, ativo=True, itens_ficha__isnull=False
            ).exists()
        ):
            raise ValidationError({"pizza": "Selecione uma pizza ativa com ficha técnica."})

    def __str__(self):
        return f"{self.pizza}: {self.quantidade} ({self.registro})"


class Movimentacao(models.Model):
    class Tipo(models.TextChoices):
        BAIXA = "BAIXA", "Baixa por venda"
        ESTORNO = "ESTORNO", "Estorno de venda"

    registro = models.ForeignKey(
        RegistroVenda, on_delete=models.PROTECT, related_name="movimentacoes"
    )
    ingrediente = models.ForeignKey(
        "ingredientes.Ingrediente", on_delete=models.PROTECT, related_name="movimentacoes_venda"
    )
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=7, choices=Tipo.choices)
    versao = models.PositiveIntegerField()
    quantidade = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    custo_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0"))],
    )
    saldo_anterior = models.DecimalField(max_digits=12, decimal_places=3)
    saldo_posterior = models.DecimalField(max_digits=12, decimal_places=3)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["criado_em", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["registro", "ingrediente", "tipo", "versao"],
                name="movimento_venda_unico",
            ),
            models.CheckConstraint(
                condition=models.Q(quantidade__gt=0), name="movimento_quantidade_positiva"
            ),
            models.CheckConstraint(
                condition=models.Q(custo_unitario__gte=0), name="movimento_custo_positivo"
            ),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.ingrediente} ({self.quantidade})"
