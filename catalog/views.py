from django.shortcuts import render

import django_filters
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import generics, mixins, viewsets
from rest_framework.permissions import AllowAny

from accounts.permissions import EhLojista, ehLojista
from catalog.models import Categoria, Produto, Variacao
from catalog.serializers import CategoriaSerializer, ProdutoDetalheSerializer, ProdutoEscritaSerializer, ProdutoListSerializer, VariacaoEstoqueSerializer, VariacaoSerializer

EXEMPLO_PRODUTO = {
    "nome": "Camisa preta ",
    "descricao": "Camisa preta de algodão com estampa frontal da banda kiss",
    "preco": "89.99",
    "ativo": True,
    "categoria_id": 1,
}

class ProdutoFilter(django_filters.FilterSet):
    categoria = django_filters.NumberFilter(field_name="categoria_id")
    preco_max = django_filters.NumberFilter(field_name="preco", lookup_expr="lte")
    preco_min = django_filters.NumberFilter(field_name="preco", lookup_expr="gte")
    pesquisa = django_filters.CharFilter(field_name="nome", lookup_expr="icontains")
    status = django_filters.ChoiceFilter( 
        choices=[('ativo', 'ativo'), ('inativo', 'inativo')], method="filtrar_status",
    )

    class Meta:
        model = Produto
        fields = []

    def filtrar_status(self, queryset, name, value):
        if not ehLojista(self.request.user):
            return queryset
        return queryset.filter(ativo = (value == 'ativo'))

@extend_schema(
    tags=['Categorias'],
    summary='Lista de categorias',
    description='Categorias fixas da loja, criadas por seed. Acesso público e paginado',
)
class CategoriaListView(generics.ListAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

@extend_schema_view(
    list=extend_schema(
        tags=['Produtos'],
        summary='Listar e buscar produtos',
        description=(
            """
            Os produtos podem ser acessados por todos e é paginado. Os filtros combináveis: `category` (id), `min_price`, 
            `max_price`, `search`. Os Visitantes e Clientes podem somente ver os produtos que estão ativos. O lojista autenticado vê todos os 
            produtos, até os inativos e pode usar `status` (active ou inactive)
            """
        ),
    ),
    retrieve=extend_schema(
        tags=['Produtos'],
        summary='Detalhes do produto',
        description=(
            """
            Os produtos podem ser acessados por todos (Acesso público). Devolve o produto com categoria e variações.
            Os produtos inativos retorna 404 para os Clientes e Visitantes.
            """
        ),
    ),
    create=extend_schema(
        tags=['Produtos'],
        summary='Criar produto - lojista',
        description=(
            """
            Somente o lojista. Os preços devems er maiores que zero e a categoria deve existir. 
            O estoque de produtos é conrolado nas variações
            """
        ),
        examples=[OpenApiExample('Novo produto', request_only=True, value=EXEMPLO_PRODUTO)],
    ),
    update=extend_schema(
        tags=['Produtos'],
        summary='Editar, ativar ou desativar produto - lojista',
        description=(
            """
            Somente o lojista. Os produtos não são excluídos. Eles são ativados e desativados.
            Para tirar um produto de venda: `ativo: false`
            """
        ),
        examples=[
            OpenApiExample(
                'Desativar produto', request_only=True, value={**EXEMPLO_PRODUTO, 'ativo': False}
            )
        ],
    ),
)
class ProdutoViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, 
    mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    filterset_class = ProdutoFilter

    # Definindo métodos HTTP permitidos
    http_method_names = ["get", "post", "put", "head", "options"]

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [EhLojista()]

    def get_queryset(self):
        queryset = Produto.objects.select_related('categoria')
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('variacoes')
        if not ehLojista(self.request.user):
            queryset = queryset.filter(ativo = True)

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return ProdutoListSerializer
        if self.action == 'retrieve':
            return ProdutoDetalheSerializer
        
        return ProdutoEscritaSerializer

@extend_schema_view(
    create=extend_schema(
        tags=['Variações'],
        summary='Criar variação de um produto - lojista',
        description=(
            """
            Somente o lojista. Cada combinação de tamanho e cor é única dentro de um produto.
            Para produtos de tamanho único, basta usar tamanho `Único`
            """
        ),
        examples=[
            OpenApiExample(
                'Nova variação',
                request_only=True,
                value={'tamanho': "M", "cor": "Azul", "quantidade": 10},
            )
        ],
    ),
    update=extend_schema(
        tags=['Variações'],
        summary='Atualizar o estoque de uma variação - lojista',
        description=(
            """
            Somente o lojista. Atualiza apenas a quantidade em estoque.
            Variações não são excluídas, zere o estoque para tirar de venda.
            """
        ),
        examples=[OpenApiExample('Novo estoque', request_only=True, value={'quantidade': 25})],
    ),
)
class VariacaoViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    permission_classes = [EhLojista]

    # Definindo métodos HTTP permitidos
    http_method_names = ["post", "put", "head", "options"]

    def get_produto(self):
        if not hasattr(self, '_produto'):
            self._produto = get_object_or_404(Produto, pk=self.kwargs["produto_id"])
        return self._produto

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Variacao.objects.none()

        return Variacao.objects.filter(produto_id=self.kwargs['produto_id'])

    def get_serializer_class(self):
        if self.action == 'update':
            return VariacaoEstoqueSerializer
        
        return VariacaoSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action == 'create' and not getattr(self, 'swagger_fake_view', False):
            context['produto'] = self.get_produto()

        return context

    def perform_create(self, serializer):
        serializer.save(produto = self.get_produto())