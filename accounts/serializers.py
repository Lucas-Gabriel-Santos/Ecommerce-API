from rest_framework import serializers
from django.db import transaction
from .validators import validar_forca_senha
from accounts.models import Usuario, Cliente
from cart.models import Carrinho

# Dados pessoais do cliente
class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        exclude = ['usuario']

# Mostra os dados públicos do usuário e as informações do cliente
class UsuarioSerializer(serializers.ModelSerializer):
    cliente = ClienteSerializer(read_only= True)
    class Meta:
        model = Usuario
        fields = ['id', 'email', 'papel', 'cliente']
        read_only_fields = ['id', 'papel']

# Responsável pelo cadastro de cliente
class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only= True, validators=[validar_forca_senha])
    cliente = ClienteSerializer()
    class Meta:
        model = Usuario
        fields = ['id', 'email', 'password','papel', 'cliente']
        read_only_fields = ["id", "papel"]

    # Verifica se o email já está cadastrado para impedir duplicatas
    def validate_email(self, value):
        if Usuario.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Este Email já está cadastrado")
        return value.lower()

    # Cria o usuário, seu perfil de cliente e o carrinho
    @transaction.atomic
    def create(self, validated_data):
        cliente_data = validated_data.pop('cliente')
        password = validated_data.pop('password')
        usuario = Usuario.objects.create_user(password=password, **validated_data)
        cliente = Cliente.objects.create(usuario= usuario, **cliente_data)
        Carrinho.objects.create(cliente = cliente)
        return usuario

# Responsável pela redefinição de senha
class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(write_only= True, validators=[validar_forca_senha])

# Valida o email informado na recuperação de senha
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()