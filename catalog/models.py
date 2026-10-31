from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

# UC03, UC04 e UC05: Categoria, Produto e Variacao

class Categoria(models.Model):
    nome = models.CharField(max_length= 25, unique=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome

class Produto(models.Model):
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.PROTECT, 
        related_name='produtos'
    )
    nome = models.CharField(max_length= 100)
    preco = models.DecimalField(max_digits= 10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    descricao = models.TextField(blank= True)
    ativo = models.BooleanField(default= True)

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(preco__gt=0), 
                name="produto_preco_positivo",
            )
        ]

    def __str__(self):
        return f'{self.nome} - {self.preco}'

class Variacao(models.Model):
    produto = models.ForeignKey(
        Produto, 
        on_delete=models.PROTECT, 
        related_name='variacoes' 
    )
    tamanho = models.CharField(max_length= 20)
    quantidade = models.PositiveBigIntegerField(default= 0)
    cor = models.CharField(max_length= 50)

    class Meta:
       ordering = ["id"]
       constraints = [
            models.UniqueConstraint(
                fields=["produto", "tamanho", "cor"],
                name="variacao_unica_por_produto",
            )
        ]

    def __str__(self):
            return f'{self.produto.nome} - [Tamanho: {self.tamanho} - Cor: {self.cor}] - Estoque: {self.quantidade}'

