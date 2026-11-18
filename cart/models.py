from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import Cliente
from catalog.models import Variacao

# Cada cliente possui um único carrinho e ele armazerna os itens até o final da compra
class Carrinho(models.Model):
    cliente = models.OneToOneField(
        Cliente, 
        on_delete=models.CASCADE, 
        related_name='carrinho')

    def __str__(self):
        return f'Carrinho de {self.cliente.nome}'

# Cada variação adicionada ao carrinho, guardando sua quantidade e impedindo duplicatas da mesma variação
class ItemCarrinho(models.Model):
    carrinho = models.ForeignKey(
        Carrinho, 
        on_delete=models.CASCADE, 
        related_name='itens'
    )
    variacao = models.ForeignKey(
        Variacao, 
        on_delete=models.PROTECT, 
        related_name='itens_carrinho'
    )
    quantidade = models.PositiveBigIntegerField(default= 1, validators=[MinValueValidator(1)]) # Quantidade mínima começa com 1 ao adicionar

    # Garante que a variação apareça apenas uma vez no carrinho
    class Meta:
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=["carrinho", "variacao"], name="variacao_unica_por_carrinho"
            ),
            # Quantidade de itens seja sempre maior ou igual a um
            models.CheckConstraint(
                condition=models.Q(quantidade__gte=1), name="item_carrinho_quantidade_minima"
            ),
        ]

    def __str__(self):
        return(
            f'{self.quantidade} x {self.variacao.produto.nome}'
            f'({self.variacao.tamanho} / {self.variacao.cor})')