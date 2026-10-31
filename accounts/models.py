from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
import uuid
from django.utils import timezone
from datetime import timedelta

class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("O email é obrigatório.")
        user = self.model(email= self.normalize_email(email).lower(), **extra)
        user.set_password(password)
        user.save(using= self._db)
        return user

    def create_user(self, email, password= None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password= None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra)

class Usuario(AbstractUser): #AbstractUser já vem com o campo Senha
    class Papel(models.TextChoices):
        CLIENTE = 'cliente', 'Cliente'
        LOJISTA = 'lojista', 'Lojista'

    username = None
    email = models.EmailField(unique = True)
    papel = models.CharField(max_length= 10, choices= Papel.choices, default= Papel.CLIENTE)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UsuarioManager()

    def __str__(self):
        return f'{self.email} - ({self.papel})'

class Cliente(models.Model):
    usuario = models.OneToOneField(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='cliente'
    )
    nome = models.CharField(max_length= 100)
    data_nascimento = models.DateField()
    telefone = models.CharField(max_length= 11, validators=[RegexValidator(r"^\d{10,11}$", "Informe só dígitos (DDD + número)")])
    cpf = models.CharField(max_length= 11,  unique=True, validators=[RegexValidator(r"^\d{11}$", "O CPF deve ter 11 dígitos")])
    cep = models.CharField(max_length= 8, validators=[RegexValidator(r"^\d{8}$", "O CEP deve ter 8 dígitos.")])
    endereco = models.CharField(max_length= 300)

    def __str__(self):
        return self.nome

class TokenRecuperacaoSenha(models.Model):
    usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='token_recuperacao'
    )
    token = models.UUIDField(default = uuid.uuid4, unique = True, editable =  False)
    expira_em = models.DateTimeField()
    usado = models.BooleanField(default = False)

    # Se o token for novo, ele define a expiração para daqui 5 minutos
    def save(self, *args, **kwargs):
        if not self.pk and not self.expira_em:
            self.expira_em = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Token para {self.usuario.email} - (Usado: {self.usado})'