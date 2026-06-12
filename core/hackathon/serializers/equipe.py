from rest_framework.serializers import ModelSerializer

from ..models import Equipe

class EquipeSerializer(ModelSerializer):
    class Meta: 
        model = Equipe
        fields = ['id', 'nome_equipe', 'tema', 'projeto']

class EquipeListSerializer(ModelSerializer):
    class Meta: 
        model = Equipe
        fields = ['id', 'nome_equipe']