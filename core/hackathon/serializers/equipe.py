from rest_framework.serializers import ModelSerializer

from ..models import Equipe

class EquipeSerializer(ModelSerializer):
    class Meta: 
        model = Equipe
        fields = ['id', 'nome_equipe', 'edicao', 'tema', 'projeto']

class EquipeListSerializer(ModelSerializer):
    class Meta: 
        model = Equipe
        fields = ['id', 'nome_equipe']