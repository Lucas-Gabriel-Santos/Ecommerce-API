from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from accounts.views import EsqueciSenhaView, LoginView, RedefinirSenhaView, RegistroView
from rest_framework.routers import SimpleRouter
from catalog.views import CategoriaListView, ProdutoViewSet, VariacaoViewSet
from cart.views import CarrinhoView, ItemCarrinhoViewSet

router = SimpleRouter(trailing_slash=False)  # sem barra final, como no documento
router.register("products", ProdutoViewSet, basename="produto")
router.register("cart/items", ItemCarrinhoViewSet, basename="item-carrinho")

urlpatterns = [
    path('admin/', admin.site.urls),

    # accounts (UC01 e UC02)
    path("auth/register", RegistroView.as_view(), name="auth-register"),
    path("auth/login", LoginView.as_view(), name="auth-login"),
    path("auth/forgot-password", EsqueciSenhaView.as_view(), name="auth-forgot-password"),
    path("auth/reset-password", RedefinirSenhaView.as_view(), name="auth-reset-password"),

    # documentação (Swagger)
    path("schema", SpectacularAPIView.as_view(), name="schema"),
    path("docs", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    # catalog (UC03, UC04 e UC05)
    path("categories", CategoriaListView.as_view(), name="categoria-list"),
    path("products/<int:produto_id>/variations", VariacaoViewSet.as_view({"post": "create"}), name="variacao-criar"),
    path("products/<int:produto_id>/variations/<int:pk>", VariacaoViewSet.as_view({"put": "update"}), name="variacao-atualizar"),
    path("", include(router.urls)),

    # cart (UC06)
    path("cart", CarrinhoView.as_view(), name="carrinho"),
]
