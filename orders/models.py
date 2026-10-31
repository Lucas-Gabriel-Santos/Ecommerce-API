from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from accounts.models import Cliente
from catalog.models import Variacao

# UC07, UC08 e UC09: Pedido, ItemPedido, MetodoPagamento

class TipoPagamento(models.TextChoices):
    PIX = 'PIX', 'Pix'
    CREDITO = 'CREDITO', 'Cartão de Crédito'
    DEBITO = 'DEBITO', 'Cartão de Débito'

class StatusPedido(models.TextChoices):
    PENDENTE = "PENDENTE", "Pendente"
    CONFIRMADO = "CONFIRMADO", "Confirmado"
    ENVIADO = "ENVIADO", "Enviado"
    ENTREGUE = "ENTREGUE", "Entregue"
    CANCELADO = "CANCELADO", "Cancelado"

validar_cep = RegexValidator(r"^\d{8}$", "O CEP deve ter 8 dígitos.")
validar_uf = RegexValidator(r"^[A-Z]{2}$", "Use a sigla da UF em maiúsculas.") #DOCUMENTAR NO SWAGGER QUE SOMENTE PODE LETRAS MAIUSCULAS
validar_ultimos4 = RegexValidator(r"^\d{4}$", "Informe os 4 últimos dígitos.")

class Pedido(models.Model):
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.PROTECT, 
        related_name='pedidos'
    )
    status = models.CharField(max_length= 15, choices= StatusPedido.choices, default= StatusPedido.PENDENTE, db_index=True)
    criado_em = models.DateTimeField(auto_now_add= True)

    cep = models.CharField(max_length= 8, validators=[validar_cep])
    rua = models.CharField(max_length= 300)
    numero = models.CharField(max_length= 10)
    bairro = models.CharField(max_length= 100)
    cidade = models.CharField(max_length= 100)
    uf = models.CharField(max_length= 2, validators=[validar_uf])

    tipo_pagamento = models.CharField(max_length= 20, choices=TipoPagamento.choices)
    ultimos4_pagamento = models.CharField(max_length= 4, blank= True, validators=[validar_ultimos4])

    class Meta:
        ordering = ["criado_em", "id"]

    @property
    def total(self):
        return sum(item.quantidade * item.preco_unitario for item in self.itens.all())

    def __str__(self):
        return f'Pedido #{self.id} - {self.cliente.nome} ({self.status})'
    
class ItemPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido, 
        on_delete= models.CASCADE, 
        related_name= 'itens'
    )
    variacao = models.ForeignKey(
        Variacao, 
        on_delete= models.PROTECT, 
        related_name= 'itens_pedido'
    )
    quantidade = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    preco_unitario = models.DecimalField(max_digits= 10, decimal_places= 2)

    class Meta:
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(fields=["pedido", "variacao"], name="variacao_unica_por_pedido"),
            models.CheckConstraint(condition=models.Q(quantidade__gte=1), name="item_pedido_quantidade_minima"),
            models.CheckConstraint(condition=models.Q(preco_unitario__gt=0), name="item_pedido_preco_positivo",),
        ]

    def __str__(self):
        return f'{self.quantidade}x {self.variacao.produto.nome} (Pedido #{self.pedido_id})'

class MetodoPagamento(models.Model):
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.CASCADE, 
        related_name='metodos_pagamento'
    )
    tipo = models.CharField(max_length= 20, choices= TipoPagamento.choices)
    apelido = models.CharField(max_length= 30, blank = True)
    ultimos4 = models.CharField(max_length= 4, blank = True, validators=[validar_ultimos4])

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.tipo} - {self.apelido or 'sem apelido'}"
