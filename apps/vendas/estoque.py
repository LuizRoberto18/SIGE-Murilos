"""Baixa e estorno do estoque associados às vendas."""

from collections import defaultdict
from decimal import Decimal

from django.db import transaction

from apps.ingredientes.models import Ingrediente
from apps.pizzas.models import ItemFicha, Pizza

from .models import ItemVenda, Movimentacao, RegistroVenda


class ErroEstoque(Exception):
    """A venda não pode ser aplicada ao estado atual dos cadastros."""


def _itens_enviados(formset):
    itens = {}
    for form in formset.forms:
        dados = form.cleaned_data
        if not dados or dados.get("DELETE") or not dados.get("pizza"):
            continue
        itens[dados["pizza"].pk] = dados["quantidade"]
    return itens


def _fichas_das_pizzas(pizzas_ids):
    pizzas = {
        pizza.pk: pizza
        for pizza in Pizza.objects.select_for_update().filter(pk__in=pizzas_ids, ativo=True)
    }
    if set(pizzas) != set(pizzas_ids):
        raise ErroEstoque("Uma das pizzas não está mais disponível. Atualize a página.")

    fichas = defaultdict(list)
    for item in (
        ItemFicha.objects.select_for_update()
        .select_related("ingrediente")
        .filter(pizza_id__in=pizzas_ids)
    ):
        fichas[item.pizza_id].append(item)
    if any(not fichas[pizza_id] for pizza_id in pizzas_ids):
        raise ErroEstoque("Uma das pizzas está sem ficha técnica. Atualize a página.")
    return pizzas, fichas


@transaction.atomic
def salvar_venda(formset, usuario):
    """Substitui os itens da venda, estornando antes o consumo vigente."""
    enviados = _itens_enviados(formset)
    registro = RegistroVenda.objects.select_for_update().get(pk=formset.instance.pk)
    atuais = dict(registro.itens_venda.values_list("pizza_id", "quantidade"))
    if enviados == atuais and (registro.versao_estoque > 0 or not enviados):
        return False, []

    versao = registro.versao_estoque + 1
    baixas_anteriores = list(
        Movimentacao.objects.filter(
            registro=registro,
            tipo=Movimentacao.Tipo.BAIXA,
            versao=registro.versao_estoque,
        )
    )
    pizzas, fichas = _fichas_das_pizzas(enviados)
    ingredientes_ids = {movimento.ingrediente_id for movimento in baixas_anteriores}
    ingredientes_ids.update(item.ingrediente_id for itens in fichas.values() for item in itens)
    ingredientes = {
        ingrediente.pk: ingrediente
        for ingrediente in Ingrediente.objects.select_for_update().filter(pk__in=ingredientes_ids)
    }

    for baixa in baixas_anteriores:
        ingrediente = ingredientes[baixa.ingrediente_id]
        saldo_anterior = ingrediente.quantidade_estoque
        ingrediente.quantidade_estoque += baixa.quantidade
        ingrediente.save(update_fields=["quantidade_estoque", "atualizado_em"])
        Movimentacao.objects.create(
            registro=registro,
            ingrediente=ingrediente,
            usuario=usuario,
            tipo=Movimentacao.Tipo.ESTORNO,
            versao=versao,
            quantidade=baixa.quantidade,
            custo_unitario=baixa.custo_unitario,
            saldo_anterior=saldo_anterior,
            saldo_posterior=ingrediente.quantidade_estoque,
        )

    formset.instance = registro
    formset.save()
    consumos = defaultdict(Decimal)
    custos_atuais = {
        ingrediente_id: ingrediente.custo_unitario
        for ingrediente_id, ingrediente in ingredientes.items()
    }
    for item in ItemVenda.objects.filter(registro=registro).select_related("pizza"):
        itens_ficha = fichas[item.pizza_id]
        custo = pizzas[item.pizza_id].calcular_custo(itens_ficha, custos_atuais)
        item.preco_unitario = pizzas[item.pizza_id].preco_venda
        item.custo_unitario = custo
        item.save(update_fields=["preco_unitario", "custo_unitario"])
        for ficha in itens_ficha:
            consumos[ficha.ingrediente_id] += ficha.quantidade * item.quantidade

    for ingrediente_id, quantidade in consumos.items():
        if quantidade <= 0:
            continue
        ingrediente = ingredientes[ingrediente_id]
        saldo_anterior = ingrediente.quantidade_estoque
        ingrediente.quantidade_estoque -= quantidade
        ingrediente.save(update_fields=["quantidade_estoque", "atualizado_em"])
        Movimentacao.objects.create(
            registro=registro,
            ingrediente=ingrediente,
            usuario=usuario,
            tipo=Movimentacao.Tipo.BAIXA,
            versao=versao,
            quantidade=quantidade,
            custo_unitario=ingrediente.custo_unitario,
            saldo_anterior=saldo_anterior,
            saldo_posterior=ingrediente.quantidade_estoque,
        )

    registro.versao_estoque = versao
    registro.save(update_fields=["versao_estoque", "atualizado_em"])
    negativos = sorted(
        ingrediente.nome
        for ingrediente in ingredientes.values()
        if ingrediente.quantidade_estoque < 0
    )
    return True, negativos
