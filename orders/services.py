from django.db import transaction
from django.db.models import F
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from cart.models import Carrinho
from catalog.models import Variacao
from orders.models import ItemPedido, Pedido, StatusPedido

class EstoqueInsuficiente(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Estoque Insuficiente'
    default_code = 'estoque_insuficiente'

# UC08: Transições válidas
TRANSICOES = {
    StatusPedido.PENDENTE: {StatusPedido.CONFIRMADO, StatusPedido.CANCELADO},
    StatusPedido.CONFIRMADO: {StatusPedido.ENVIADO, StatusPedido.CANCELADO},
    StatusPedido.ENVIADO: {StatusPedido.ENTREGUE},
    StatusPedido.ENTREGUE: set(),
    StatusPedido.CANCELADO: set(),
}

@transaction.atomic
def criar_pedido(cliente, endereco, metodo):
    carrinho = Carrinho.objects.get(cliente = cliente)
    itens = list(carrinho.itens.select_related('variacao_produto'))

    if not itens:
        raise ValidationError('O carrinho está vazio')

    # Revalida os produtos ativos e estoque de todos os itens
    estoque_vazio = []
    for item in itens:
        variacao = item.variacao

        if not variacao.produto.ativo:
            raise ValidationError(f'O produto "{variacao.produto.nome}" não está ativo. Remova do carrinho ')

        if item.quantidade > variacao.quantidade:
            estoque_vazio.append({
                "id_variacao": variacao.id,
                "produto": variacao.produto.nome,
                "tamanho": variacao.tamanho,
                "cor": variacao.cor,
                "solicitado": item.quantidade,
                "disponivel": variacao.quantidade,
            })

        if estoque_vazio:
            raise EstoqueInsuficiente({"detail": 'Existe itens sem estoque suficiente', "itens": estoque_vazio})

        # Cria o pedido com a cópia do endereço e do pagamento
        pedido = Pedido.objects.create(
            cliente=cliente,
            tipo_pagamento=metodo.tipo,
            ultimos4_pagamento=metodo.ultimos4,
            **endereco,
        )

        # Baixa o estoque e congela o preço de cada item
        itens_pedido = []
        for item in itens:
            baixou = Variacao.objects.filter(
                pk=item.variacao_id, quantidade__gte=item.quantidade
            ).update(quantidade=F('quantidade') - item.quantidade)

            if not baixou:
                raise EstoqueInsuficiente({"detail": 'O estoque mudou durante a compra', "itens": [{"id_variacao": item.id_variacao}]})

            itens_pedido.append(ItemPedido(
                pedido=pedido,
                variacao=item.variacao,
                quantidade=item.quantidade,
                preco_unitario=item.variacao.produto.preco
            ))

        ItemPedido.objects.bulk_create(itens_pedido)

        # Vai esvaziar o carrinho
        carrinho.itens.all().delete()
        return pedido

# Muda o status respeitando as transições. Cancelar devolve para o estoque - UC08
@transaction.atomic
def alterar_status(pedido, novo_status):

   if novo_status not in TRANSICOES[pedido.status]:
       permitidos = ', '.join(sorted(TRANSICOES[pedido.status])) or 'nenhum'
       raise ValidationError(
           f"Transição inválida de {pedido.status} para {novo_status}. "
           f"Permitidos: {permitidos}"
       )

   mudou_status = Pedido.objects.filter(pk = pedido.pk, status = pedido.status).update(status = novo_status)

   if not mudou_status:
       raise ValidationError('O status do pedido mudou. Tente novamente')

   if novo_status == StatusPedido.CANCELADO:
       for item in pedido.itens.all():
           Variacao.objects.filter(pk = item.id_variacao).update(
               quantidade = F('quantidade') + item.quantidade
            )
           
   pedido.refresh_from_db()
   return pedido

