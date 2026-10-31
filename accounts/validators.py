import re
from rest_framework import serializers

def validar_forca_senha(value):
    faltas = []
    if len(value) < 8:
        faltas.append("pelo menos 8 caracteres")
    if not re.search(r"[A-Z]", value):
        faltas.append("pelo menos 1 letra maiúscula")
    if not re.search(r"[^\w\s]", value):
        faltas.append("pelo menos 1 caractere especial")
    if faltas:
        raise serializers.ValidationError("A senha deve ter " + ", ".join(faltas) + ".")
    return value