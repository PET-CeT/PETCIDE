from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

class TextoInputSerializer(serializers.Serializer):
    descricao = serializers.CharField()
    evento = serializers.CharField()
    ano = serializers.IntegerField()

class SimilaridadeOutputSerializer(serializers.Serializer):
    texto_base = serializers.CharField()
    evento_base = serializers.CharField()
    texto_mais_semelhante = serializers.CharField()
    evento_mais_semelhante = serializers.CharField()
    similaridade = serializers.FloatField()
    
class TextEventSerializer(serializers.Serializer):
    texto = serializers.CharField()
    evento = serializers.CharField()
    ano = serializers.IntegerField()