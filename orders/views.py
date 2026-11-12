from django.shortcuts import render

from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import EhCliente, EhLojista, ehLojista
from orders.models import MetodoPagamento, Pedido, StatusPedido
from orders.serializers import MetodoPagamentoSerializer, PedidoCriarSerializer, PedidoSerializer, PedidoStatusSerializer

STATUS_ATIVOS = [StatusPedido.PENDENTE, StatusPedido.CONFIRMADO, StatusPedido.ENVIADO]

@extend_schema_view(
    list=extend_schema(
        tags=['Pedidos'],
        summary='Listar pedidos',
        description=(
            """
            Paginado. O cliente vê somente os próprios pedidos. O lojista vê todos. sem filtro e só os ativos (PENDENTE, CONFIRMADO e ENVIADO).
            Usando `status` dá para ver todos, como ENTREGUE e CANCELADO.
            """
        ),
        parameters=[
            OpenApiParameter(
                'status', str, enum=[s.value for s in StatusPedido],
                description='Filtro por status - somente lojista',
            )
        ],
    ),
    retrieve=extend_schema(
        tags=['Pedidos'],
        summary='Detalhar pedido',
        description=(
            """
            O cliente acessa somente os próprios pedidos, se tentar acessar de outro retorna 404.
            O lojista acessa de todos.
            """
        ),
    ),
    create=extend_schema(
        tags=['Pedidos'],
        summary='Finalizar compra - checkout do carrinho inteiro',
        description=(
            """
            Somente o Cliente. Informe o endereço de entrega e o `payment_method_id`, que deve
            ser somente do cliente logado. O estoque de todos os itens é revalidado e baixado 
            em uma transação: se algum item não tiver no estoque, nenhum pedido é criado e a resposta será 404.
            O pedido nasce PENDENTE, guarda o preço unitário do momento da compra, copia o endereço e o pagamento, e o carrinho é esvaziado.
            """
        ),
        examples=[
            OpenApiExample(
                "Checkout",
                request_only=True,
                value={
                    'payment_method_id': 1,
                    'cep': "59114071",
                    'rua': "Rua do limoeiro",
                    'numero': "80",
                    'bairro': "Centro",
                    'cidade': "Natal",
                    'uf': "RN",
                },
            )
        ],
    ),
)
class PedidoViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):

    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_permissions(self):
        if self.action == "create":
            return [EhCliente()]
        if self.action == "alterar_status":
            return [EhLojista()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Pedido.objects.none()

        queryset = Pedido.objects.select_related('cliente').prefetch_related('itens__variacao__produto')

        # O cliente vai ver somente os próprios pedidos
        if not ehLojista(self.request.user):
            return queryset.filtes(cliente__usuario = self.request.user)

        if self.action == "list":
            status_pedido = self.request.query_params.get('status')

            if status_pedido:
                if status_pedido not in StatusPedido.values:
                    raise ValidationError({"status": f"Use um destes seguintes valores: {', '.join(StatusPedido.values)}."})

                return queryset.filter(status = status_pedido)
            return queryset.filter(status__in = STATUS_ATIVOS)
        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return PedidoCriarSerializer
        elif self.action == "alterar_status":
            return PedidoStatusSerializer
        return PedidoSerializer

    def status_alterar(self, request, pk = None):
        pedido = self.get_object()
        serializer = self.get_serializer(pedido, data = request.data)
        serializer.is_valid(raise_exception = True)
        serializer.save()

        return Response(serializer.data)

@extend_schema_view(
    create = extend_schema(
        tags = ['Métodos de Pagamento'],
        summary = 'Cadastrar métodos de pagamento',
        description = (
            """
            Somente o Cliente. Tipos de método: PIX, CREDITO E DEBIDO. Se formcartão o cliente informa os 4 últimos
            digitos. O número completo do cartão e o CVV nunca são aceitas.
            """
        ),
        exemples = [
            OpenApiExample(
                'Cartão de crédito', request_only=True,
                value={"tipo": "CREDITO", "apelido": "Cartão principal", "ultimos4": "9696"},
            ),
            OpenApiExample("Pix", request_only=True, value={"tipo": "PIX", "apelido": "Chave CPF"}),
        ],
    ),
    list = extend_schema(
        tags = ['Métodos de Pagamento'],
        summary = 'Listar os métodos de pagamento',
        description = (
            """
            Somente o Cliente. Paginado, apenas os clientes logados podem ver os métodos.
            """
        ),
    ),
    destroy = extend_schema(
        tags = ['Métodos de Pagamento'],
        summary = 'Remover os métodos de pagamento',
        description = (
            """
            Somente o Cliente, e apenas os próprios métodos. Pedidos já feitos não são afetados, 
            porque guardam uma cópia dos dados.
            """
        ),
    ),
)
class MetodoPagamentoViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = MetodoPagamentoSerializer
    permission_class = [EhCliente]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return MetodoPagamento.objects.none()
        return MetodoPagamento.objects.filter(cliente__usuario = self.request.user)

    def perform_create(self, serializer):
        serializer.save(cliente = self.request.user.cliente)