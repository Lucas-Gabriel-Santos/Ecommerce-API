from rest_framework import serializers
from catalog.models import Categoria, Produto, Variacao

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nome']

class VariacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variacao
        fields = ['id', 'tamanho', 'cor', 'quantidade']

    def validate(self, attrs):
        produto = self.context['produto']
        tamanho = attrs.get('tamanho', getattr(self.instance, 'tamanho', None))
        cor = attrs.get('cor', getattr(self.instance, "cor", None))

        variacao_duplicada = Variacao.objects.filter(produto=produto, tamanho__iexact=tamanho, cor__iexact=cor)

        if self.instance:
            variacao_duplicada = variacao_duplicada.exclude(pk=self.instance.pk)
        if variacao_duplicada.exists():
            raise serializers.ValidationError("Esta variação já existe para o produto")
        return attrs

class VariacaoEstoqueSerializer(serializers.ModelSerializer):
    class Meta:
        mmodel = Variacao
        fields = ["id", "tamanho", "cor", "quantidade"]
        read_only_fields = ["id", "tamanho", "cor"]
    

class ProdutoListSerializer(serializers.ModelSerializer):
    categoria = serializers.CharField(source="categoria.nome", read_only=True)

    class Meta:
        model = Produto
        fields = ['id', 'nome', 'preco', 'ativo', 'categoria']

class ProdutoDetalheSerializer(serializers.ModelSerializer):
    # No GET, mostra todos os dados de categoria e variações associadas ao protudo
    categoria = CategoriaSerializer(read_only= True)
    variacoes = VariacaoSerializer(many= True, read_only= True )

    class Meta:
        model = Produto
        fields = ['id', 'nome','descricao', 'preco', 'ativo', 'categoria', 'categoria_id', 'variacoes']

class ProdutoEscritaSerializer(serializers.ModelSerializer):
    categoria_id = serializers.PrimaryKeyRelatedField(queryset=Categoria.objects.all(), source='categoria')

    class Meta:
        model = Produto
        fields = ['id', 'nome', 'descricao', 'preco', 'ativo', 'categoria_id']
        read_only_fields = ['id']

    def validate_nome(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("O nome não pode ficar vazio")
        return value

    def validate_preco(self, value):
        if value <= 0:
            raise serializers.ValidationError("O preço deve ser maior que zero")
        return value

    def to_representation(self, instance):
        
        # Depois de criar ou editar, devolve o formato completo do detalhe.
        return ProdutoDetalheSerializer(instance, context=self.context).data
