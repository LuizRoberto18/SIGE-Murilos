from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


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
