from rest_framework.views import exception_handler

def tratar_erros(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return None

    data = response.data

    if isinstance(data, dict) and 'detail' in data:
        corpo = {'message': str(data['detail'])}
        extras = {chave: valor for chave, valor in data.items() if chave != 'detail'}

        if extras:
            corpo['errors'] = extras

        elif isinstance(data, dict) and 'non_field_errors' in data and len(data) == 1:
            erros = data['non_field_errors']
            corpo = {'message': " ".join(str(erro) for erro in erros)}

        elif isinstance(data, dict):
            corpo = {'message': 'Dados Inválidos', 'errors': data}

        elif isinstance(data, list):
            if any(isinstance(item, dict) for item in data):
                corpo = {'message': 'Dados Inválidos na lista', 'errors': data}
            else:
                corpo = {'message': " ".join(str(item) for item in erros)}

        else:
            corpo = {'message': str(data)}