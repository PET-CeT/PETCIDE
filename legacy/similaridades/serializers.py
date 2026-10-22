from rest_framework import serializers
from .models import TextoEvento

class TextoInputSerializer(serializers.Serializer):
    descricao = serializers.CharField(required=True)
    evento = serializers.CharField(required=True)

class SimilaridadeOutputSerializer(serializers.Serializer):
    texto_base = serializers.CharField()
    evento_base = serializers.CharField()
    texto_mais_semelhante = serializers.CharField()
    evento_mais_semelhante = serializers.CharField()
    similaridade = serializers.FloatField()
    
class TextEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextoEvento
        fields = ['id','descricao', 'evento', 'ano']
        extra_kwargs = {
            'id': {'read_only': True},
            'descricao': {'required': True},
            'evento': {'required': True},
            'ano': {'required': True}
        }