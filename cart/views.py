from django.shortcuts import render

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import generics, mixins, viewsets

from accounts.permissions import EhCliente
from cart.models import Carrinho, ItemCarrinho
from cart.serializers import  CarrinhoSerializer, AdicionarItemSerializer, AtualizarItemSerializer

@extend_schema(
    tags=['Carrinho'],
    summary= 'ver todos os itens que existem no meu carrinho',
    description= (
        """
        Somente para clientes autenticados. Devolve os itens do carrinho
        para o usuário logado, com o preço, subtotal e total.
        """
    ),
)
class CarrinhoView(generics.RetrieveAPIView):
    queryset = Carrinho.objects.none()
    serializer_class = CarrinhoSerializer
    permission_class = [EhCliente]

    # O cliente só vai poder ver o proprio carrinho
    def get_object(self):
        return get_object_or_404(
            Carrinho.objects.prefetch_related('itens__variacao__produto'),
            cliente__usuario = self.request.user
        )

@extend_schema_view(
    create = extend_schema(
        tags = ['Carrinho'],
        summary = 'Adicionar itens ao carrinho',
        description = (
            """
            Somente para clientes. Coloque a variação e quantidade do item.
            Se variação já estiver no carrinho, ela e somanda com a quantidade. A quantidade mínima é 1,
            o estoque da variação, e produtos inativos não podem ser adicionados.
            """
        ),
        examples = [
            OpenApiExample('Adicionar item', request_only = True, value={'variacao_id': 3, 'quantidade': 2},)
        ],
    ),
    update = extend_schema(
        tags = ['Carrinho'],
        summary = 'Atualizar a quantidade de itens no carrinho',
        description = (
            """
            Somente para clientes. O valor enviado substitui a quantidade atual de um item.
            Mínimo é 1 e o máximo é o estoque existente de variações.
            """
        ),
        examples=[
            OpenApiExample("Nova quantidade", request_only=True, value={"quantidade": 3})
        ],
    ),
    destroy = extend_schema(
        tags = ['Carrinho'],
        summary = 'Excluir itens do carrinho',
        description = 'Somente para clientes. Exclui itens do próprio carrinho.'
    ),
)
class ItemCarrinhoViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet,):
    permission_classes = [EhCliente]

    # Definindo métodos HTTP permitidos
    http_method_names = ["post", "put", "delete","head", "options"]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False): 
            return ItemCarrinho.objects.none()
        return ItemCarrinho.objects.filter( carrinho__cliente__usuario = self.request.user).select_related("variacao__produto")

    def get_serializer_class(self):
        if self.action == 'create':
            return AdicionarItemSerializer
        return AtualizarItemSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()

        if self.action == 'create' and not getattr(self, 'swagger_fake_view', False):
            context['carrinho'] = get_object_or_404(Carrinho, cliente__usuario=self.request.user)
        return context