from rest_framework import serializers
from cart.models import Carrinho, ItemCarrinho
from catalog.models import Variacao
from decimal import Decimal
from django.db import transaction

class ItemCarrinhoSerializer(serializers.ModelSerializer):
    produto = serializers.CharField(source="variacao.produto.nome", read_only=True)
    id_variacao = serializers.IntegerField(source="variacao.id", read_only=True)
    tamanho = serializers.CharField(source="variacao.tamanho", read_only=True)
    cor = serializers.CharField(source="variacao.cor", read_only=True)
    preco_unitario = serializers.DecimalField(source="variacao.produto.preco", max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = ItemCarrinho
        fields = [
            "id", "produto", "id_variacao", "tamanho", "cor",
            "preco_unitario", "quantidade", "subtotal",
        ]
    
    def get_subtotal(self, obj):
        return (obj.quantidade * obj.variacao.produto.preco).quantize(Decimal("0.01"))

class CarrinhoSerializer(serializers.ModelSerializer):
    itens = ItemCarrinhoSerializer(many= True, read_only= True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Carrinho
        fields = ['id', 'itens', 'total']

    def get_total(self, obj):
        total = sum(
            (i.quantidade * i.variacao.produto.preco for i in obj.itens.all()),
            Decimal("0"),
        )
        return total.quantize(Decimal("0.01"))

# POST/cart/items
class AdicionarItemSerializer(serializers.Serializer):
    id_variacao = serializers.PrimaryKeyRelatedField(
        queryset=Variacao.objects.select_related("produto"), source="variacao"
    )
    quantidade = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        variacao = attrs['variacao']
        carrinho = self.context["carrinho"]

        if not variacao.produto.ativo:
            raise serializers.ValidationError("Não é possível adicionar um produto inativo")

        existente = ItemCarrinho.objects.filter(carrinho= carrinho, variacao= variacao).first()
        no_carrinho = existente.quantidade if existente else 0

        if no_carrinho + attrs['quantidade'] > variacao.quantidade:
            raise serializers.ValidationError(
                f'O estoque é insuficiente. Disponível: {variacao.quantidade}; '
                f'Já está no carrinho: {no_carrinho}'
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        carrinho = self.context['carrinho']
        item, criado = ItemCarrinho.objects.get_or_create(
            carrinho=carrinho,
            variacao=validated_data["variacao"],
            defaults={"quantidade": validated_data["quantidade"]},
        )

        if not criado:
            item.quantidade += validated_data['quantidade']
            item.save(update_fields=['quantidade'])

        return item

    def to_representation(self, instance):
        return ItemCarrinhoSerializer(instance, context=self.context).data

# PUT/cart/items
class AtualizarItemSerializer(serializers.Serializer):
    quantidade = serializers.IntegerField(min_value= 1)

    class Meta:
        model = ItemCarrinho
        fields = ['quantidade']

    def validate_quantidade(self, value):
        variacao = self.instance.variacao

        if value > self.instance.quantidade and not variacao.produto.ativo:
            raise serializers.ValidationError("Este produto está inativo.")
        if value > variacao.quantidade:
            raise serializers.ValidationError(
                f"Estoque insuficiente. Disponível: {variacao.quantidade}."
            )
        return value

    def to_representation(self, instance):
        return ItemCarrinhoSerializer(instance, context=self.context).data