from decouple import config
from django.core.management.base import BaseCommand, CommandError
from rest_framework.exceptions import ValidationError
from accounts.models import Usuario
from accounts.validators import validar_forca_senha

class Command(BaseCommand):
    help = "Criar o lojista inicial da loja"

    def handle(self, *args, **options):
        email = config("LOJISTA_EMAIL", default="lojistaLoja@email.com").strip().lower()
        senha = config("LOJISTA_SENHA", default="Lojista@123")

        try:
            validar_forca_senha(senha)
        except ValidationError as erro:
            raise CommandError(f"Senha fraca: {erro.detail[0]}")

        if Usuario.objects.filter(email__iexact =  email).exists():
            self.stdout.write(self.style.WARNING(f"O usuário {email} já existe"))
            return

        Usuario.objects.create_user(email= email, password= senha, papel= Usuario.Papel.LOJISTA)
        self.stdout.write(self.style.SUCCESS(f"Lojista criado!"))