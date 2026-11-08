from rest_framework import serializers
from orders.models import ItemPedido, MetodoPagamento, Pedido, StatusPedido, TipoPagamento
from orders.services import criar_pedido, alterar_status

class ItemPedidoSerializer(serializers.ModelSerializer):
    produto = serializers.CharField(source='variacao.produto.nome', read_only= True)
    id_variacao = serializers.IntegerField(read_only= True)
    tamanho = serializers.CharField(source= 'variacao.tamanho', read_only= True)
    cor = serializers.CharField(source= 'variacao.cor', read_only= True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = ItemPedido
        fields = ['id', 'produto', 'id_variacao', 'tamanho', 'cor', 'quantidade', 'preco_unitario', 'subtotal',]

    def get_subtotal(self, obj):
        return obj.quantidade * obj.preco_unitario

class PedidoSerializer(serializers.ModelSerializer):
    cliente = serializers.CharField(source= 'cliente.nome', read_only= True)
    itens = ItemPedidoSerializer(many= True, read_only=True)
    total = serializers.DecimalField(max_digits= 10, decimal_places= 2, read_only= True)

    class Meta:
        model = Pedido
        fields = ['id', 'cliente','status', 'criado_em', 'cep', 'rua', 'numero', 'bairro', 'cidade', 'uf', 'tipo_pagamento', 'ultimos4_pagamento', 'itens', 'total' ]

# POST/orders
class PedidoCriarSerializer(serializers.ModelSerializer):
    id_payment_method = serializers.PrimaryKeyRelatedField(
        queryset = MetodoPagamento.objects.none(),
        source = "metodo_pagameto",
        write_only = True
    )

    class Meta:
        model = Pedido
        fields = ['cep', 'rua', 'numero', 'bairro', 'cidade', 'uf', 'id_payment_method']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')

        if request and request.user.is_authenticated and hasattr(request.user, 'cliente'):
            self.fields['id_payment_method'].queryset  = MetodoPagamento.objects.filter(cliente = request.user.cliente)

    def create(self, validated_data):
        metodo = validated_data.pop('metodo_pagamento')
        cliente = self.context['request'].user.cliente

        return criar_pedido(cliente, validated_data, metodo)

    def to_representation(self, instance):
        return PedidoSerializer(instance, context = self.context).data
    
# PATCH/orders/:id/status
class PedidoStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices= StatusPedido.choices)

    def update(self, instance, validated_data):
        return alterar_status(instance, validated_data['status'])

    def to_representation(self, instance):
        return PedidoSerializer(instance, context = self.context).data

# UC09: Métodos de pagaento
class MetodoPagamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetodoPagamento
        fields = '__all__'
        read_only_fields = ['id']

    # UC09: Faz com que não seja permitido adicionar o n° completo do cartão ou o CVV
    def to_internal_value(self, data):
        extras = set(data) - set(self.fields)

        if extras:
            raise serializers.ValidationError(
                'O número completo do cartão e o CVV não são aceitos'
                f'Campos não permitidos: {', '.join(sorted(extras))}'
            )

        return super().to_internal_value(data)

    def validate(self, attrs):
        ultimos4 = attrs.get('ultimos4', '')

        if attrs['tipo'] == TipoPagamento.PIX:
            if ultimos4:
                raise serializers.ValidationError({'Ultimos4': 'PIX não usa os 4 últimos dígitos'})

            elif not ultimos4:
                raise serializers.ValidationError({'Ultimos4': 'Informe os últimos 4 dígitos do seu cartãi'})

            return attrs