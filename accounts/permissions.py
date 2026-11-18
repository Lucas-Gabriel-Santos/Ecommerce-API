from rest_framework.permissions import BasePermission
from accounts.models import Usuario

# Verifica se o usuário está autenticado como lojista
def ehLojista(user):
    return bool(user and user.is_authenticated and user.papel == Usuario.Papel.LOJISTA)

# Classe de permissões personalizadas para apenas o lojista fazer
class EhLojista(BasePermission):
    message = 'Apenas o Lojista pode realizar esta ação'

    def has_permission(self, request, view):
        return ehLojista(request.user)

# Classe de permissões personalizadas que permite acesso somente a cliente autenticado
class EhCliente(BasePermission):
    message = 'Apenas o Cliente pode realizar esta ação'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.papel == Usuario.Papel.CLIENTE)
    