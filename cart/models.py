from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import Cliente
from catalog.models import Variacao

# UC06: Carrinho e ItemCarrinho

class Carrinho(models.Model):
    cliente = models.OneToOneField(
        Cliente, 
        on_delete=models.CASCADE, 
        related_name='carrinho')

    def __str__(self):
        return f'Carrinho de {self.cliente.nome}'

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

    class Meta:
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=["carrinho", "variacao"], name="variacao_unica_por_carrinho"
            ),
            models.CheckConstraint(
                condition=models.Q(quantidade__gte=1), name="item_carrinho_quantidade_minima"
            ),
        ]

    def __str__(self):
        return(
            f'{self.quantidade} x {self.variacao.produto.nome}'
            f'({self.variacao.tamanho} / {self.variacao.cor})')