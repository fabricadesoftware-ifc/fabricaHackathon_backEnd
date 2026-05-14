from rest_framework import serializers
from ..models import Edicao

class EdicaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edicao
        fields = "__all__"
        
    def validate(self, data):
        if data['data_fim'] <= data['data_inicio']:
            raise serializers.ValidationError({"data_inicio": "A data de início deve ser anterior à data de fim."})
        if data['minimo_participantes'] > data['maximo_participantes']:
            raise serializers.ValidationError({"minimo_participantes": "O número mínimo de participantes deve ser menor ou igual ao número máximo de participantes."})
        if data['maximo_equipes'] <= 0:
            raise serializers.ValidationError({"maximo_equipes": "O número máximo de equipes deve ser maior que zero."})
        return data
    
class EdicaoListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edicao
        fields = ["id", "nome", "ano", "status", "data_inicio", "data_fim"]
        