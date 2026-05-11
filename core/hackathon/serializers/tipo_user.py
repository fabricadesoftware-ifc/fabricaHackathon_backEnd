from rest_framework import serializers
from ..models import TipoUser

class TipoUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoUser
        fields = ['id', 'nome']