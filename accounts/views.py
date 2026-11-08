from django.shortcuts import render

import logging
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema

from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.models import TokenRecuperacaoSenha, Usuario
from accounts.serializers import ForgotPasswordSerializer, RegistroSerializer, ResetPasswordSerializer

logger = logging.getLogger(__name__)

MENSAGEM_FORGOT = "Enviaremos as instruções de recuperação se o seu email já estiver cadastrado no sistema"

@extend_schema(
    tags=['Autenticação'],
    summary='Cadastro dos clientes',
    description=(
        """
        Cria um usuário com o papel sendo Cliente.
        O campo papel, se enviado, é ignorado.
        """
    ),
    examples=[
        OpenApiExample(
            'Cadastro',
            request_only=True,
            value={
                "email": "gabriel@email.com",
                "password": "lucas@123",
                "cliente": {
                    "nome": "Lucas Gabriel",
                    "data_nascimento": "2000-07-17",
                    "telefone": "84998576734",
                    "cpf": "12345678901",
                    "cep": "59114071",
                    "endereco": "Rua do Limoeiro, 80, Natal - RN"
                },
            },
        )
    ],
)
class RegistroView(generics.CreateAPIView):
    serializer_class = RegistroSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

@extend_schema(
    tags=['Autenticação'],
    summary='Login - Cliente ou Lojista',
    description='Autentica por email e senha e devolve o JWT (`access`) e o `refresh`',
    examples=[
        OpenApiExample(
            'Login',
            request_only=True,
            value={"email": "gabriel@email.com", "password": "lucas@123"},
        )
    ],
)
class LoginView(TokenObtainPairView):
    permission_class = [AllowAny]
    authentication_classes = []

@extend_schema(
    tags=['Autenticação'],
    summary='Solicitar recuperação de senha',
    description=(
        'Envia um link com token temporário se o email estiver cadastrado'
    ),
    request=ForgotPasswordSerializer,
    responses={200: OpenApiResponse(description=MENSAGEM_FORGOT)},
    examples=[OpenApiExample('Solicitação', request_only=True, value={"email": "gabriel@email.com"})],
)
class EsqueciSenhaView(APIView):
    permission_class = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = ForgotPasswordSerializer(data = request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        usuario = Usuario.objects.filter(email__iexact=email, is_active=True).first()

        if usuario is not None:

            with transaction.atomic():
                TokenRecuperacaoSenha.objects.filter(usuario = usuario, usado = False).update(usado = True)
                registro = TokenRecuperacaoSenha.objects.create(
                    usuario =  usuario,
                    expira_em = timezone.now() + timedelta(minutes=settings.PASSWORD_RESET_TIMEOUT_MINUTES)
                )

            link = f"{settings.PASSWORD_RESET_URL}?token={registro.token}"
            try:
                send_mail(
                    subject='Recuperação de senha',
                    message=(
                        'Recebemos o seu pedido para redefinir senha.\n\n'
                        f"Token: {registro.token}\n"
                        f"Link: {link}\n\n"
                        f"Ele vale por {settings.PASSWORD_RESET_TIMEOUT_MINUTES} minutos "
                        "e só pode ser usado uma vez.\n"
                        "Se não foi você, ignore este email."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[usuario.email],
                )
            except Exception:
                logger.exception('Falha ao enviar email de recuperação')

        return Response({"detail": MENSAGEM_FORGOT}, status=status.HTTP_200_OK)

@extend_schema(
    tags=['Autenticação'],
    summary='Redefinir a senha',
    description=(
        """
        Redefine a senha com o token recebido por email. O token expira e só pode 
        ser usado uma vez. A nova senha exige 8 caracteres, 1 maiúscula e 1 caractere especial
        """
    ),
    request=ResetPasswordSerializer,
    responses={200: OpenApiResponse(description='Senha redefinida com sucesso')},
    examples=[
        OpenApiExample(
            'Redefinição',
            request_only=True,
            value={
                "token": "3f2b8c1e-5a7d-4c2e-9b1a-6d8e0f4a7c21",
                "new_password": "NovaSenha@123",
            },
        )
    ],
)
class RedefinirSenhaView(APIView):
    permission_class = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = ResetPasswordSerializer(data = request.data)
        serializer.is_valid(raise_exception = True)
        token = serializer.validated_data['token']
        senha_nova = serializer.validated_data['new_password']

        with transaction.atomic():
            registro = (
                TokenRecuperacaoSenha.objects.select_for_update()
                .select_for_update('usuario')
                .filter(token = token, usado = False, expira_em__gt = timezone.now())
                .first()
            )

            if registro is None:
                raise ValidationError('Token inválido ou já expirado')

            usuario = registro.usuario
            usuario.set_password(senha_nova)
            usuario.save(update_fields=['password'])

            TokenRecuperacaoSenha.objects.filter(usuario=usuario, usado=False).update(usado=True)

        return Response({"detail": 'Senha redefinida com sucesso'}, status=status.HTTP_200_OK)

