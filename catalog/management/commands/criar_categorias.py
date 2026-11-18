from django.core.management.base import BaseCommand
from catalog.models import Categoria

# Lista de categorias utilizadas no catalogo da loja
CATEGORIAS = [
    'Calças',
    'Bermudas',
    'Blusas',
    'Regatas',
    'Vestidos',
    'Shorts',
    'Saias',
]

class Command(BaseCommand):
    help = "Criar as categorias da loja"

    def handle(self, *args, **options):
        criadas = 0

        for nome in CATEGORIAS:
            _, criada = Categoria.objects.get_or_create(nome = nome)
            criadas = criadas + int(criada)

            self.stdout.write(self.style.SUCCESS(f"{criadas} categorias criadas."))