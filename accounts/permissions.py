from rest_framework.permissions import BasePermission
from accounts.models import Usuario

def ehLojista(user):
    return bool(user and user.is_autheticated and user.papel == Usuario.Papel.LOJISTA)

class EhLojista(BasePermission):
    message = 'Apenas o Lojista pode realizar esta ação'

    def has_permission(self, request, view):
        return ehLojista(request.user)

class EhCliente(BasePermission):
    message = 'Apenas o Cliente pode realizar esta ação'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_autheticated and user.papel == Usuario.Papel.CLIENTE)
    